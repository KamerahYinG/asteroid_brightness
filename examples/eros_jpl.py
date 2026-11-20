"""Query Eros, compare H-G12 with Horizons V, and save a PNG + CSV."""
import csv
from pathlib import Path
from astropy.time import Time, TimeDelta
from asteroid_brightness import magnitude_at


def main():
    start = Time("2026-11-01T00:00:00", scale="utc")
    times = [(start + TimeDelta(i * 2, format="jd")).isot + "Z" for i in range(16)]
    rows = magnitude_at(433, times, H=10.4, G12=0.5)
    out = Path("asteroid_brightness/outputs")
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    with (out / "data" / "eros_jpl.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_utc", "r_au", "delta_au", "alpha_deg",
                         "hg12_v_mag", "jpl_v_mag", "jpl_h", "jpl_g"])
        for row in rows:
            writer.writerow([row.time_utc, row.r_au, row.delta_au, row.alpha_deg,
                             row.v_mag, row.jpl_v_mag, row.jpl_h, row.jpl_g])
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    dates = [Time(row.time_utc).to_datetime() for row in rows]
    ax.plot(dates, [row.v_mag for row in rows], "o-", label="H-G12 (H=10.4, G12=0.5)")
    ax.plot(dates, [row.jpl_v_mag for row in rows], "s--", label="JPL reference V (H-G)")
    ax.set(xlabel="UTC time", ylabel="V magnitude", title="433 Eros: JPL geometry")
    ax.invert_yaxis(); ax.legend(); ax.grid(True, alpha=.3)
    fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(out / "figures" / "eros_jpl_comparison.png", dpi=150)
    plt.close(fig)
    print(f"Saved {len(rows)} epochs; {rows[0]}; {rows[-1]}")


if __name__ == "__main__":
    main()
