import sys
from pathlib import Path

import numpy as np
import pandas as pd

from common import load_energy

DOWNTIME_REASONS = ["Furnace maintenance", "Power fluctuation", "Material shortage", "Mechanical failure"]
DEFECT_TYPES = ["Pastry", "Z_Scratch", "K_Scratch", "Stains", "Dirtiness", "Bumps", "Other_Faults"]


def main(src: str, out: str = "data/raw/production.csv"):
    e = load_energy(src).sort_values("ts").reset_index(drop=True)
    rng = np.random.default_rng(42)
    n = len(e)
    lt = e["load_type"].str.lower()
    is_max, is_med = lt.str.contains("max").values, lt.str.contains("med").values

    kwh_per_t = np.select([is_max, is_med], [42, 48], default=55) * rng.normal(1, 0.05, n)

    down = np.zeros(n, dtype=bool)
    reason = np.full(n, None, dtype=object)
    i = 0
    while i < n:
        if rng.random() < 0.004:
            dur = int(rng.integers(2, 16))
            down[i:i + dur] = True
            reason[i:i + dur] = rng.choice(DOWNTIME_REASONS)
            i += dur
        else:
            i += 1

    tonnes = np.where(down, 0.0, e["usage_kwh"].values / kwh_per_t)

    base_temp = np.select([is_max, is_med], [1600, 1570], default=1540)
    temp = np.where(down, 900, base_temp) + rng.normal(0, 12, n)
    spikes = rng.random(n) < 0.002
    temp[spikes] = rng.choice([0, 3000], spikes.sum())
    temp[rng.random(n) < 0.003] = np.nan

    defects = rng.poisson(tonnes * 0.03)
    defect_type = np.where(defects > 0, rng.choice(DEFECT_TYPES, n), None)

    df = pd.DataFrame({
        "ts": e["ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "tonnes_produced": tonnes.round(3),
        "furnace_temp_c": temp.round(1),
        "is_downtime": down,
        "downtime_reason": reason,
        "defect_count": defects,
        "defect_type": defect_type,
    })
    df = pd.concat([df, df.sample(frac=0.001, random_state=1)]).sort_values("ts")

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main(sys.argv[1])