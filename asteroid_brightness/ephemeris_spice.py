"""Optional cached Horizons asteroid SPK and SPICE position adapter.

This adapter needs a matching planetary SPK and leapseconds kernel supplied by
the caller. It returns geometric (no light-time correction) barycentric vectors.
"""
import base64
import hashlib
import json
from pathlib import Path
from datetime import timedelta
from astropy import units as u
from astropy.time import Time
import numpy as np


def download_asteroid_spk(asteroid_id, start_utc, stop_utc, cache_dir):
    """Download once from Horizons SPK API; return (cached BSP path, SPK ID)."""
    import requests

    start = Time(start_utc, scale="utc").isot
    stop = Time(stop_utc, scale="utc").isot
    if Time(stop_utc, scale="utc") <= Time(start_utc, scale="utc"):
        raise ValueError("stop_utc must be after start_utc")
    target = str(asteroid_id).rstrip(";")
    # Horizons SPK generation accepts calendar days; pad the requested UTC span.
    start_day = Time(start_utc, scale="utc").to_datetime().date().isoformat()
    stop_day = (Time(stop_utc, scale="utc").to_datetime().date() + timedelta(days=1)).isoformat()
    key = hashlib.sha256(f"number-v2|{target}|{start}|{stop}".encode()).hexdigest()[:20]
    cache = Path(cache_dir).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"asteroid_{key}.bsp"
    metadata = cache / f"asteroid_{key}.json"
    if path.is_file() and metadata.is_file():
        return path, json.loads(metadata.read_text(encoding="utf-8"))["spk_id"]
    response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api", params={
        "format": "json", "EPHEM_TYPE": "SPK", "OBJ_DATA": "NO",
        "COMMAND": f"'{target};'", "START_TIME": f"'{start_day}'",
        "STOP_TIME": f"'{stop_day}'"}, timeout=120)
    response.raise_for_status()
    data = response.json()
    if "spk" not in data or "spk_file_id" not in data:
        raise RuntimeError(f"Horizons SPK generation failed: {data.get('result', data.get('message', data))}")
    binary = base64.b64decode(data["spk"], validate=False)
    temporary = path.with_suffix(".partial")
    temporary.write_bytes(binary)
    temporary.replace(path)
    metadata.write_text(json.dumps({"spk_id": str(data["spk_file_id"]),
                                    "asteroid_id": target, "start_utc": start,
                                    "stop_utc": stop}, ensure_ascii=False), encoding="utf-8")
    return path, str(data["spk_file_id"])


def positions_from_spk(asteroid_spk, asteroid_spk_id, times_utc,
                       planetary_spk, leapseconds_kernel, observer_id="399"):
    """Return asteroid, observer, Sun barycentric J2000 positions in AU.

    The caller supplies NAIF planetary and leap-second kernels. All three
    vectors use the same barycentric origin, frame, and geometric epoch.
    """
    import spiceypy as spice

    scalar = isinstance(times_utc, str) or (isinstance(times_utc, Time) and times_utc.isscalar)
    times = [times_utc] if scalar else list(times_utc)
    if not times:
        raise ValueError("at least one UTC time is required")
    for kernel in (leapseconds_kernel, planetary_spk, asteroid_spk):
        if not Path(kernel).is_file():
            raise FileNotFoundError(kernel)
    kernels = [str(leapseconds_kernel), str(planetary_spk), str(asteroid_spk)]
    loaded = []
    try:
        for kernel in kernels:
            spice.furnsh(kernel)
            loaded.append(kernel)
        et = [spice.utc2et(Time(t, scale="utc").isot) for t in times]
        def vector(target, epoch):
            return np.asarray(spice.spkpos(str(target), epoch, "J2000", "NONE", "0")[0]) * u.km.to(u.au)
        ast = np.array([vector(asteroid_spk_id, t) for t in et])
        observer = np.array([vector(observer_id, t) for t in et])
        sun = np.array([vector("10", t) for t in et])
    finally:
        for kernel in reversed(loaded):
            spice.unload(kernel)
    return (ast[0], observer[0], sun[0]) if scalar else (ast, observer, sun)
