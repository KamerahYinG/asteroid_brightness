"""Online Horizons observer tables. No photometric model is applied here."""
from dataclasses import dataclass
import numpy as np
from astropy.time import Time


@dataclass(frozen=True)
class JplGeometry:
    time_utc: str
    r_au: float
    delta_au: float
    alpha_deg: float
    jpl_v_mag: float | None = None
    jpl_h: float | None = None
    jpl_g: float | None = None


def _optional_float(row, name):
    if name not in row.colnames:
        return None
    value = row[name]
    if np.ma.is_masked(value):
        return None
    result = float(value)
    return result if np.isfinite(result) else None


def query_jpl_geometry(asteroid_id, times):
    """Query Earth-geocenter Horizons geometry at UTC epochs; preserve input order."""
    from astroquery.jplhorizons import Horizons

    values = [times] if isinstance(times, (str, Time)) else list(times)
    if not values:
        raise ValueError("at least one UTC time is required")
    epochs = Time(values, scale="utc")
    # 500@399 is Earth's geocenter. The trailing semicolon selects a small body.
    target = str(asteroid_id).rstrip(";") + ";"
    tables = []
    # Keep epoch lists short enough for Horizons' URI length limit.
    for first in range(0, len(values), 30):
        chunk = list(epochs.utc.jd[first:first + 30])
        tables.append(Horizons(id=target, location="500@399", epochs=chunk).ephemerides(
            quantities="9,19,20,24"))
    if sum(len(table) for table in tables) != len(values):
        raise RuntimeError("Horizons returned an unexpected number of epochs")
    output = []
    for i, row in enumerate(row for table in tables for row in table):
        output.append(JplGeometry(
            epochs[i].isot + "Z", float(row["r"]), float(row["delta"]),
            float(row["alpha"]), _optional_float(row, "V"),
            _optional_float(row, "H"), _optional_float(row, "G")))
    return output
