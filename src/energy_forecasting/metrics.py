from __future__ import annotations

import numpy as np
import pandas as pd


def pinball_loss(y: np.ndarray, prediction: np.ndarray, quantile: float) -> float:
    error = y - prediction
    return float(np.mean(np.maximum(quantile * error, (quantile - 1.0) * error)))


def interval_metrics(y: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float) -> dict[str, float]:
    coverage = np.mean((y >= lower) & (y <= upper))
    width = np.mean(upper - lower)
    # Mask before multiplying so valid infinite conformal intervals score +inf,
    # rather than producing NaN from the otherwise inactive infinity * 0 term.
    lower_penalty = np.where(y < lower, lower - y, 0.0)
    upper_penalty = np.where(y > upper, y - upper, 0.0)
    interval_score = (upper - lower) + (2.0 / alpha) * (lower_penalty + upper_penalty)
    finite_mask = np.isfinite(lower) & np.isfinite(upper)
    return {
        "coverage": float(coverage),
        "mean_width": float(width),
        "interval_score": float(np.mean(interval_score)),
        "unbounded_fraction": float(np.mean(~finite_mask)),
        "finite_only_mean_width": float(np.mean((upper - lower)[finite_mask])) if finite_mask.any() else float("nan"),
        "finite_only_interval_score": float(np.mean(interval_score[finite_mask])) if finite_mask.any() else float("nan"),
    }


def approximate_crps(y: np.ndarray, predictions: pd.DataFrame, quantiles: list[float]) -> float:
    losses = []
    for q in quantiles:
        column = f"q{int(round(q * 100)):02d}"
        error = y - predictions[column].to_numpy()
        losses.append(np.maximum(q * error, (q - 1.0) * error))
    loss_grid = np.column_stack(losses)
    return float(2.0 * np.mean(np.trapezoid(loss_grid, x=np.asarray(quantiles), axis=1)))


def rolling_coverage(y: pd.Series, lower: pd.Series, upper: pd.Series, window: int) -> pd.Series:
    hit = ((y >= lower) & (y <= upper)).astype(float)
    return hit.rolling(window=window, min_periods=min(window, max(24, window // 4))).mean()

