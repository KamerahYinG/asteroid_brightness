"""Public brightness API. Only the JPL source needs a network connection."""
from dataclasses import dataclass
import numpy as np
from astropy.time import Time
from .config import DEFAULT_ASTEROID, DEFAULT_EARTH, OrbitParams
from .geometry import observation_geometry
from .orbit_kepler import position_au
from .photometry import magnitude


@dataclass(frozen=True)
class BrightnessResult:
    v_mag: float
    r_au: float
    delta_au: float
    alpha_deg: float
    time_utc: str | None = None
    jpl_v_mag: float | None = None
    jpl_h: float | None = None
    jpl_g: float | None = None


def magnitude_from_geometry(H, G12, r_au, delta_au, alpha_deg):
    """Offline H-G12 V magnitude; scalar inputs return float, arrays return ndarray."""
    return magnitude(r_au, delta_au, alpha_deg, H, G12)


def magnitude_from_positions(asteroid_pos_au, observer_pos_au, H, G12,
                             sun_pos_au=(0, 0, 0)):
    """Offline brightness from same-frame, same-origin, same-epoch AU vectors."""
    geom = observation_geometry(asteroid_pos_au, observer_pos_au, sun_pos_au)
    return magnitude_from_geometry(H, G12, **geom)


def magnitude_at(asteroid_id, time, H, G12, source="jpl", *,
                 asteroid_orbit: OrbitParams | None = None,
                 observer_orbit: OrbitParams = DEFAULT_EARTH):
    """Return one BrightnessResult or a list for UTC time sequences.

    ``source='kepler'`` requires asteroid_orbit; asteroid_id is then only a label.
    JPL comparison fields come from Horizons' own H-G model, not H-G12.
    """
    scalar = isinstance(time, (str, Time)) and (not isinstance(time, Time) or time.isscalar)
    values = [time] if scalar else list(time)
    if not values:
        raise ValueError("at least one UTC time is required")
    if source == "jpl":
        from .ephemeris_jpl import query_jpl_geometry
        rows = query_jpl_geometry(asteroid_id, values)
        results = [BrightnessResult(magnitude_from_geometry(H, G12, x.r_au, x.delta_au, x.alpha_deg),
                                    x.r_au, x.delta_au, x.alpha_deg, x.time_utc,
                                    x.jpl_v_mag, x.jpl_h, x.jpl_g) for x in rows]
    elif source == "kepler":
        if asteroid_orbit is None:
            raise ValueError("source='kepler' requires asteroid_orbit")
        results = []
        for t in values:
            ast = position_au(t, asteroid_orbit)
            obs = position_au(t, observer_orbit)
            g = observation_geometry(ast, obs)
            results.append(BrightnessResult(magnitude_from_geometry(H, G12, **g),
                                            g["r_au"], g["delta_au"], g["alpha_deg"],
                                            Time(t, scale="utc").isot + "Z"))
    else:
        raise ValueError("source must be 'jpl' or 'kepler'")
    return results[0] if scalar else results
