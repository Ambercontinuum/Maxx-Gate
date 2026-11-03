"""Stability — advice only, never load-bearing, labelled STUB unless real.

Advice: "verify" on a spike (K >= 5 or flip_rate > 0.2), otherwise
"proceed". Both K and flip_rate None means OFF / missing — the gate
treats that as missing, never as a clean signal. If this piece is off,
flat, or missing, the gate still works on cost rules alone.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Stability:
    k: float | None
    flip_rate: float | None
    advice: str
    source: str = "STUB"


def advise(k=None, flip_rate=None) -> Stability:
    if k is None and flip_rate is None:
        return Stability(k=None, flip_rate=None, advice="proceed", source="OFF")
    spike = (k is not None and k >= 5.0) or (flip_rate is not None and flip_rate > 0.2)
    return Stability(k=k, flip_rate=flip_rate, advice="verify" if spike else "proceed")


def is_missing(stability: Stability | None) -> bool:
    if stability is None:
        return True
    if stability.source == "OFF":
        return True
    return stability.k is None and stability.flip_rate is None
