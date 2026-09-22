from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


FEATURE_COLUMNS = [
    "horizon",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "price_lag24",
    "price_lag168",
    "last_observed_price",
    "history_mean24",
    "history_std24",
    "history_mean168",
    "history_std168",
    "history_missing_rate168",
    "load_forecast_mw",
    "renewable_forecast_mw",
    "temperature_forecast_c",
]


@dataclass
class QuantileEnsemble:
    quantiles: list[float]
    backend: str = "sklearn"
    params: dict = field(default_factory=dict)
    seed: int = 20260817

    def __post_init__(self) -> None:
        self.models: dict[float, object] = {}
        if self.backend not in {"sklearn", "lightgbm"}:
            raise ValueError("backend must be 'sklearn' or 'lightgbm'")

    def _new_model(self, quantile: float):
        if self.backend == "lightgbm":
            try:
                from lightgbm import LGBMRegressor
            except ImportError as exc:
                raise ImportError("Install requirements-optional.txt to use LightGBM") from exc
            return LGBMRegressor(
                objective="quantile",
                alpha=quantile,
                n_estimators=self.params.get("max_iter", 200),
                learning_rate=self.params.get("learning_rate", 0.05),
                num_leaves=self.params.get("max_leaf_nodes", 31),
                min_child_samples=self.params.get("min_samples_leaf", 20),
                reg_lambda=self.params.get("l2_regularization", 0.1),
                random_state=self.seed,
                verbosity=-1,
            )
        return HistGradientBoostingRegressor(
            loss="quantile",
            quantile=quantile,
            max_iter=self.params.get("max_iter", 150),
            learning_rate=self.params.get("learning_rate", 0.06),
            max_leaf_nodes=self.params.get("max_leaf_nodes", 31),
            min_samples_leaf=self.params.get("min_samples_leaf", 20),
            l2_regularization=self.params.get("l2_regularization", 0.1),
            random_state=self.seed,
        )

    def fit(self, frame: pd.DataFrame, target: str = "price_eur_mwh") -> "QuantileEnsemble":
        x = frame[FEATURE_COLUMNS]
        y = frame[target]
        for q in self.quantiles:
            model = self._new_model(q)
            model.fit(x, y)
            self.models[q] = model
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not self.models:
            raise RuntimeError("Model has not been fitted")
        raw = np.column_stack([self.models[q].predict(frame[FEATURE_COLUMNS]) for q in self.quantiles])
        rearranged = np.sort(raw, axis=1)
        return pd.DataFrame(
            rearranged,
            columns=[quantile_column(q) for q in self.quantiles],
            index=frame.index,
        )


def quantile_column(q: float) -> str:
    return f"q{int(round(q * 100)):02d}"


def ood_score(train: pd.DataFrame, candidate: pd.DataFrame) -> tuple[np.ndarray, float]:
    mean = train[FEATURE_COLUMNS].mean(axis=0)
    std = train[FEATURE_COLUMNS].std(axis=0).replace(0.0, 1.0)
    train_score = np.sqrt(np.mean(((train[FEATURE_COLUMNS] - mean) / std) ** 2, axis=1))
    candidate_score = np.sqrt(np.mean(((candidate[FEATURE_COLUMNS] - mean) / std) ** 2, axis=1))
    threshold = float(np.quantile(train_score, 0.95))
    return candidate_score.to_numpy(), threshold

