from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SplitFrames:
    train: pd.DataFrame
    calibration: pd.DataFrame
    test: pd.DataFrame


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    values = np.zeros(n, dtype=float)
    noise = rng.normal(0.0, sigma, n)
    for i in range(1, n):
        values[i] = phi * values[i - 1] + noise[i]
    return values


def simulate_hourly_market(
    n_days: int = 420,
    start: str = "2024-01-01",
    timezone: str = "UTC",
    seed: int = 20260817,
) -> pd.DataFrame:
    """Create a transparent hourly market benchmark with three temporal regimes.

    Regime labels are retained for evaluation but excluded from model features. Forecast
    columns are noisy issuance-time proxies; realised columns are never used as future
    covariates.
    """

    rng = np.random.default_rng(seed)
    n = n_days * 24
    timestamp = pd.date_range(start=start, periods=n, freq="h", tz=timezone)
    hour = timestamp.hour.to_numpy()
    dow = timestamp.dayofweek.to_numpy()
    doy = timestamp.dayofyear.to_numpy()
    day_id = np.arange(n) // 24

    regime = np.where(day_id < 250, "stable", np.where(day_id < 330, "volatile", "renewable_shift"))
    volatility_mult = np.where(regime == "stable", 1.0, np.where(regime == "volatile", 2.2, 1.5))
    renewable_mult = np.where(regime == "renewable_shift", 1.45, 1.0)

    annual = np.cos(2 * np.pi * (doy - 15) / 365.25)
    daily_temp = 3.0 * np.sin(2 * np.pi * (hour - 14) / 24)
    temperature = 15.0 - 9.0 * annual + daily_temp + _ar1(rng, n, 0.93, 0.8)

    morning_peak = 7.5 * np.exp(-0.5 * ((hour - 8) / 2.4) ** 2)
    evening_peak = 11.0 * np.exp(-0.5 * ((hour - 19) / 2.8) ** 2)
    weekend = np.where(dow >= 5, -5.0, 0.0)
    weather_load = 0.42 * np.abs(temperature - 18.0)
    load_actual = 42.0 + morning_peak + evening_peak + weekend + weather_load + _ar1(rng, n, 0.82, 1.2)
    load_actual = np.clip(load_actual, 24.0, None)

    daylight = np.maximum(0.0, np.sin(np.pi * (hour - 6) / 12))
    solar_season = 0.62 + 0.38 * np.sin(2 * np.pi * (doy - 80) / 365.25)
    cloud = np.clip(0.72 + _ar1(rng, n, 0.78, 0.10), 0.12, 1.0)
    solar_potential = 24.0 * daylight * solar_season * cloud * renewable_mult

    wind_cf = np.clip(0.42 + _ar1(rng, n, 0.96, 0.055), 0.02, 0.95)
    wind_potential = 25.0 * wind_cf * renewable_mult

    availability = np.ones(n)
    outage_starts = rng.choice(np.arange(48, n - 48), size=max(10, n_days // 14), replace=False)
    for start_idx in outage_starts:
        duration = int(rng.integers(3, 15))
        availability[start_idx : start_idx + duration] *= rng.uniform(0.35, 0.78)
    renewable_actual = (solar_potential + wind_potential) * availability

    load_forecast = load_actual + rng.normal(0.0, 1.3 * volatility_mult, n)
    renewable_forecast = solar_potential + wind_potential + rng.normal(0.0, 1.8 * volatility_mult, n)
    renewable_forecast = np.clip(renewable_forecast, 0.0, None)
    temperature_forecast = temperature + rng.normal(0.0, 1.1 * volatility_mult, n)

    net_load = load_actual - renewable_actual
    scarcity = np.maximum(net_load - 47.0, 0.0) ** 1.55
    surplus = np.maximum(renewable_actual - load_actual + 4.0, 0.0)
    price_noise = rng.normal(0.0, 4.5 * volatility_mult, n)
    price = 18.0 + 1.08 * net_load + 0.78 * scarcity - 1.5 * surplus + price_noise
    spike_prob = np.where(regime == "volatile", 0.020, 0.006)
    spikes = rng.random(n) < spike_prob
    price += spikes * rng.gamma(shape=2.0, scale=32.0, size=n)
    price = np.clip(price, -80.0, 420.0)

    observed_price = price.copy()
    missing = rng.random(n) < 0.006
    observed_price[missing] = np.nan

    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "day_id": day_id,
            "regime": regime,
            "price_eur_mwh": price,
            "price_observed_eur_mwh": observed_price,
            "load_actual_mw": load_actual,
            "renewable_actual_mw": renewable_actual,
            "load_forecast_mw": load_forecast,
            "renewable_forecast_mw": renewable_forecast,
            "temperature_actual_c": temperature,
            "temperature_forecast_c": temperature_forecast,
            "availability": availability,
            "data_missing_flag": missing.astype(int),
            "price_spike_flag": spikes.astype(int),
        }
    )


def build_day_ahead_examples(hourly: pd.DataFrame, min_history_days: int = 8) -> pd.DataFrame:
    """Build 24-hour direct forecasts using only information available at daily issuance."""

    hourly = hourly.copy().reset_index(drop=True)
    observed_series = hourly["price_observed_eur_mwh"].ffill()
    required_history = min_history_days * 24
    if observed_series.iloc[:required_history].isna().any():
        raise ValueError(
            "Observed price history begins with missing values; provide an earlier "
            "observation or remove the incomplete leading period. Future values are "
            "not used to backfill history."
        )
    observed = observed_series.to_numpy()
    missing = hourly["data_missing_flag"].to_numpy()
    rows: list[dict[str, float | int | str | pd.Timestamp]] = []

    for issue_day in range(min_history_days, int(hourly["day_id"].max()) + 1):
        issue_pos = issue_day * 24
        if issue_pos + 24 > len(hourly):
            break
        hist24 = observed[issue_pos - 24 : issue_pos]
        hist168 = observed[issue_pos - 168 : issue_pos]
        miss168 = missing[issue_pos - 168 : issue_pos]
        issue_time = hourly.loc[issue_pos, "timestamp"]

        for horizon in range(1, 25):
            target_pos = issue_pos + horizon - 1
            target_time = hourly.loc[target_pos, "timestamp"]
            lag24_pos = target_pos - 24
            lag168_pos = target_pos - 168
            rows.append(
                {
                    "issue_time": issue_time,
                    "target_time": target_time,
                    "issue_day": issue_day,
                    "horizon": horizon,
                    "hour_sin": np.sin(2 * np.pi * target_time.hour / 24),
                    "hour_cos": np.cos(2 * np.pi * target_time.hour / 24),
                    "dow_sin": np.sin(2 * np.pi * target_time.dayofweek / 7),
                    "dow_cos": np.cos(2 * np.pi * target_time.dayofweek / 7),
                    "price_lag24": observed[lag24_pos],
                    "price_lag168": observed[lag168_pos],
                    "last_observed_price": observed[issue_pos - 1],
                    "history_mean24": float(np.mean(hist24)),
                    "history_std24": float(np.std(hist24)),
                    "history_mean168": float(np.mean(hist168)),
                    "history_std168": float(np.std(hist168)),
                    "history_missing_rate168": float(np.mean(miss168)),
                    "load_forecast_mw": hourly.loc[target_pos, "load_forecast_mw"],
                    "renewable_forecast_mw": hourly.loc[target_pos, "renewable_forecast_mw"],
                    "temperature_forecast_c": hourly.loc[target_pos, "temperature_forecast_c"],
                    "price_eur_mwh": hourly.loc[target_pos, "price_eur_mwh"],
                    "regime": hourly.loc[target_pos, "regime"],
                    "availability": hourly.loc[target_pos, "availability"],
                    "price_spike_flag": hourly.loc[target_pos, "price_spike_flag"],
                }
            )
    return pd.DataFrame(rows)


def chronological_split(examples: pd.DataFrame, train_fraction: float, calibration_fraction: float) -> SplitFrames:
    days = np.sort(examples["issue_day"].unique())
    n_train = int(len(days) * train_fraction)
    n_calibration = int(len(days) * calibration_fraction)
    train_days = days[:n_train]
    calibration_days = days[n_train : n_train + n_calibration]
    test_days = days[n_train + n_calibration :]
    if min(len(train_days), len(calibration_days), len(test_days)) == 0:
        raise ValueError("Chronological split produced an empty partition")
    return SplitFrames(
        train=examples[examples["issue_day"].isin(train_days)].reset_index(drop=True),
        calibration=examples[examples["issue_day"].isin(calibration_days)].reset_index(drop=True),
        test=examples[examples["issue_day"].isin(test_days)].reset_index(drop=True),
    )


def dataframe_fingerprint(frame: pd.DataFrame) -> str:
    payload = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    return hashlib.sha256(payload).hexdigest()
