"""Observation geometry from heliocentric position vectors."""
import numpy as np

def observation_geometry(asteroid_pos_au, observer_pos_au, sun_pos_au=(0, 0, 0)):
    """Compute r, Delta and Sun–asteroid–observer angle from common-frame AU vectors.

    Inputs may have shape (3,) or broadcastable shape (..., 3).
    """
    ast, observer, sun = (np.asarray(x, dtype=float) for x in
                          (asteroid_pos_au, observer_pos_au, sun_pos_au))
    if any(x.ndim < 1 or x.shape[-1] != 3 for x in (ast, observer, sun)):
        raise ValueError("position vectors must have shape (..., 3)")
    if not all(np.all(np.isfinite(x)) for x in (ast, observer, sun)):
        raise ValueError("position vectors must be finite")
    toward_sun, toward_observer = sun - ast, observer - ast
    r = np.linalg.norm(toward_sun, axis=-1)
    delta = np.linalg.norm(toward_observer, axis=-1)
    if np.any(r <= 0) or np.any(delta <= 0):
        raise ValueError("heliocentric and observer distances must be positive")
    cosine = np.sum(toward_sun * toward_observer, axis=-1) / (r * delta)
    alpha = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    scalar = np.ndim(alpha) == 0
    return {"r_au": float(r) if scalar else r,
            "delta_au": float(delta) if scalar else delta,
            "alpha_deg": float(alpha) if scalar else alpha}
