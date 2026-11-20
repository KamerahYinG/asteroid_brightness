"""Command line interface and high-level simulation functions."""
import argparse, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
from astropy.time import Time, TimeDelta
try:
    from .config import DEFAULT_ASTEROID, DEFAULT_EARTH, DEFAULT_H, DEFAULT_G12, OrbitParams
    from .orbit_kepler import position_au, orbital_period_days
    from .geometry import observation_geometry
    from .photometry import magnitude
except ImportError:  # allow `python main.py` from this directory
    from config import DEFAULT_ASTEROID, DEFAULT_EARTH, DEFAULT_H, DEFAULT_G12, OrbitParams
    from orbit_kepler import position_au, orbital_period_days
    from geometry import observation_geometry
    from photometry import magnitude

def magnitude_at(t, params=DEFAULT_ASTEROID, earth_params=DEFAULT_EARTH, H=DEFAULT_H, G12=DEFAULT_G12):
    ast = position_au(t, params); earth = position_au(t, earth_params)
    geom = observation_geometry(ast, earth)
    return {"time_utc": Time(t, scale="utc").isot + "Z", "position_au": ast,
            **geom, "V_mag": magnitude(geom["r_au"], geom["delta_au"], geom["alpha_deg"], H, G12)}

def time_series(start, end, step_days, params=DEFAULT_ASTEROID, H=DEFAULT_H, G12=DEFAULT_G12):
    if step_days <= 0: raise ValueError("step_days must be positive")
    t0, t1 = Time(start, scale="utc"), Time(end, scale="utc")
    if t1 < t0: raise ValueError("end must not precede start")
    out=[]; t=t0
    while t <= t1 + 1e-10 * (t1-t0):
        out.append(magnitude_at(t.isot + "Z", params, DEFAULT_EARTH, H, G12)); t += TimeDelta(step_days, format="jd")
    return out

def write_csv(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["time_utc","r_au","delta_au","alpha_deg","V_mag"])
        for x in rows: w.writerow([x["time_utc"], f'{x["r_au"]:.9f}', f'{x["delta_au"]:.9f}', f'{x["alpha_deg"]:.6f}', f'{x["V_mag"]:.6f}'])

def plot_outputs(rows, outdir="outputs/figures", H=DEFAULT_H):
    import matplotlib.pyplot as plt
    Path(outdir).mkdir(parents=True, exist_ok=True); times=[Time(x["time_utc"]).to_datetime() for x in rows]
    fig,ax=plt.subplots(); ax.plot(times,[x["V_mag"] for x in rows]); ax.invert_yaxis(); ax.set(xlabel="UTC time",ylabel="V magnitude"); fig.autofmt_xdate(); fig.savefig(Path(outdir)/"magnitude_vs_time.png",dpi=150); plt.close(fig)
    fig,axs=plt.subplots(3,1,sharex=True,figsize=(7,8));
    for a,k,l in zip(axs,["r_au","delta_au","alpha_deg"],["r (AU)","Delta (AU)","Phase angle (deg)"]): a.plot(times,[x[k] for x in rows]); a.set_ylabel(l); a.grid(True,alpha=.3)
    axs[-1].set_xlabel("UTC time"); fig.autofmt_xdate(); fig.savefig(Path(outdir)/"geometry_vs_time.png",dpi=150); plt.close(fig)
    al=np.linspace(0,120,241); fig,ax=plt.subplots()
    for g in [0.0,0.5,0.9]: ax.plot(al,[magnitude(1,1,a,H,g) for a in al],label=f"G12={g}")
    ax.set(xlabel="Phase angle (deg)",ylabel="V magnitude"); ax.legend(); ax.grid(True,alpha=.3); fig.savefig(Path(outdir)/"phase_curves.png",dpi=150); plt.close(fig)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--time"); p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--step-days",type=float,default=2); p.add_argument("--plot",action="store_true"); args=p.parse_args()
    if args.time:
        x=magnitude_at(args.time); print(f"time_utc: {x['time_utc']}\nposition_au: {x['position_au']}\nr_au: {x['r_au']:.6f}\ndelta_au: {x['delta_au']:.6f}\nalpha_deg: {x['alpha_deg']:.4f}\nV_mag: {x['V_mag']:.6f}")
    elif args.start and args.end:
        rows=time_series(args.start,args.end,args.step_days)
        base = Path(__file__).resolve().parent / "outputs"
        write_csv(rows, base / "data" / "demo.csv")
        if args.plot: plot_outputs(rows, base / "figures"); print(f"Wrote {base / 'data' / 'demo.csv'} and {base / 'figures'}/*.png")
    else: p.error("provide --time or --start and --end")
if __name__ == "__main__": main()
