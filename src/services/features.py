import pandas as pd

_SIMPLE_FEATURES = ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]

_FULL_COLS = [
    "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
    "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
    "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
]


def build_simple_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[_SIMPLE_FEATURES], df["Appliances"]


def build_full_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[_FULL_COLS], df["Appliances"]


def assemble_simple_features(lights: int, T1: float, weather: dict) -> dict:
    return {
        "lights": lights,
        "T1": T1,
        "T_out": weather["T_out"],
        "RH_out": weather["RH_out"],
        "Windspeed": weather["Windspeed"],
        "Visibility": weather["Visibility"],
        "Tdewpoint": weather["Tdewpoint"],
    }
