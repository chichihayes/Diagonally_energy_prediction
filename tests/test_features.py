def test_build_simple_matrix_returns_7_columns():
    from src.services.data_loader import load_and_split
    from src.services.features import build_simple_matrix
    train, _ = load_and_split()
    X, y = build_simple_matrix(train)
    assert list(X.columns) == ["lights", "T1", "T_out", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
    assert y.name == "Appliances"
    assert len(X) == len(y)
