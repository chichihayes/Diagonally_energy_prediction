import json
import os

import pandas as pd
import numpy as np

_CSV_PATH = "data/raw/House1.csv"
_TRAIN_END = "2013-12-15"

APPLIANCE_RENAME = {
    "Appliance1": "Fridge",
    "Appliance2": "ChestFreezer",
    "Appliance3": "UprightFreezer",
    "Appliance4": "TumbleDryer",
    "Appliance5": "WashingMachine",
    "Appliance6": "Dishwasher",
    "Appliance7": "Computer",
    "Appliance8": "Television",
    "Appliance9": "ElectricHeater",
}

APPLIANCE_COLS = list(APPLIANCE_RENAME.values())

MODEL_FEATURES = [
    "hour", "day_of_week", "month", "is_weekend", "is_night", "is_peak_hour",
    "lag_1", "lag_6", "lag_144", "lag_1008",
    "rolling_mean_6", "rolling_mean_144", "rolling_std_6",
]

_OVERNIGHT_APPLIANCES = [
    "TumbleDryer", "WashingMachine", "Dishwasher",
    "Computer", "Television", "ElectricHeater",
]


def _cap_outliers_iqr(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        df[col] = df[col].clip(lower=q1 - 1.5 * iqr, upper=q3 + 1.5 * iqr)
    return df


def load_house1_csv() -> pd.DataFrame:
    df = pd.read_csv(_CSV_PATH)
    df["datetime"] = pd.to_datetime(df["Unix"], unit="s", utc=True).dt.tz_convert("Europe/London").dt.tz_localize(None)
    df = df.set_index("datetime")
    df = df.drop(columns=["Unix", "Aggregate"], errors="ignore")
    df = df.rename(columns=APPLIANCE_RENAME)
    present = [c for c in APPLIANCE_COLS if c in df.columns]
    return df[present]


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.resample("10min").mean()
    df = df.clip(lower=0)
    present = [c for c in APPLIANCE_COLS if c in df.columns]
    df = _cap_outliers_iqr(df, present)
    df = df.interpolate(method="time", limit=6)
    df = df.dropna()
    df["aggregate_wh"] = df[present].sum(axis=1)
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)
    df["is_night"] = ((df.index.hour >= 22) | (df.index.hour < 6)).astype(int)
    df["is_peak_hour"] = ((df.index.hour >= 16) & (df.index.hour <= 20)).astype(int)
    agg = df["aggregate_wh"]
    df["lag_1"] = agg.shift(1)
    df["lag_6"] = agg.shift(6)
    df["lag_144"] = agg.shift(144)
    df["lag_1008"] = agg.shift(1008)
    df["rolling_mean_6"] = agg.shift(1).rolling(6).mean()
    df["rolling_mean_144"] = agg.shift(1).rolling(144).mean()
    df["rolling_std_6"] = agg.shift(1).rolling(6).std()
    return df.dropna()


def load_and_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = load_house1_csv()
    df = preprocess(raw)

    train = df[df.index.normalize() <= pd.Timestamp(_TRAIN_END)].copy()
    test = df[df.index.normalize() > pd.Timestamp(_TRAIN_END)].copy()

    os.makedirs("src/model/trained", exist_ok=True)

    stat_cols = APPLIANCE_COLS + ["aggregate_wh"]
    appliance_stats = {
        col: {"mean": float(train[col].mean()), "std": float(train[col].std())}
        for col in stat_cols
        if col in train.columns
    }

    overnight_mask = (train.index.hour >= 22) | (train.index.hour < 6)
    overnight = train[overnight_mask]
    overnight_thresholds = {
        col: float(overnight[col].mean() + 2 * overnight[col].std())
        for col in _OVERNIGHT_APPLIANCES
        if col in train.columns
    }

    stats = {
        "appliance_stats": appliance_stats,
        "overnight_thresholds": overnight_thresholds,
    }
    with open("src/model/trained/training_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    os.makedirs("data/processed", exist_ok=True)
    train.to_csv("data/processed/train.csv")
    test.to_csv("data/processed/test.csv")

    return train, test
