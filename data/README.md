# Data schema and real-data extension

The default experiment creates a simulated hourly market table. This makes the complete
pipeline reproducible without credentials and prevents accidental disclosure of employer
data.

Within the simulator, the load, renewable and temperature forecast proxies are generated
by perturbing the corresponding simulated realised series with noise. They are treated as
available at issue time in this controlled benchmark, but may be more informative than
operational forecasts. A real-data extension must use values and publication timestamps
that were genuinely available when each forecast would have been issued.

For a real-data extension, create one hourly table with the following columns:

| Column | Meaning | Availability rule |
|---|---|---|
| timestamp | timezone-aware target time | known |
| price_eur_mwh | realised target price | target only |
| load_actual_mw | realised load | target only |
| renewable_actual_mw | realised wind/solar | target only |
| load_forecast_mw | forecast available at issuance | known at issue time |
| renewable_forecast_mw | forecast available at issuance | known at issue time |
| temperature_forecast_c | forecast available at issuance | known at issue time |

Recommended public sources:

- ENTSO-E Transparency Platform: generation, load and day-ahead price exports.
- Elexon Insights API: public GB demand, generation and price endpoints.
- Open Power System Data time-series package: harmonised hourly European load, renewable
  generation and prices.

The adapter must preserve publication timestamps. Do not use revised actual values as
features if they would not have been available when the forecast was issued.
