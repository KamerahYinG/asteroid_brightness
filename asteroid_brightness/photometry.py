"""H-G12 photometry, independent of orbit and geometry implementation."""
import numpy as np
from astropy import units as u
from sbpy.photometry import HG12

def phase_function(alpha_deg, g12=0.5):
    """Return dimensionless Phi(alpha; G12), normalized to one at zero phase."""
    a = np.asarray(alpha_deg, dtype=float)
    if np.any((a < 0) | (a > 180)):
        raise ValueError("phase angle must be between 0 and 180 degrees")
    # HG12.evaluate returns H + phase magnitude; use H=0 to avoid double-counting H.
    a, g = np.broadcast_arrays(a, np.asarray(g12, dtype=float))
    if np.any(~np.isfinite(a)) or np.any(~np.isfinite(g)):
        raise ValueError("phase angle and G12 must be finite")
    # sbpy's original HG12 branches on a scalar G12, while phase angles vectorize.
    if np.all(g == g.flat[0]):
        val = HG12.evaluate(a * u.deg, 0.0, float(g.flat[0]))
        phase_mag = np.asarray(getattr(val, "value", val), dtype=float)
    else:
        phase_mag = np.empty(a.shape)
        for idx in np.ndindex(a.shape):
            val = HG12.evaluate(float(a[idx]) * u.deg, 0.0, float(g[idx]))
            phase_mag[idx] = float(getattr(val, "value", val))
    return np.power(10.0, -0.4 * phase_mag)

def magnitude(r_au, delta_au, alpha_deg, H=20.0, G12=0.5):
    r_au, delta_au, alpha_deg, H, G12 = np.broadcast_arrays(
        np.asarray(r_au, dtype=float), np.asarray(delta_au, dtype=float),
        np.asarray(alpha_deg, dtype=float), np.asarray(H, dtype=float),
        np.asarray(G12, dtype=float))
    if np.any(~np.isfinite(r_au)) or np.any(~np.isfinite(delta_au)) or np.any(r_au <= 0) or np.any(delta_au <= 0):
        raise ValueError("r and delta must be positive")
    phi = phase_function(alpha_deg, G12)
    if np.any(phi <= 0) or np.any(~np.isfinite(phi)):
        raise ValueError("invalid phase function value")
    result = H + 5 * np.log10(r_au * delta_au) - 2.5 * np.log10(phi)
    return float(result) if result.ndim == 0 else result
