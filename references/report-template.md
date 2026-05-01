# PaperSOTA report template

# [Dataset Name] PaperSOTA Report

## 1. Dataset

- Dataset name:
- Aliases:
- Domain / task:
- Official homepage:
- Introducing paper:
- Verification notes:

## 2. Metrics

Briefly explain each metric used by this dataset. Preserve metric direction arrows.

Example:

- KLD↓: measures the divergence between predicted and ground-truth distributions; lower is better.
- SIM↑: measures pixel-wise map similarity; higher is better.
- NSS↑: measures normalized scanpath saliency consistency with ground truth; higher is better.

## 3. Benchmark / Algorithm Comparison

Use one table per comparable protocol. Split tables when methods use different dataset splits, annotation regimes, one-shot/few-shot settings, extra training data, or different evaluation protocols.

| Paper | Metric 1 | Metric 2 | Metric 3 | Notes |
|---|---:|---:|---:|---|
| ShortTitle, VenueYear [1] | 1.234 | 0.456 | — | metric not found in accessible text |
| MethodName, VenueYear [2] | **0.890** | **0.510** | **1.547** | best comparable result |

Bold the best value in each metric column. For `↓`, lower is better. For `↑`, higher is better.

## 4. References

[1] Author A, Author B. **Paper Title**. Venue, Year. URL.

[2] Author C et al. **Paper Title**. Venue, Year. URL.

## 5. Notes and limitations

- List inaccessible PDFs/HTML pages.
- List possible false positives.
- List protocol differences that prevent direct comparison.
- List metrics that were unavailable or extracted with low confidence.
