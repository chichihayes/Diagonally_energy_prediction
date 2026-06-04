import logging
import os

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Loughborough, UK — monthly (mean_c, min_c) fallback when API is unavailable
_UK_MONTHLY_TEMPS: dict[int, tuple[float, float]] = {
    1: (3.0, 0.5),  2: (3.5, 0.5),  3: (6.0, 2.5),  4: (9.0, 4.5),
    5: (12.0, 7.0), 6: (15.5, 10.5), 7: (17.5, 12.5), 8: (17.0, 12.0),
    9: (14.0, 9.5), 10: (10.5, 6.0), 11: (6.5, 2.5), 12: (4.0, 1.0),
}

_CSV_PATH = "data/raw/House_1.csv"

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
    "day_of_week", "month", "is_weekend",
    "lag_1", "lag_7", "rolling_mean_7",
    "heater_lag_1", "heater_lag_7", "heater_rolling_mean_7",
    "temp_mean_c", "temp_min_c",
]

# ---------------------------------------------------------------------------
# Data split constants — single source of truth for train/test/demo dates
# ---------------------------------------------------------------------------

TEST_DATES = pd.to_datetime([
    "2013-10-16", "2014-12-07", "2015-01-03",  # LOW
    "2014-07-21", "2014-11-12", "2014-08-01",  # MID
    "2013-11-22", "2013-12-12", "2014-01-19",  # HIGH
])

DEMO_DATE = pd.Timestamp("2015-02-10")


# ===========================================================================
# PIPELINE STAGE 1 — Load raw data
# ===========================================================================

def load_house1_csv() -> pd.DataFrame:
    """
    Read House_1.csv.
    Returns a DataFrame indexed by datetime with one column per appliance (watts, 8-sec intervals).
    """
    df = pd.read_csv(_CSV_PATH)
    df["datetime"] = (
        pd.to_datetime(df["Unix"], unit="s", utc=True)
        .dt.tz_convert("Europe/London")
        .dt.tz_localize(None)
    )
    df = df.set_index("datetime")
    df = df.drop(columns=["Unix", "Aggregate"], errors="ignore")
    df = df.rename(columns=APPLIANCE_RENAME)
    present = [c for c in APPLIANCE_COLS if c in df.columns]
    logger.info("Stage 1 — loaded %d raw readings (%s to %s)",
                len(df), df.index.min().date(), df.index.max().date())
    return df[present]


# ===========================================================================
# PIPELINE STAGE 2 — Resample to 10-minute intervals
# ===========================================================================

def _resample_to_10min(df: pd.DataFrame) -> pd.DataFrame:
    """
    Average watts within each 10-minute window, clip negatives,
    interpolate short gaps (≤ 60 min), drop remaining NaN rows,
    and add aggregate_wh as the sum across all appliances per interval.
    """
    df = df.resample("10min").mean()
    df = df.clip(lower=0)
    present = [c for c in APPLIANCE_COLS if c in df.columns]
    df = df[present].interpolate(method="time", limit=6)
    df = df.dropna()
    df["aggregate_wh"] = df[present].sum(axis=1)
    logger.info("Stage 2 — resampled to 10-min: %d intervals", len(df))
    return df


# ===========================================================================
# PIPELINE STAGE 3 — Aggregate to daily totals
# ===========================================================================

def _aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sum all 10-min intervals within each calendar day.
    Adds day_of_week, month, is_weekend calendar columns.
    """
    present = [c for c in APPLIANCE_COLS if c in df.columns]
    daily = df[present + ["aggregate_wh"]].resample("D").sum()
    daily["day_of_week"] = daily.index.dayofweek
    daily["month"]       = daily.index.month
    daily["is_weekend"]  = (daily.index.dayofweek >= 5).astype(int)
    logger.info("Stage 3 — aggregated to %d daily rows (%s to %s)",
                len(daily), daily.index.min().date(), daily.index.max().date())
    return daily


# ===========================================================================
# PIPELINE STAGE 4 — Add lag features
# ===========================================================================

def _add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lag features from aggregate_wh and ElectricHeater.

    Aggregate lags:
      lag_1          — yesterday's total Wh
      lag_7          — same day last week's Wh
      rolling_mean_7 — 7-day rolling mean (shifted to avoid leakage)

    Heater lags (same structure):
      heater_lag_1, heater_lag_7, heater_rolling_mean_7

    First 7 rows will have NaN lags and are dropped in the final dropna().
    """
    agg    = df["aggregate_wh"]
    heater = df["ElectricHeater"]

    df["lag_1"]          = agg.shift(1)
    df["lag_7"]          = agg.shift(7)
    df["rolling_mean_7"] = agg.shift(1).rolling(7).mean()

    df["heater_lag_1"]          = heater.shift(1)
    df["heater_lag_7"]          = heater.shift(7)
    df["heater_rolling_mean_7"] = heater.shift(1).rolling(7).mean()

    logger.info("Stage 4 — lag features added (lag_1, lag_7, rolling_mean_7 for aggregate + heater)")
    return df


# ===========================================================================
# PIPELINE STAGE 5 — Merge temperature
# ===========================================================================

_TEMP_CSV_PATH = "data/raw/temperature_loughborough.csv"


def _load_temperature() -> pd.DataFrame:
    """
    Load temperature from the saved CSV (data/raw/temperature_loughborough.csv).
    Falls back to the Open-Meteo historical API if the file is missing,
    and saves the result so future runs don't need the API.
    """
    if os.path.exists(_TEMP_CSV_PATH):
        weather = pd.read_csv(_TEMP_CSV_PATH, parse_dates=["date"])
        weather = weather.rename(columns={"date": "datetime"}).set_index("datetime")
        logger.info("Stage 5 — temperature loaded from %s (%d rows)", _TEMP_CSV_PATH, len(weather))
        return weather

    logger.warning("Temperature file not found — fetching from Open-Meteo API and saving to disk")
    try:
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            "?latitude=52.77&longitude=-1.20"
            "&start_date=2013-10-09&end_date=2015-07-10"
            "&daily=temperature_2m_mean,temperature_2m_min,temperature_2m_max"
            "&timezone=Europe%2FLondon"
        )
        d = requests.get(url, timeout=30).json()["daily"]
        weather = pd.DataFrame({
            "date":        d["time"],
            "temp_mean_c": d["temperature_2m_mean"],
            "temp_min_c":  d["temperature_2m_min"],
        })
        os.makedirs("data/raw", exist_ok=True)
        weather.to_csv(_TEMP_CSV_PATH, index=False)
        logger.info("Temperature saved to %s for future runs", _TEMP_CSV_PATH)
        return weather.rename(columns={"date": "datetime"}).assign(
            datetime=lambda x: pd.to_datetime(x["datetime"])
        ).set_index("datetime")
    except Exception as exc:
        logger.warning("Temperature API unavailable (%s) — using UK monthly averages", exc)
        return pd.DataFrame()


def _merge_temperature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Join daily temperature (mean_c, min_c, max_c) onto the daily DataFrame.
    Source priority: saved CSV → Open-Meteo API → UK monthly climate averages.
    """
    weather = _load_temperature()

    if not weather.empty:
        df = df.join(weather[["temp_mean_c", "temp_min_c"]])
    else:
        df["temp_mean_c"] = df.index.month.map(lambda m: _UK_MONTHLY_TEMPS[m][0])
        df["temp_min_c"]  = df.index.month.map(lambda m: _UK_MONTHLY_TEMPS[m][1])
        logger.info("Stage 5 — temperature from UK monthly climate averages (fallback)")

    return df


# ===========================================================================
# Orchestrator — runs stages 1–5 in order
# ===========================================================================

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Run stages 2–5 on a raw loaded DataFrame. Returns the full clean daily dataset."""
    df = _resample_to_10min(df)
    df = _aggregate_daily(df)
    df = _add_lag_features(df)
    df = _merge_temperature(df)
    df = df.dropna()
    logger.info("Preprocessing complete — %d clean daily rows", len(df))
    return df


# ===========================================================================
# PIPELINE STAGE 6 — Split and save
# ===========================================================================


def save_processed_splits() -> None:
    """
    Full pipeline entry point. Runs all 6 stages and writes:

      data/processed/train.csv           all days except 9 test days
      data/processed/test.csv            9 strategic test days (3 LOW / 3 MID / 3 HIGH)
      src/model/trained/training_stats.json
    """
    # Stage 1
    raw = load_house1_csv()

    # Stages 2–5
    df = preprocess(raw)

    # Stage 6 — split
    holdout_mask = df.index.normalize().isin(TEST_DATES.normalize())

    train_df = df[~holdout_mask].copy()
    test_df  = df[holdout_mask].copy()

    os.makedirs("data/processed", exist_ok=True)
    train_df.reset_index().rename(columns={"index": "datetime"}).to_csv(
        "data/processed/train.csv", index=False
    )
    test_df.reset_index().rename(columns={"index": "datetime"}).to_csv(
        "data/processed/test.csv", index=False
    )
    logger.info(
        "Stage 6 — train.csv: %d days (%s to %s)",
        len(train_df), train_df.index.min().date(), train_df.index.max().date(),
    )
    logger.info("Stage 6 — test.csv: %d strategic test days", len(test_df))


# ===========================================================================
# Convenience loader (used by notebooks / evaluate_rf_retest)
# ===========================================================================

def load_all() -> pd.DataFrame:
    """Load and preprocess everything. No split, no side effects."""
    return preprocess(load_house1_csv())
