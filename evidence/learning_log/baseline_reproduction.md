\# Baseline reproduction



\## Run information



\- Date: 25 September 2026

\- Repository: P1\_WORKING\_REPOSITORY

\- Python: 3.13.15

\- Configuration: configs/base.yaml

\- Exit code: 0

\- Unit tests before the run: 6/6 passed

\- Data status: simulated benchmark, not employer or field data



\## Command



`python scripts/run\_experiment.py --config configs/base.yaml --output-root evidence/runs/baseline`



\## Environment comparison



\- Supplied reference environment: Python 3.12.14

\- My local environment: Python 3.13.15 on Windows

\- Reference data fingerprint: 6bacc0ff00f87704fae89a6d82506daf9acbca9ef67ba4897ae611122df3bd70

\- Local data fingerprint: 6d446b5560d6427574969caeb1b861aaebca30923fefa6093931b7700907e495



\## Data comparison



\- Same shape: yes

\- Maximum absolute numeric difference: 2.842170943040401e-14

\- Numeric data equal after rounding to 10 decimal places: yes

\- Non-numeric columns equal: yes

\- Conclusion: the local simulated data match the reference data to 10 decimal places, but they are not byte-identical



\## Local results



| Method | Coverage | Mean width | Interval score |

| --- | ---: | ---: | ---: |

| Raw quantiles | 0.556225 | 11.896091 | 34.007247 |

| Static CQR (pooled) | 0.924197 | 27.600691 | 32.188923 |

| Static CQR (by horizon) | 0.927711 | 29.282753 | 33.657756 |

| Adaptive CQR | 0.826305 | 22.362592 | 30.906253 |



\- Seasonal-naive MAE: 11.268044

\- Quantile-model MAE: 6.299118



\## My interpretation



The raw quantile interval covered only 55.6% of the observations, which was well below the 80% target. This means that the uncalibrated interval was too narrow and underestimated the uncertainty during the evaluation period.



Static CQR used the calibration errors to adjust and widen the prediction intervals. This increased the coverage to about 92%, but it also produced wider and less precise intervals. In this run, the higher coverage therefore came with a trade-off: the intervals were more reliable but less sharp.



Adaptive CQR achieved 82.6% coverage, which was close to the 80% target. Its mean interval width was smaller than those of both static CQR methods, and it also achieved the lowest interval score in this run. This suggests that adaptive calibration provided a better balance between coverage and interval width on this simulated benchmark. However, one simulated experiment cannot prove that adaptive CQR is always better, or that it would produce the same results with real electricity-market data.



\## Reproduction conclusion



I successfully ran the baseline experiment on Windows with Python 3.13.15 after all six unit tests had passed. My results were close to the supplied reference results and supported the same main conclusions. The simulated data were equal after rounding the numeric values to 10 decimal places, but very small cross-platform floating-point differences changed the exact fingerprint and some output values. I therefore describe this as a successful cross-platform reproduction, rather than a byte-identical reproduction.

