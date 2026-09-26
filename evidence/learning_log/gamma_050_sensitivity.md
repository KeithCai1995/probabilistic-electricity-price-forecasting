\# Supplied gamma sensitivity experiment



\## Run information



\- Date: 25 September 2026

\- Python: 3.13.15

\- Data status: simulated benchmark, not employer or field data

\- Baseline configuration: configs/base.yaml

\- Sensitivity configuration: configs/gamma\_sensitivity.yaml

\- Parameter change: adaptive\_gamma from 0.015 to 0.050

\- Exit code: 0



\## Purpose



This experiment examined how a larger adaptive gamma affected the Adaptive CQR results. All other settings, including the random seed, data, model and evaluation procedure, remained unchanged.



\## Results



| Adaptive CQR metric | Gamma 0.015 | Gamma 0.050 |

| --- | ---: | ---: |

| Coverage | 0.826305 | 0.804217 |

| Mean width | 22.362592 | 21.348917 |

| Interval score | 30.906253 | 31.116844 |



The target coverage was 0.80.



\## My interpretation



Increasing gamma from 0.015 to 0.050 made the adaptive calibration react more quickly. Coverage moved closer to the 80% target, and the average interval became narrower. However, the interval score became slightly worse.



I therefore do not regard gamma 0.050 as better in every respect. It gave a narrower interval and coverage closer to the target, but some missed observations may have received larger penalties. This result shows why coverage alone is not enough when comparing probabilistic forecasts.



The raw quantile and static CQR results did not change, which was expected because adaptive\_gamma only controls the adaptive calibration method.



\## Limitations



This comparison used one simulated dataset and one random seed. It does not show that gamma 0.050 would perform better on real electricity-market data or under every type of regime change.

