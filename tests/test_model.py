import pytest


def test_data_loader_returns_train_test_split():
    from src.services.data_loader import load_and_split
    train, test = load_and_split()
    assert len(train) + len(test) == 19735
    assert len(train) == pytest.approx(19735 * 0.8, abs=5)
    assert "rv1" not in train.columns
    assert "rv2" not in train.columns
    assert "date" not in train.columns
    assert "Appliances" in train.columns


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
