"""Shared entry-point wrapper for the scripts.

Turns the two failures every newcomer hits — no ``.env``, no GDS projection —
into a one-line instruction instead of a traceback.
"""

from __future__ import annotations

from typing import Callable

from .config import ConfigError


def run(main: Callable[[], int]) -> int:
    try:
        return main()
    except ConfigError as exc:
        print(f"\nConfiguration error: {exc}")
        return 2
    except RuntimeError as exc:
        print(f"\n{exc}")
        return 2
    except KeyboardInterrupt:
        print()
        return 130
