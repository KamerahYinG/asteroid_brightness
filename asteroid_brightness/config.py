"""Default parameters for the simplified coplanar Kepler model."""
from dataclasses import dataclass
from datetime import datetime, timezone

K_GAUSSIAN = 0.01720209895  # AU**1.5 / day

@dataclass(frozen=True)
class OrbitParams:
    a_au: float
    e: float
    M0_deg: float
    t0: str

DEFAULT_ASTEROID = OrbitParams(2.2, 0.15, 20.0, "2026-01-01T00:00:00Z")
DEFAULT_EARTH = OrbitParams(1.0, 0.0, 0.0, "2026-01-01T00:00:00Z")
DEFAULT_H = 20.0
DEFAULT_G12 = 0.5
