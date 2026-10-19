from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal, ROUND_CEILING
from numbers import Real

import numpy as np
import pandas as pd


def conformity_scores(y: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return np.maximum(lower - y, y - upper)


def finite_sample_quantile(scores: np.ndarray, miscoverage: float) -> float:
    """Return the conformal rank k=ceil((n+1)(1-alpha)), with 1-based k.

    The extra (n+1)st score is +infinity. This is the standard finite-sample
    correction under exchangeable scores; it is not a guarantee under arbitrary
    time dependence. Invalid/nonfinite scores are rejected rather than dropped.
    """

    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or scores.size == 0:
        raise ValueError("A nonempty one-dimensional array of conformity scores is required")
    if not np.isfinite(scores).all():
        raise ValueError("Conformity scores must all be finite")
    if isinstance(miscoverage, (bool, np.bool_)) or not isinstance(miscoverage, Real):
        raise ValueError("miscoverage must be a finite scalar strictly between 0 and 1")
    alpha = float(miscoverage)
    if not np.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("miscoverage must be a finite scalar strictly between 0 and 1")
    # Decimal text semantics prevent .7 at n=9 becoming ceil(3.0000000000000004).
    # Adjacent representable alpha values still remain on their respective sides.
    rank = int((Decimal(scores.size + 1) * (Decimal(1) - Decimal(str(alpha)))).to_integral_value(rounding=ROUND_CEILING))
    if rank > scores.size:
        return float("inf")
    return float(np.partition(scores, rank - 1)[rank - 1])


def static_cqr(
    y_calibration: np.ndarray,
    lower_calibration: np.ndarray,
    upper_calibration: np.ndarray,
    lower_test: np.ndarray,
    upper_test: np.ndarray,
    miscoverage: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    scores = conformity_scores(y_calibration, lower_calibration, upper_calibration)
    qhat = finite_sample_quantile(scores, miscoverage)
    return lower_test - qhat, upper_test + qhat, qhat


def groupwise_static_cqr(
    calibration: pd.DataFrame,
    test: pd.DataFrame,
    lower_col: str,
    upper_col: str,
    target_col: str,
    group_col: str,
    miscoverage: float,
) -> tuple[np.ndarray, np.ndarray, dict[int, float]]:
    """Apply one fixed CQR correction within each forecast group.

    For this portfolio the group is the forecast horizon. This comparator separates
    the effect of horizon-specific calibration from the effect of online adaptation.
    """

    lower_out = np.empty(len(test), dtype=float)
    upper_out = np.empty(len(test), dtype=float)
    qhats: dict[int, float] = {}

    for group_value in sorted(test[group_col].unique()):
        calibration_group = calibration[calibration[group_col] == group_value]
        test_mask = test[group_col].to_numpy() == group_value
        if calibration_group.empty:
            raise ValueError(f"No calibration rows for {group_col}={group_value}")
        scores = conformity_scores(
            calibration_group[target_col].to_numpy(),
            calibration_group[lower_col].to_numpy(),
            calibration_group[upper_col].to_numpy(),
        )
        qhat = finite_sample_quantile(scores, miscoverage)
        lower_out[test_mask] = test.loc[test_mask, lower_col].to_numpy() - qhat
        upper_out[test_mask] = test.loc[test_mask, upper_col].to_numpy() + qhat
        qhats[int(group_value)] = qhat

    return lower_out, upper_out, qhats


def adaptive_cqr(
    calibration: pd.DataFrame,
    test: pd.DataFrame,
    lower_col: str,
    upper_col: str,
    target_col: str,
    horizon_col: str,
    miscoverage: float,
    gamma: float,
    window_per_horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Online, horizon-specific adaptive CQR with no use of future test outcomes.

    The local miscoverage rate uses an ACI-inspired update with clipping to
    [0.01, 0.99], and a trailing score buffer. Clipping changes the usual ACI
    recursion, so its unmodified telescoping guarantees cannot be claimed here.
    In particular, a small buffer can require an infinite conformal bound.
    This empirical wrapper is not a coverage theorem for arbitrary dependent
    time series. Each horizon updates only after its earlier outcome is observed.
    """

    buffers: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=window_per_horizon))
    alpha_t: dict[int, float] = defaultdict(lambda: float(miscoverage))
    for horizon, group in calibration.groupby(horizon_col, sort=True):
        scores = conformity_scores(
            group[target_col].to_numpy(),
            group[lower_col].to_numpy(),
            group[upper_col].to_numpy(),
        )
        for score in scores[-window_per_horizon:]:
            buffers[int(horizon)].append(float(score))

    lower_out = np.empty(len(test))
    upper_out = np.empty(len(test))
    alpha_path = np.empty(len(test))
    qhat_path = np.empty(len(test))

    order = np.argsort(pd.to_datetime(test["target_time"]).to_numpy())
    for position in order:
        row = test.iloc[position]
        horizon = int(row[horizon_col])
        if not buffers[horizon]:
            raise ValueError(f"No calibration scores for horizon {horizon}")
        local_alpha = float(np.clip(alpha_t[horizon], 0.01, 0.99))
        qhat = finite_sample_quantile(np.asarray(buffers[horizon]), local_alpha)
        low = float(row[lower_col] - qhat)
        high = float(row[upper_col] + qhat)
        lower_out[position] = low
        upper_out[position] = high
        alpha_path[position] = local_alpha
        qhat_path[position] = qhat

        y = float(row[target_col])
        error = float(not (low <= y <= high))
        alpha_t[horizon] = float(np.clip(local_alpha + gamma * (miscoverage - error), 0.01, 0.99))
        score = float(max(row[lower_col] - y, y - row[upper_col]))
        buffers[horizon].append(score)

    return lower_out, upper_out, alpha_path, qhat_path
