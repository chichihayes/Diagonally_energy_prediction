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


def test_build_full_matrix_returns_25_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_full_matrix
    train, _ = load_and_split()
    X, y = build_full_matrix(train)
    expected_cols = [
        "lights", "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    assert list(X.columns) == expected_cols
    assert y.name == "Appliances"
    assert len(X) == len(y)


def test_build_full_matrix_excludes_rv_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_full_matrix
    train, _ = load_and_split()
    X, _ = build_full_matrix(train)
    assert "rv1" not in X.columns
    assert "rv2" not in X.columns


def test_assemble_full_features_returns_25_keys_in_order():
    from src.services.features import assemble_full_features
    sensors = {
        "T1": 19.89, "RH_1": 47.6,
        "T2": 19.2,  "RH_2": 44.79,
        "T3": 19.79, "RH_3": 44.73,
        "T4": 17.17, "RH_4": 41.67,
        "T5": 17.2,  "RH_5": 55.2,
        "T6": 7.03,  "RH_6": 84.26,
        "T7": 17.2,  "RH_7": 41.63,
        "T8": 18.2,  "RH_8": 48.9,
        "T9": 17.03, "RH_9": 45.53,
    }
    weather = {
        "T_out": 28.4, "Press_mm_hg": 1012.0,
        "RH_out": 82.0, "Windspeed": 3.1,
        "Visibility": 10.0, "Tdewpoint": 25.1,
    }
    result = assemble_full_features(lights=0, sensors=sensors, weather=weather)
    expected_keys = [
        "lights",
        "T1", "RH_1", "T2", "RH_2", "T3", "RH_3", "T4", "RH_4",
        "T5", "RH_5", "T6", "RH_6", "T7", "RH_7", "T8", "RH_8", "T9", "RH_9",
        "T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint",
    ]
    assert list(result.keys()) == expected_keys
    assert len(result) == 25
    assert result["lights"] == 0
    assert result["T1"] == 19.89
    assert result["T_out"] == 28.4
    assert result["Press_mm_hg"] == 1012.0


def test_assemble_full_features_preserves_all_sensor_values():
    from src.services.features import assemble_full_features
    sensors = {f"T{i}": float(i) for i in range(1, 10)}
    sensors.update({f"RH_{i}": float(i * 10) for i in range(1, 10)})
    weather = {
        "T_out": 30.0, "Press_mm_hg": 1010.0,
        "RH_out": 75.0, "Windspeed": 4.0,
        "Visibility": 12.0, "Tdewpoint": 22.0,
    }
    result = assemble_full_features(lights=50, sensors=sensors, weather=weather)
    assert result["T3"] == 3.0
    assert result["RH_7"] == 70.0
    assert result["Windspeed"] == 4.0
    assert result["lights"] == 50
