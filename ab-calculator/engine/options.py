"""Method choices (SPEC Step 0, BACKLOG B21).

PM mode is Expert mode with locked defaults: both call the same engine
functions. The PM version (v1) uses only the defaults below. Expert mode
(v2) will let users change them. Until then, any other value raises
NotImplementedError, like the data-source stubs.
"""

from __future__ import annotations

from typing import Literal

CIMethod = Literal["wald", "newcombe"]
Alternative = Literal["two-sided", "greater", "less"]
NIMethod = Literal["standard", "advanced"]

DEFAULT_CI_METHOD: CIMethod = "wald"            # SPEC 1.2
DEFAULT_ALTERNATIVE: Alternative = "two-sided"  # SPEC 1.1, superiority
DEFAULT_NI_METHOD: NIMethod = "standard"        # Blackwelder, as Sealed Envelope

# Values that work in v1. Everything else is an Expert-mode option (v2).
V1_SUPPORTED: dict[str, set[str]] = {
    "ci_method": {DEFAULT_CI_METHOD},
    "alternative": {DEFAULT_ALTERNATIVE},
    "ni_method": {DEFAULT_NI_METHOD},
}


def require_v1(name: str, value: str) -> None:
    """Raise NotImplementedError if `value` is not available in v1."""
    if value not in V1_SUPPORTED[name]:
        raise NotImplementedError(
            f"{name}={value!r} is an Expert-mode option (v2). "
            f"v1 supports: {sorted(V1_SUPPORTED[name])}."
        )
