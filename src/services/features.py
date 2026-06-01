import pandas as pd

_SIMPLE_FEATURES = ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]


def build_simple_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[_SIMPLE_FEATURES], df["Appliances"]


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
