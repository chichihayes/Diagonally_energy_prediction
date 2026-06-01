import pandas as pd

_SIMPLE_FEATURES = ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]


def build_simple_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[_SIMPLE_FEATURES], df["Appliances"]
