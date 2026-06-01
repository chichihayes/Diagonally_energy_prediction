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


_model_full = None


def _get_full_model():
    global _model_full
    if _model_full is None:
        path = os.environ.get("MODEL_PATH_FULL", "src/model/trained/model_full.joblib")
        _model_full = joblib.load(path)
    return _model_full


def predict_full(features: dict) -> float:
    model = _get_full_model()
    df = pd.DataFrame([features])
    return float(model.predict(df)[0])
