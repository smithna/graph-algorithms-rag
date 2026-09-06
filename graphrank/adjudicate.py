"""LLM adjudication of candidate pairs — opt-in, capped, cached, read-only.

The algorithm's job in entity resolution is not to decide. It is to shrink the
candidate set from O(n²) to something a slower, better judge can afford to look
at. On this corpus that is the difference between 6.2 million Person pairs and
about three hundred — four orders of magnitude, which is what turns "ask a model
about every pair" from absurd into a few cents.

This module is the slower, better judge. It is **off by default** everywhere,
for three reasons that all matter for a conference demo:

1. It costs money. Nothing in this repo should quietly spend the presenter's
   API budget because a script was run with default flags.
2. It costs time. Adjudicating a few hundred pairs serially takes long enough
   to kill a live demo.
3. It is non-deterministic in a way the rest of the pipeline is not. Every
   other number in this talk is reproducible; this one is reproducible only
   because of the cache below.

Three safety rails, in the order they fire:

``enabled``    adjudication does nothing unless explicitly switched on
``max_calls``  a hard cap checked before every request, not a target
``cache``      every verdict is written to disk keyed by (model, label, pair),
               so re-running a demo costs nothing and returns identical output

Like the rest of section 4, this writes nothing to the database. It returns
verdicts as values; what the caller does with them is the caller's business, and
in this repo the only thing anyone does with them is print them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import settings
from .resolution import CandidatePair

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "adjudication"

#: Deliberately small and cheap. The judge is doing a narrow, well-specified
#: binary task with a rubric, not open-ended reasoning.
DEFAULT_MODEL = "gpt-4o-mini"

#: A cap, not a budget to spend. Chosen so a full Person run over this corpus
#: stays well under a dollar and finishes inside a coffee break.
DEFAULT_MAX_CALLS = 50

SPECIES_LABELS = frozenset({"PlantSpecies", "AnimalSpecies"})

RESOLUTION_PROMPT = """
You are an expert on the Lewis and Clark Expedition (1804-1806).

You will be given two entity names of the same type extracted from the expedition
journals. Determine whether they refer to the same real-world entity.

Be conservative. These names were extracted from journals whose spelling is
wildly inconsistent, so surface similarity is weak evidence — but so is
dissimilarity, because the same person is written many ways. Weigh what you know
about the expedition's roster over what the strings look like.

Specific traps in this corpus:
  - Joseph Field and Reubin Field are BROTHERS, not the same man.
  - Toussaint Charbonneau and Jean Baptiste Charbonneau are FATHER and SON.
  - Meriwether Lewis and William Clark are the two captains, not one person.
  - Many privates share a given name (John Shields, John Collins, John Potts).
    A shared first name is not evidence.

If they are the same entity, provide the best canonical name — the most complete,
modern, and widely accepted form. Examples of preferred forms:
  "Meriwether Lewis" not "Capt. Lewis" or "Lewis"
  "William Clark"    not "Capt. Clark" or "Clark"
  "Arikara"          not "Ricaras" or "Rickarees"
  "Hidatsa"          not "Minnetarees" or "Gros Ventres"
  "Shoshone"         not "Snake Indians"
  "Nez Perce"        not "Chopunnish"

If they are NOT the same entity, set same_entity to false. The canonical_name
field will be ignored.
""".strip()

SPECIES_RESOLUTION_PROMPT = """
You are a taxonomist and historian of natural history specialising in the Lewis
and Clark Expedition (1804-1806).

You will be given two species names extracted from the expedition journals.
Determine whether they refer to exactly the same biological species.

RULES — read carefully before deciding:

1. Same species only if they are the same taxon. Ecological similarity, shared
   habitat, or co-occurrence in the journals is NOT sufficient. When in doubt,
   set same_entity to false.

2. A broad common name that covers multiple species (e.g. "duck", "hawk",
   "eagle", "goat", "wolf", "deer", "squirrel") must NOT be merged with a
   specific scientific name unless you are certain the common name was used
   exclusively for that species in this corpus.

3. A genus-level placeholder (e.g. "ANAS SP.", "OVIS SP.") should only be merged
   with a species-level name if the species is the sole member of that genus
   likely to appear in the journals AND the common name evidence is unambiguous.

4. Canonical name must be a valid binomial in ALL CAPS (e.g. "CANIS LUPUS") or
   GENUS SP. in ALL CAPS. Never use a common name as the canonical name.

5. Known pairs that must NEVER be merged:
   - Wolf (CANIS LUPUS) != coyote (CANIS LATRANS) != domestic dog
   - Grouse (BONASA UMBELLUS) != prairie hen (TYMPANUCHUS CUPIDO) != wild turkey
   - Pronghorn (ANTILOCAPRA AMERICANA) != mountain goat (OREAMNOS AMERICANUS)
     != bighorn sheep (OVIS CANADENSIS)
   - White-tailed deer (ODOCOILEUS VIRGINIANUS) != mule deer (O. HEMIONUS)
   - Canada goose (BRANTA CANADENSIS) != brant (BRANTA BERNICLA)
   - Cottonwood (POPULUS DELTOIDES) != aspen (POPULUS TREMULOIDES)

If they are the same species, provide the accepted binomial in ALL CAPS as
canonical_name. If they are NOT the same species, set same_entity to false.
""".strip()


@dataclass
class Verdict:
    """One adjudicated pair."""

    pair: CandidatePair
    same_entity: bool
    canonical_name: str | None
    #: "cache" | "llm" | "skipped-cap" | "error"
    source: str
    error: str | None = None

    @property
    def decided(self) -> bool:
        return self.source in ("cache", "llm")


class AdjudicationBudget(RuntimeError):
    """Raised only when a caller asks for strict cap behaviour."""


def _schema():
    """The structured-output model, imported lazily.

    ``pydantic`` is a hard dependency of this module and of nothing else in the
    repo, which is why it is imported here rather than at module scope — a demo
    that never turns adjudication on should not need it installed.
    """
    from pydantic import BaseModel

    class ResolutionDecision(BaseModel):
        same_entity: bool
        canonical_name: str  # ignored when same_entity is False

    return ResolutionDecision


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=settings().openai_api_key)


def _cache_path(model: str, label: str, names: tuple[str, str]) -> Path:
    left, right = sorted(names)
    key = hashlib.sha256(f"{model}::{label}::{left}::{right}".encode()).hexdigest()[:32]
    return CACHE_DIR / f"{key}.json"


def _parse(model: str, label: str, left: str, right: str):
    """Call the model, tolerating the openai 3.x move of ``parse``.

    ``client.beta.chat.completions.parse`` became ``client.chat.completions.parse``
    in openai 3.8.0. The installed version here has the new path; the fallback
    keeps this working against the older client the corps repo pins.
    """
    client = _client()
    prompt = SPECIES_RESOLUTION_PROMPT if label in SPECIES_LABELS else RESOLUTION_PROMPT
    kwargs = dict(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Entity type: {label}\nName 1: {left}\nName 2: {right}",
            },
        ],
        response_format=_schema(),
    )
    endpoint = getattr(client.chat.completions, "parse", None)
    if endpoint is None:  # pragma: no cover - older client
        endpoint = client.beta.chat.completions.parse
    return endpoint(**kwargs).choices[0].message.parsed


def adjudicate(
    pairs: list[CandidatePair],
    *,
    enabled: bool = False,
    model: str = DEFAULT_MODEL,
    max_calls: int = DEFAULT_MAX_CALLS,
    use_cache: bool = True,
    strict_cap: bool = False,
) -> list[Verdict]:
    """Adjudicate candidate pairs. Returns one verdict per input pair.

    Does nothing unless ``enabled`` is True — an adjudication-shaped no-op is
    returned instead, so callers do not need two code paths.

    Cached verdicts do not count against ``max_calls``: the cap exists to bound
    spending and wall time, and a cache hit costs neither. Once the cap is
    reached, remaining pairs come back with ``source="skipped-cap"`` rather than
    raising, so a demo degrades to a partial answer instead of a traceback.
    Pass ``strict_cap=True`` to raise :class:`AdjudicationBudget` instead.
    """
    if not enabled:
        return [
            Verdict(pair=p, same_entity=False, canonical_name=None, source="disabled")
            for p in pairs
        ]

    verdicts: list[Verdict] = []
    calls_made = 0

    for pair in pairs:
        label = pair.left.label
        names = pair.names
        path = _cache_path(model, label, names)

        if use_cache and path.exists():
            cached = json.loads(path.read_text())
            verdicts.append(
                Verdict(
                    pair=pair,
                    same_entity=bool(cached["same_entity"]),
                    canonical_name=cached.get("canonical_name"),
                    source="cache",
                )
            )
            continue

        if calls_made >= max_calls:
            if strict_cap:
                raise AdjudicationBudget(
                    f"adjudication cap of {max_calls} calls reached with "
                    f"{len(pairs) - len(verdicts)} pairs still unjudged"
                )
            verdicts.append(
                Verdict(
                    pair=pair,
                    same_entity=False,
                    canonical_name=None,
                    source="skipped-cap",
                )
            )
            continue

        try:
            decision = _parse(model, label, names[0], names[1])
            calls_made += 1
        except Exception as exc:  # network, quota, schema drift
            verdicts.append(
                Verdict(
                    pair=pair,
                    same_entity=False,
                    canonical_name=None,
                    source="error",
                    error=str(exc),
                )
            )
            continue

        canonical = (decision.canonical_name or "").strip().upper() or None
        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "same_entity": decision.same_entity,
                        "canonical_name": canonical,
                        "names": list(names),
                        "label": label,
                        "model": model,
                    },
                    indent=2,
                )
            )

        verdicts.append(
            Verdict(
                pair=pair,
                same_entity=bool(decision.same_entity),
                canonical_name=canonical,
                source="llm",
            )
        )

    return verdicts


def confirmed_pairs(verdicts: list[Verdict]) -> list[CandidatePair]:
    """The pairs the judge accepted — the correct input to transitive closure.

    This is the ordering the original pipeline used and the demo reproduces:
    candidates are for recall, adjudication is for precision, and WCC runs
    **after** both. Running WCC over unadjudicated candidates is what produces
    a single component containing most of the expedition.
    """
    return [v.pair for v in verdicts if v.decided and v.same_entity]


def summarize(verdicts: list[Verdict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for verdict in verdicts:
        counts[verdict.source] = counts.get(verdict.source, 0) + 1
    counts["confirmed"] = sum(1 for v in verdicts if v.decided and v.same_entity)
    counts["rejected"] = sum(1 for v in verdicts if v.decided and not v.same_entity)
    return counts
