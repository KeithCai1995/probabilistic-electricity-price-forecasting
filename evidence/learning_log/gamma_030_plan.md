\# Planned gamma 0.030 experiment



\## Run plan



\- Date: 26 September 2026

\- Baseline configuration: configs/base.yaml

\- New configuration: configs/gamma\_030.yaml

\- Parameter changed: adaptive\_gamma from 0.015 to 0.030

\- Data status: simulated benchmark, not employer or field data



\## Reason for the change



The supplied gamma 0.050 experiment produced coverage closer to the 80% target and a narrower interval than the gamma 0.015 baseline. However, its interval score was slightly worse.



I chose to test gamma 0.030 because it is between the baseline and the more reactive gamma 0.050 setting. I want to see whether an intermediate update rate can retain some of the improvement in coverage and interval width without increasing the interval score as much.



\## Expected result



I expect the Adaptive CQR coverage and mean width to fall somewhere between the results for gamma 0.015 and gamma 0.050. The interval score may also fall between them, but this is only a hypothesis and the actual result may be different.



The raw quantile and static CQR results should remain unchanged because adaptive\_gamma only affects Adaptive CQR.



\## Evaluation



I will compare:



1\. the distance between Adaptive CQR coverage and the 0.80 target;

2\. mean interval width, where a smaller value is preferable if coverage remains adequate;

3\. interval score, where a lower value is better;

4\. whether the non-adaptive methods remain unchanged.

