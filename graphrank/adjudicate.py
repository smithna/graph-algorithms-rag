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

#: Chosen by measurement, not by reputation — see the table below.
#:
#: The pipeline this ports from uses `gpt-4o-mini`, which was the sensible
#: default when it was written in 2024. It is now the worst of the six models
#: benchmarked on this exact task, and not by a little.
#:
#: Scored over 187 labelled Person pairs from the pre-disambiguation graph
#: (48 real duplicates, 139 non-duplicates), against the identity gold set:
#:
#:     model           TP  FP  FN   precision  recall     F1   wall
#:     gpt-4o-mini     31   0  17       1.000   0.646  0.785    16s
#:     gpt-4.1-nano    39   0   9       1.000   0.812  0.897    13s
#:     gpt-5-nano      39   0   9       1.000   0.812  0.897   105s
#:     gpt-5-mini      47   0   1       1.000   0.979  0.989    89s
#:     gpt-5.4-nano    47   0   1       1.000   0.979  0.989    18s
#:     gpt-5.6-luna    48   0   0       1.000   1.000  1.000    30s
#:
#: Two things stand out. **Every model has perfect precision.** On a task this
#: constrained they are all conservative, and none of them invented a merge. So
#: the entire spread is recall — the differentiator is how many real duplicates
#: a model is willing to recognise, and `gpt-4o-mini` misses a third of them
#: (`GEORGE DREWYER`/`GEORGE DROUILLARD`, `SILAS GOODRICH`/`SILAS GUTRICH`, most
#: of the Bratton variants).
#:
#: And **the price difference is irrelevant at this scale.** Adjudicating every
#: Person candidate pair in the corpus costs roughly 9 cents on `gpt-4o-mini`
#: and 12 cents here. Three cents buys 35 points of recall. Choose on quality;
#: the whole corpus is pocket change either way.
#:
#: Caveat worth keeping: the top three are separated by one pair each on a
#: 187-pair sample, so they are statistically indistinguishable. The gap down to
#: `gpt-4o-mini` is not. Re-run `--compare-models` on your own corpus rather
#: than trusting this ordering.
DEFAULT_MODEL = "gpt-5.6-luna"

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

    try:
        return endpoint(**kwargs).choices[0].message.parsed
    except Exception as exc:
        # The GPT-5 generation rejects an explicit temperature outright:
        #   "Unsupported value: 'temperature' does not support 0 with this model"
        # Determinism was the only reason it was set, and those models are
        # already low-variance on a task this constrained. Drop it and retry
        # rather than pinning this repo to one model generation.
        if "temperature" not in str(exc):
            raise
        kwargs.pop("temperature", None)
        return endpoint(**kwargs).choices[0].message.parsed


def adjudicate(
    pairs: list[CandidatePair],
    *,
    enabled: bool = False,
    model: str = DEFAULT_MODEL,
    max_calls: int = DEFAULT_MAX_CALLS,
    use_cache: bool = True,
    strict_cap: bool = False,
    max_workers: int = 8,
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

    # Cache lookups first, serially and cheaply: they cost nothing and they
    # decide how much real work is left.
    results: list[Verdict | None] = [None] * len(pairs)
    todo: list[int] = []
    for i, pair in enumerate(pairs):
        path = _cache_path(model, pair.left.label, pair.names)
        if use_cache and path.exists():
            try:
                cached = json.loads(path.read_text())
                results[i] = Verdict(
                    pair=pair,
                    same_entity=bool(cached["same_entity"]),
                    canonical_name=cached.get("canonical_name"),
                    source="cache",
                )
                continue
            except Exception:
                pass
        todo.append(i)

    # The remainder in parallel. Serial adjudication of a few thousand pairs is
    # hours; the calls are independent and IO-bound, so this is the whole fix.
    import threading
    lock = threading.Lock()
    calls_made = 0

    def judge_one(i: int) -> Verdict:
        nonlocal calls_made
        pair = pairs[i]
        label = pair.left.label
        with lock:
            if calls_made >= max_calls:
                if strict_cap:
                    raise AdjudicationBudget(
                        f"adjudication cap of {max_calls} calls reached"
                    )
                return Verdict(pair=pair, same_entity=False, canonical_name=None,
                               source="skipped-cap")
            calls_made += 1
        try:
            decision = _parse(model, label, *pair.names)
        except Exception as exc:
            return Verdict(pair=pair, same_entity=False, canonical_name=None,
                           source="error", error=str(exc))
        canonical = (decision.canonical_name or "").strip().upper() or None
        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _cache_path(model, label, pair.names).write_text(json.dumps({
                "same_entity": decision.same_entity, "canonical_name": canonical,
                "names": list(pair.names), "label": label, "model": model}, indent=2))
        return Verdict(pair=pair, same_entity=bool(decision.same_entity),
                       canonical_name=canonical, source="llm")

    if todo:
        import concurrent.futures as futures
        with futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            for i, v in zip(todo, pool.map(judge_one, todo)):
                results[i] = v

    return [v for v in results if v is not None]


def cached_verdict(
    left: str, right: str, label: str, model: str = DEFAULT_MODEL
) -> bool | None:
    """Look up a previously adjudicated pair without calling the model.

    Returns True/False if this exact pair was judged before, else None.

    This is what makes transitivity verification affordable. Candidate
    adjudication rejects most of what it sees and the pipeline throws those
    rejections away — but a rejection is precisely the evidence the transitivity
    check needs. `SACAGAWEA ~ TOUSSAINT CHARBONNEAU` co-occur in nearly every
    passage, so they are almost certainly proposed as a candidate and rejected
    long before anything asks whether `HIS WIFE` bridges them.

    Keeping negatives turns "ask the model again" into a dictionary lookup.
    """
    path = _cache_path(model, label, (left, right))
    if not path.exists():
        return None
    try:
        return bool(json.loads(path.read_text())["same_entity"])
    except Exception:
        return None


def cached_canonical(
    left: str, right: str, label: str, model: str = DEFAULT_MODEL
) -> str | None:
    """The canonical name the judge chose when it confirmed this pair, if any.

    Every confirmation names the "most complete, modern, and widely accepted
    form" — evidence the merge step should use instead of guessing. Picking the
    longest member name instead is what left Sacagawea's merged node called
    "Our Interpreter The Snake Woman" and Jefferson's called "President Of The
    States Of America": length measures wordiness, not canonicity.
    """
    path = _cache_path(model, label, (left, right))
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text())
        if cached.get("same_entity"):
            return cached.get("canonical_name") or None
    except Exception:
        pass
    return None


def confirmed_pairs(verdicts: list[Verdict]) -> list[CandidatePair]:
    """The pairs the judge accepted — the correct input to transitive closure.

    This is the ordering the original pipeline used and the demo reproduces:
    candidates are for recall, adjudication is for precision, and WCC runs
    **after** both. Running WCC over unadjudicated candidates is what produces
    a single component containing most of the expedition.
    """
    return [v.pair for v in verdicts if v.decided and v.same_entity]


#: The lineup `--compare-models` runs by default. Cheap tiers only: the judge is
#: doing constrained binary classification, and the frontier models cost 10-50x
#: for a task the small ones already saturate.
CANDIDATE_MODELS = [
    "gpt-4o-mini",
    "gpt-4.1-nano",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-5.4-nano",
    "gpt-5.6-luna",
]


@dataclass
class ModelScore:
    model: str
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    errors: int
    seconds: float
    missed: list[tuple[str, str]]

    @property
    def precision(self) -> float:
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def benchmark_models(
    labelled: list[tuple[CandidatePair, bool]],
    *,
    models: list[str] | None = None,
    max_workers: int = 8,
) -> list[ModelScore]:
    """Score each model against pairs whose correct answer is already known.

    ``labelled`` is (pair, is_really_the_same_entity). The gold set supplies the
    labels, so this measures the judge rather than the signals that nominated
    the pairs.

    Deliberately bypasses the verdict cache: comparing models means actually
    calling them. It is a few cents for the whole sweep.
    """
    import concurrent.futures as futures
    import time

    models = models or CANDIDATE_MODELS
    scores: list[ModelScore] = []

    for model in models:

        def judge(item):
            pair, truth = item
            try:
                decision = _parse(model, pair.left.label, *pair.names)
                return pair, truth, bool(decision.same_entity), None
            except Exception as exc:  # model unavailable, schema drift, quota
                return pair, truth, None, str(exc).split("\n")[0][:90]

        started = time.perf_counter()
        tp = fp = tn = fn = errors = 0
        missed: list[tuple[str, str]] = []
        with futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            for pair, truth, predicted, error in pool.map(judge, labelled):
                if predicted is None:
                    errors += 1
                elif truth and predicted:
                    tp += 1
                elif truth and not predicted:
                    fn += 1
                    missed.append(pair.names)
                elif not truth and predicted:
                    fp += 1
                    missed.append(pair.names)
                else:
                    tn += 1

        scores.append(
            ModelScore(
                model=model,
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
                errors=errors,
                seconds=time.perf_counter() - started,
                missed=missed,
            )
        )

    return scores


def summarize(verdicts: list[Verdict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for verdict in verdicts:
        counts[verdict.source] = counts.get(verdict.source, 0) + 1
    counts["confirmed"] = sum(1 for v in verdicts if v.decided and v.same_entity)
    counts["rejected"] = sum(1 for v in verdicts if v.decided and not v.same_entity)
    return counts
