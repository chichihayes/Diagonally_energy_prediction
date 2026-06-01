import logging

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.utils.data
from lightgbm import LGBMRegressor
from prophet import Prophet
from xgboost import XGBRegressor

from src.model.evaluate import select_best_by_mape
from src.services.data_loader import load_and_split
from src.services.features import build_lag_matrix

logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

_CSV_PATH = "data/raw/KAG_energydata_complete.csv"
_HORIZON = 24


# ---------------------------------------------------------------------------
# PyTorch network definitions (module-level so joblib can unpickle them)
# ---------------------------------------------------------------------------

class _LSTMNet(nn.Module):
    def __init__(self, hidden_size: int, horizon: int):
        super().__init__()
        self.lstm = nn.LSTM(1, hidden_size, num_layers=2, batch_first=True, dropout=0.1)
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


class _TFTNet(nn.Module):
    """Simplified TFT: LSTM encoder + single-layer Transformer attention + linear head."""

    def __init__(self, hidden_size: int, horizon: int, n_heads: int = 4):
        super().__init__()
        self.lstm = nn.LSTM(1, hidden_size, num_layers=1, batch_first=True)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=n_heads,
            dim_feedforward=hidden_size * 2,
            dropout=0.1,
            batch_first=True,
            norm_first=True,
        )
        self.attn = nn.TransformerEncoder(enc_layer, num_layers=1)
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.attn(out)
        return self.fc(out[:, -1, :])


class _NeuralForecaster:
    """Joblib-serializable wrapper that trains a PyTorch net on a 1-D time series."""

    def __init__(self, net: nn.Module, input_size: int, horizon: int, max_steps: int):
        self.net = net
        self.input_size = input_size
        self.horizon = horizon
        self.max_steps = max_steps
        self._mean = 0.0
        self._std = 1.0
        self._residual_std = 1.0

    def fit(self, series: np.ndarray) -> None:
        self._mean = float(series.mean())
        self._std = float(series.std()) + 1e-8
        s = (series - self._mean) / self._std

        X, y = [], []
        for i in range(len(s) - self.input_size - self.horizon + 1):
            X.append(s[i:i + self.input_size])
            y.append(s[i + self.input_size:i + self.input_size + self.horizon])
        if not X:
            return

        X_t = torch.tensor(np.array(X, dtype=np.float32)).unsqueeze(-1)
        y_t = torch.tensor(np.array(y, dtype=np.float32))

        loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_t, y_t),
            batch_size=32, shuffle=True,
        )
        opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        loss_fn = nn.MSELoss()

        self.net.train()
        step = 0
        while step < self.max_steps:
            for xb, yb in loader:
                if step >= self.max_steps:
                    break
                opt.zero_grad()
                loss_fn(self.net(xb), yb).backward()
                opt.step()
                step += 1

        self.net.eval()
        with torch.no_grad():
            residuals = (y_t.numpy() - self.net(X_t).numpy()) * self._std
        self._residual_std = float(np.std(residuals)) + 1e-8

    def predict_from_series(
        self, series: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        s = (series[-self.input_size:] - self._mean) / self._std
        x = torch.tensor(s.astype(np.float32)).unsqueeze(0).unsqueeze(-1)
        self.net.eval()
        with torch.no_grad():
            pred = self.net(x).numpy()[0]
        yhat = pred * self._std + self._mean
        margin = 1.96 * self._residual_std
        return yhat, yhat - margin, yhat + margin


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_hourly_series() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(_CSV_PATH, parse_dates=["date"])
    hourly = df.set_index("date")[["Appliances"]].resample("h").mean()
    split = int(len(hourly) * 0.8)
    return hourly.iloc[:split], hourly.iloc[split:]


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return float("inf")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


# ---------------------------------------------------------------------------
# Model trainers
# ---------------------------------------------------------------------------

def _train_prophet(train_h: pd.DataFrame, test_h: pd.DataFrame):
    df_train = train_h.reset_index().rename(columns={"date": "ds", "Appliances": "y"})
    m = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,
        uncertainty_samples=100,
    )
    m.fit(df_train)
    future_dates = pd.date_range(
        start=train_h.index[-1] + pd.Timedelta(hours=1),
        periods=_HORIZON,
        freq="h",
    )
    forecast = m.predict(pd.DataFrame({"ds": future_dates}))
    y_true = test_h["Appliances"].values[:_HORIZON]
    return m, _mape(y_true, forecast["yhat"].values)


def _train_xgb_lags(train_df: pd.DataFrame, test_df: pd.DataFrame):
    X_train, y_train = build_lag_matrix(train_df)
    X_test, y_test = build_lag_matrix(test_df)
    model = XGBRegressor(n_jobs=-1, random_state=42, verbosity=0)
    model.fit(X_train, y_train)
    return model, _mape(y_test.values, model.predict(X_test))


def _train_lgbm_lags(train_df: pd.DataFrame, test_df: pd.DataFrame):
    X_train, y_train = build_lag_matrix(train_df)
    X_test, y_test = build_lag_matrix(test_df)
    model = LGBMRegressor(n_jobs=-1, random_state=42, verbose=-1)
    model.fit(X_train, y_train)
    return model, _mape(y_test.values, model.predict(X_test))


def _train_lstm(train_h: pd.DataFrame, test_h: pd.DataFrame):
    torch.manual_seed(42)
    forecaster = _NeuralForecaster(
        net=_LSTMNet(hidden_size=64, horizon=_HORIZON),
        input_size=2 * _HORIZON,
        horizon=_HORIZON,
        max_steps=50,
    )
    train_series = train_h["Appliances"].values
    forecaster.fit(train_series)
    yhat, _, _ = forecaster.predict_from_series(train_series)
    y_true = test_h["Appliances"].values[:_HORIZON]
    return forecaster, _mape(y_true, yhat)


def _train_tft(train_h: pd.DataFrame, test_h: pd.DataFrame):
    torch.manual_seed(42)
    forecaster = _NeuralForecaster(
        net=_TFTNet(hidden_size=64, horizon=_HORIZON),
        input_size=2 * _HORIZON,
        horizon=_HORIZON,
        max_steps=50,
    )
    train_series = train_h["Appliances"].values
    forecaster.fit(train_series)
    yhat, _, _ = forecaster.predict_from_series(train_series)
    y_true = test_h["Appliances"].values[:_HORIZON]
    return forecaster, _mape(y_true, yhat)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def train_and_save(output_path: str = "src/model/trained/model_forecast.joblib") -> None:
    train_df, test_df = load_and_split()
    train_h, test_h = _load_hourly_series()

    prophet_model, prophet_mape = _train_prophet(train_h, test_h)
    xgb_model, xgb_mape = _train_xgb_lags(train_df, test_df)
    lgbm_model, lgbm_mape = _train_lgbm_lags(train_df, test_df)
    lstm_model, lstm_mape = _train_lstm(train_h, test_h)
    tft_model, tft_mape = _train_tft(train_h, test_h)

    candidates = [
        ("Prophet", prophet_model, prophet_mape),
        ("XGBoost_lags", xgb_model, xgb_mape),
        ("LightGBM_lags", lgbm_model, lgbm_mape),
        ("LSTM", lstm_model, lstm_mape),
        ("TFT", tft_model, tft_mape),
    ]

    best_name, best_model, best_mape = select_best_by_mape(candidates)
    print(f"Best model: {best_name}  MAPE={best_mape:.2f}%")
    joblib.dump({"model": best_model, "model_type": best_name}, output_path)
