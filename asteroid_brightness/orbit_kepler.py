"""Two-body, heliocentric Kepler orbits.  This module only returns positions."""
import numpy as np
from astropy.time import Time
try:
    from .config import K_GAUSSIAN, OrbitParams
except ImportError:  # direct script compatibility
    from config import K_GAUSSIAN, OrbitParams

def _validate(p: OrbitParams):
    if p.a_au <= 0:
        raise ValueError("semi-major axis a must be positive")
    if not 0 <= p.e < 1:
        raise ValueError("eccentricity e must satisfy 0 <= e < 1")

def _days(t, t0):
    return float((Time(t, scale="utc") - Time(t0, scale="utc")).to_value("day"))

def position_au(t, params: OrbitParams) -> np.ndarray:
    """Return heliocentric equatorial-plane position [x,y,z] in AU."""
    _validate(params)
    dt = _days(t, params.t0)
    n = K_GAUSSIAN / params.a_au ** 1.5
    M = np.deg2rad(params.M0_deg) + n * dt
    M = np.remainder(M, 2 * np.pi)
    E = M if params.e < 0.8 else np.pi
    for _ in range(50):
        d = (E - params.e * np.sin(E) - M) / (1 - params.e * np.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    x = params.a_au * (np.cos(E) - params.e)
    y = params.a_au * np.sqrt(1 - params.e**2) * np.sin(E)
    return np.array([x, y, 0.0], dtype=float)

def orbital_period_days(params: OrbitParams) -> float:
    _validate(params)
    return 2 * np.pi * params.a_au ** 1.5 / K_GAUSSIAN
