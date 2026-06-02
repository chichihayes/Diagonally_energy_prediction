import pandas as pd

_CSV_PATH = "data/raw/KAG_energydata_complete.csv"


def load_uci_csv() -> pd.DataFrame:
    return pd.read_csv(_CSV_PATH)


def load_and_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(_CSV_PATH)
    df = df.drop(columns=["date", "rv1", "rv2"])
    split = int(len(df) * 0.8)
    return df.iloc[:split].reset_index(drop=True), df.iloc[split:].reset_index(drop=True)
