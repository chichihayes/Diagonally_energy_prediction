import os

import joblib
import pandas as pd

_model_simple = None


def _get_simple_model():
    global _model_simple
    if _model_simple is None:
        path = os.environ.get("MODEL_PATH_SIMPLE", "src/model/trained/model_simple.joblib")
        _model_simple = joblib.load(path)
    return _model_simple


def predict_simple(features: dict) -> float:
    model = _get_simple_model()
    df = pd.DataFrame([features])
    return float(model.predict(df)[0])
