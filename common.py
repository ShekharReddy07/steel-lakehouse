import re

import pandas as pd


def norm(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", col.strip().lower()).strip("_")


def load_energy(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [norm(c) for c in df.columns]
    need = {"date", "usage_kwh", "co2_tco2", "load_type"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")
    df["ts"] = pd.to_datetime(df["date"], dayfirst=True)
    return df.drop(columns=["date"])