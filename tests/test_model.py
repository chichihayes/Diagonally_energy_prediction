import pytest


def test_predict_simple_returns_float(tmp_path, monkeypatch):
    import joblib
    import pandas as pd
    from sklearn.dummy import DummyRegressor

    dummy = DummyRegressor(strategy="constant", constant=60.5)
    X = pd.DataFrame([{
        "lights": 0, "T1": 20.0, "T_out": 28.0,
        "RH_out": 80.0, "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
    }])
    dummy.fit(X, [60.5])
    model_path = tmp_path / "model_simple.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_SIMPLE", str(model_path))

    import importlib
    from src.model import predict as predict_module
    importlib.reload(predict_module)

    features = {
        "lights": 0, "T1": 20.0, "T_out": 28.0,
        "RH_out": 80.0, "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0,
    }
    result = predict_module.predict_simple(features)
    assert isinstance(result, float)
    assert result == pytest.approx(60.5)


def test_data_loader_returns_train_test_split():
    from src.services.data_loader import load_and_split
    train, test = load_and_split()
    assert len(train) + len(test) == 19735
    assert len(train) == pytest.approx(19735 * 0.8, abs=5)
    assert "rv1" not in train.columns
    assert "rv2" not in train.columns
    assert "date" not in train.columns
    assert "Appliances" in train.columns


def test_train_full_produces_loadable_model(tmp_path):
    import joblib
    import pandas as pd
    from src.model.train_full import train_and_save
    out = tmp_path / "model_full.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    model = joblib.load(str(out))
    sample = pd.DataFrame([{
        "lights": 0, "T1": 19.89, "RH_1": 47.6, "T2": 19.2, "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73, "T4": 17.17, "RH_4": 41.67, "T5": 17.2,
        "RH_5": 55.2, "T6": 7.03, "RH_6": 84.26, "T7": 17.2, "RH_7": 41.63,
        "T8": 18.2, "RH_8": 48.9, "T9": 17.03, "RH_9": 45.53,
        "T_out": 6.6, "Press_mm_hg": 733.5, "RH_out": 92.0,
        "Windspeed": 7.0, "Visibility": 63.0, "Tdewpoint": 5.3,
    }])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)


def test_predict_full_returns_float(tmp_path, monkeypatch):
    import joblib
    import pandas as pd
    from sklearn.dummy import DummyRegressor

    cols = [
        "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    dummy = DummyRegressor(strategy="constant", constant=150.0)
    X = pd.DataFrame([{c: 1.0 for c in cols}])
    dummy.fit(X, [150.0])
    model_path = tmp_path / "model_full.joblib"
    joblib.dump(dummy, str(model_path))
    monkeypatch.setenv("MODEL_PATH_FULL", str(model_path))

    from src.model import predict as predict_module
    import importlib
    importlib.reload(predict_module)

    result = predict_module.predict_full({c: 1.0 for c in cols})
    assert isinstance(result, float)
    assert result == pytest.approx(150.0)


def test_train_simple_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_simple import train_and_save
    out = tmp_path / "model_simple.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    model = joblib.load(str(out))
    import pandas as pd
    sample = pd.DataFrame([{
        "lights": 0, "T1": 20.0, "T_out": 28.0,
        "RH_out": 80.0, "Windspeed": 3.0, "Visibility": 10.0, "Tdewpoint": 25.0
    }])
    result = model.predict(sample)
    assert isinstance(float(result[0]), float)


def test_train_forecast_produces_loadable_model(tmp_path):
    import joblib
    from src.model.train_forecast import train_and_save
    out = tmp_path / "model_forecast.joblib"
    train_and_save(output_path=str(out))
    assert out.exists()
    artifact = joblib.load(str(out))
    assert "model" in artifact
    assert "model_type" in artifact
    assert artifact["model_type"] in {
        "Prophet", "XGBoost_lags", "LightGBM_lags", "LSTM", "TFT"
    }
