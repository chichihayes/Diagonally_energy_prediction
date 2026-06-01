import joblib
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

from src.services.data_loader import load_and_split
from src.services.features import build_full_matrix
from src.model.evaluate import select_best_by_r2


def train_and_save(output_path: str = "src/model/trained/model_full.joblib") -> None:
    train_df, test_df = load_and_split()
    X_train, y_train = build_full_matrix(train_df)
    X_test, y_test = build_full_matrix(test_df)

    models = [
        ("RandomForest", RandomForestRegressor(n_jobs=-1, random_state=42)),
        ("XGBoost", XGBRegressor(n_jobs=-1, random_state=42, verbosity=0)),
        ("LightGBM", LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1)),
        ("CatBoost", CatBoostRegressor(verbose=0, random_state=42)),
        ("ExtraTrees", ExtraTreesRegressor(n_jobs=-1, random_state=42)),
        ("Ridge", Ridge()),
    ]

    candidates = []
    for name, model in models:
        model.fit(X_train, y_train)
        score = r2_score(y_test, model.predict(X_test))
        candidates.append((name, model, score))

    winner_name, winner_model, winner_score = select_best_by_r2(candidates)
    print(f"Best model: {winner_name}  R²={winner_score:.4f}")
    joblib.dump(winner_model, output_path)
    return {name: score for name, _, score in candidates}
