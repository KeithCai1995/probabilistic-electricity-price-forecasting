# Gamma 0.030 experiment results

## Run information

- Date: 26 September 2026
- Configuration: configs/gamma_030.yaml
- Parameter tested: adaptive_gamma = 0.030
- Exit code: 0
- Data status: simulated benchmark, not employer or field data

## Results

| Adaptive gamma | Coverage | Mean width | Interval score |
| ---: | ---: | ---: | ---: |
| 0.015 | 0.826305 | 22.362592 | 30.906253 |
| 0.030 | 0.811245 | 21.671771 | 30.906484 |
| 0.050 | 0.804217 | 21.348917 | 31.116844 |

The target coverage was 0.80.

## Comparison with my experiment plan

The results followed the pattern I expected before the run. The coverage and mean width for gamma 0.030 fell between the results for gamma 0.015 and gamma 0.050. Its interval score also fell between the other two values, although it was almost identical to the baseline score.

Compared with gamma 0.015, gamma 0.030 moved coverage closer to the 80% target and reduced the mean interval width by about 3.1%. The interval score increased by only about 0.00023.

## My interpretation

Gamma 0.030 gave a useful compromise in this experiment. It produced narrower intervals and coverage closer to the target than gamma 0.015, while avoiding most of the interval-score increase seen with gamma 0.050.

This does not mean that gamma 0.030 is universally optimal. Gamma 0.050 was still closer to the coverage target and produced the narrowest intervals, while gamma 0.015 had the lowest interval score by a very small margin. The preferred value therefore depends on which evaluation criterion matters most.

The raw quantile and static CQR results remained unchanged across the runs. This supports the conclusion that the observed differences came from the adaptive-gamma setting rather than a change to the data or forecasting model.

## Limitations

This was a small sensitivity analysis using one simulated dataset and one random seed. The results do not establish the best gamma for real electricity-market data. A stronger study would test more gamma values, multiple seeds, different regime shifts and genuine market datasets.
