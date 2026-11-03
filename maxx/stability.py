"""3. Stability — advice only, never load-bearing.

Petermann K = ||u|| * ||v|| / |<v, u>|, where u is a right eigenvector and
v is a left eigenvector. K = 1 for a Hermitian/normal case; K grows as
eigenvectors become nearly parallel; K diverges at an exceptional point.
JSD is the Jensen-Shannon divergence between proposed and perturbed outputs.

Scaffold advice thresholds below are placeholders, NOT locked values.
Amber sets LOCKED thresholds from a calibration run. If this piece is
off, flat, or missing, the gate still works on temperature rules alone.
"""
import cmath
import math
from dataclasses import dataclass


def petermann_k(u, v) -> float:
    """u, v: sequences of complex numbers. Invariant to eigenvector scaling."""
    def norm(x):
        return math.sqrt(sum(abs(z) ** 2 for z in x))

    inner = sum(complex(a).conjugate() * complex(b) for a, b in zip(v, u))
    if abs(inner) == 0:
        return math.inf
    return norm(u) * norm(v) / abs(inner)


def jsd(p, q) -> float:
    """Jensen-Shannon divergence, natural log. Result in [0, ln 2]."""
    def normed(x):
        total = sum(x)
        if total <= 0:
            raise ValueError("distribution must sum to > 0")
        return [v / total for v in x]

    p, q = normed(p), normed(q)
    if len(p) != len(q):
        raise ValueError("distributions must have the same length")
    m = [(a + b) / 2 for a, b in zip(p, q)]

    def kl(a, b):
        return sum(x * math.log(x / y) for x, y in zip(a, b) if x > 0)

    return (kl(p, m) + kl(q, m)) / 2


@dataclass(frozen=True)
class Stability:
    k: float | None
    flip_rate: float | None
    advice: str  # "verify" | "proceed"
    source: str = "STUB"  # replaced by "Glimmer" when real telemetry plugs in


def is_missing(stability: "Stability | None") -> bool:
    """PROPOSED helper 2026-10-28: OFF counts as missing, not as present.

    advise(None, None) still returns advice="proceed", source="OFF" for
    backward compatibility, but the GATE must treat that as missing (see
    gate._is_missing). Do not read an OFF advice as a clean signal.
    """
    if stability is None:
        return True
    if stability.source == "OFF":
        return True
    return stability.k is None and stability.flip_rate is None


def advise(k=None, flip_rate=None) -> Stability:
    """Scaffold advice: verify on spike or flips, proceed otherwise.

    NOTE (PROPOSED patch 2026-10-28): when off (both None), this returns
    proceed/OFF for backward compatibility ONLY. The gate treats OFF as
    missing, never as a present clean signal. See is_missing().
    """
    if k is None and flip_rate is None:
        return Stability(k=None, flip_rate=None, advice="proceed", source="OFF")
    spike = (k is not None and k >= 5.0) or (flip_rate is not None and flip_rate > 0.2)
    return Stability(k=k, flip_rate=flip_rate, advice="verify" if spike else "proceed")
