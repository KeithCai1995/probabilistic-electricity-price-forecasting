# Related work and contribution boundary

This note positions the portfolio against representative primary research. It is an
application-level literature map, not a systematic review and not proof that no similar
work exists.

## Closest strands

| Strand | Representative work | Consequence for this portfolio |
|---|---|---|
| Conformalized quantile regression | Romano, Patterson and Candes (2019) | CQR is established; the static wrapper is an implementation baseline, not an invention. |
| Online adaptation under shift | Gibbs and Candes (2021) | Adaptive updates under changing distributions are established; this project uses an ACI-style training benchmark. |
| Adaptive conformal prediction for dependent time series | Zaffran et al. (2022); Xu and Xie (2023) | Ordinary exchangeable split-conformal guarantees do not automatically apply to time series. Zaffran et al. also include a real day-ahead electricity-price case study, so adaptive conformal electricity-price forecasting is established prior work. |
| Multistep and joint reliability | Schlembach et al. (2025) | Marginal hourly coverage is not sufficient evidence of reliable 24-hour paths. |
| Probabilistic volatile-price forecasting | Cornell, Dinh and Pourmousavi (2024) | Electricity-price uncertainty and spikes already have specialised probabilistic methods. |
| Conformal electricity-price forecasting and storage trading | O'Connor et al. (2025) | This portfolio cannot claim the first use of conformal prediction for electricity prices or the first link between conformal intervals and simulated battery trading. |

## Narrow contribution

The portfolio contributes a compact and reproducible research-training benchmark that:

- uses chronological train, calibration and evaluation blocks;
- restricts features to information available at issue time;
- compares raw, static and adaptive intervals under a controlled regime shift;
- reports rolling, extreme-price and feature-distance OOD failures; and
- exposes all data generation, configuration, tests, tables and figures.

The portfolio does **not** claim a new conformal algorithm, a new electricity-price
forecasting architecture, the first adaptive conformal electricity-price application,
the first link to battery trading, general conditional coverage, reliable joint 24-hour
paths, real-market external validity or deployment readiness.

## References

1. Romano, Y., Patterson, E. and Candes, E. (2019). Conformalized Quantile Regression. NeurIPS 32. https://proceedings.neurips.cc/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html
2. Gibbs, I. and Candes, E. (2021). Adaptive Conformal Inference Under Distribution Shift. NeurIPS 34. https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html
3. Zaffran, M., Feron, O., Goude, Y., Josse, J. and Dieuleveut, A. (2022). Adaptive Conformal Predictions for Time Series. ICML 39. https://proceedings.mlr.press/v162/zaffran22a.html
4. Xu, C. and Xie, Y. (2023). Sequential Predictive Conformal Inference for Time Series. ICML 40. https://proceedings.mlr.press/v202/xu23r.html
5. Schlembach, F., Smirnov, E., Koprinska, I. and Winands, M. H. M. (2025). Conformal multistep-ahead multivariate time-series forecasting. Machine Learning, 114, 165. https://doi.org/10.1007/s10994-024-06722-9
6. Cornell, C., Dinh, N. T. and Pourmousavi, S. A. (2024). A probabilistic forecast methodology for volatile electricity prices in the Australian National Electricity Market. International Journal of Forecasting, 40(4), 1421-1437. https://www.sciencedirect.com/science/article/pii/S0169207023001358
7. O'Connor, C., Bahloul, M., Rossi, R., Prestwich, S. and Visentin, A. (2025). Conformal Prediction for electricity price forecasting in the day-ahead and real-time balancing market. Energy and AI, 21, 100571. https://www.sciencedirect.com/science/article/pii/S266654682500103X
