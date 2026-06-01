def test_assemble_simple_features_returns_correct_keys():
    from src.services.features import assemble_simple_features
    weather = {"T_out": 28.4, "RH_out": 82.0, "Windspeed": 3.1, "Visibility": 10.0, "Tdewpoint": 25.1}
    result = assemble_simple_features(lights=0, T1=19.89, weather=weather)
    assert list(result.keys()) == ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
    assert result["lights"] == 0
    assert result["T1"] == 19.89
    assert result["T_out"] == 28.4


def test_assemble_simple_features_preserves_weather_values():
    from src.services.features import assemble_simple_features
    weather = {"T_out": 30.0, "RH_out": 70.0, "Windspeed": 5.0, "Visibility": 8.0, "Tdewpoint": 22.0}
    result = assemble_simple_features(lights=100, T1=22.5, weather=weather)
    assert result["Windspeed"] == 5.0
    assert result["Visibility"] == 8.0


def test_build_simple_matrix_returns_7_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_simple_matrix
    train, _ = load_and_split()
    X, y = build_simple_matrix(train)
    assert list(X.columns) == ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
    assert y.name == "Appliances"
    assert len(X) == len(y)
