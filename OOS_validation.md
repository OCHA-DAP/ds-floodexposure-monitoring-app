# Task: Binary Temporal Segmentation Quality Assessment

## Problem Statement

Given a continuous time series $y(x) \in [0,1]$ representing daily probabilities 
for $x \in \{1, 2, \ldots, 365\}$, we apply a segmentation algorithm that produces a 
binary output $s(x) \in \{0,1\}$ through:

1. **Smoothing**: $\bar{y}(x) = \text{mean}(y[x-w : x+w])$
2. **Thresholding**: $s(x) = \begin{cases} 1 & \text{if } \bar{y}(x) > \theta \\ 0 & \text{otherwise} \end{cases}$
3. **Run Length Filtering**: Runs with length $< L_{\min}$ are rejected (set to 0)

where:
- $\theta$ is the probability threshold
- $w$ is the window size (in days)
- $L_{\min}$ is the minimum run length (default: 15 or 30 days)

The algorithm generates **runs** (contiguous sequences of 1s), representing 
Out-of-Season (OOS) periods. Different parameter combinations $(\theta, w)$ produce 
different segmentations with varying:
- Number of runs ($k$)
- Run lengths and internal homogeneity
- Temporal gaps between runs

## Objective: Model Selection Framework

This is a **model selection problem**: each configuration $(\theta, w)$ defines a 
distinct segmentation model $M_{\theta,w}$.

**Goal**: Select the model that optimally balances:

1. **Internal Cohesion**: Days within each OOS run should have similar (high) probability values
2. **Model Parsimony**: Avoid over-segmentation (too many short runs)
3. **Structural Validity**: Each run must span at least $L_{\min}$ consecutive days

We seek a segmentation that captures genuine OOS periods with stable high probabilities,
while avoiding fragmented or spurious detections that would result from over-fitting.


```python
import utils.oos_detection as oos_detection
from dotenv import load_dotenv

load_dotenv()

# # ==================== PARAMETER GRID ====================
# oos_detection.PERCENTAGE_GRID = [95, 96, 97, 98, 99]
# oos_detection.WINDOW_DAYS_GRID = [10, 15, 20, 25, 30]
# oos_detection.ADM_LEVEL_GRID = [0, 1, 2]
# oos_detection.MIN_OOS_RUN_LENGTH_GRID = [15, 30]
# # =======================================================

oos_detection.run_parameter_grid_search(
    container="dev",
    rolling_sum_days=5,
    output_dir="grid_search_results",
    max_workers=4
)
```

    Total combinations: 150
    

    Grid Search:   7%|▋         | 10/150 [00:00<00:01, 99.67it/s]

    Skipping existing: adm0_length15_pct95_win10.parquet
    Skipping existing: adm0_length15_pct95_win15.parquet
    Skipping existing: adm0_length15_pct95_win20.parquet
    Skipping existing: adm0_length15_pct95_win25.parquet
    Skipping existing: adm0_length15_pct95_win30.parquet
    Skipping existing: adm0_length15_pct96_win10.parquet
    Skipping existing: adm0_length15_pct96_win15.parquet
    Skipping existing: adm0_length15_pct96_win20.parquet
    Skipping existing: adm0_length15_pct96_win25.parquet
    Skipping existing: adm0_length15_pct96_win30.parquet
    Skipping existing: adm0_length15_pct97_win10.parquet
    Skipping existing: adm0_length15_pct97_win15.parquet
    Skipping existing: adm0_length15_pct97_win20.parquet
    Skipping existing: adm0_length15_pct97_win25.parquet
    Skipping existing: adm0_length15_pct97_win30.parquet
    Skipping existing: adm0_length15_pct98_win10.parquet
    Skipping existing: adm0_length15_pct98_win15.parquet
    Skipping existing: adm0_length15_pct98_win20.parquet
    

                                                                 

    Skipping existing: adm0_length15_pct98_win25.parquet
    

                                                                  

    Skipping existing: adm0_length15_pct98_win30.parquet
    Skipping existing: adm0_length15_pct99_win10.parquet
    Skipping existing: adm0_length15_pct99_win15.parquet
    Skipping existing: adm0_length15_pct99_win20.parquet
    Skipping existing: adm0_length15_pct99_win25.parquet
    Skipping existing: adm0_length15_pct99_win30.parquet
    Skipping existing: adm0_length30_pct95_win10.parquet
    Skipping existing: adm0_length30_pct95_win15.parquet
    Skipping existing: adm0_length30_pct95_win20.parquet
    Skipping existing: adm0_length30_pct95_win25.parquet
    Skipping existing: adm0_length30_pct95_win30.parquet
    Skipping existing: adm0_length30_pct96_win10.parquet
    Skipping existing: adm0_length30_pct96_win15.parquet
    Skipping existing: adm0_length30_pct96_win20.parquet
    Skipping existing: adm0_length30_pct96_win25.parquet
    Skipping existing: adm0_length30_pct96_win30.parquet
    Skipping existing: adm0_length30_pct97_win10.parquet
    

    Grid Search:  21%|██▏       | 32/150 [00:00<00:01, 100.36it/s]

    Skipping existing: adm0_length30_pct97_win15.parquet
    Skipping existing: adm0_length30_pct97_win20.parquet
    Skipping existing: adm0_length30_pct97_win25.parquet
    

    Grid Search:  37%|███▋      | 55/150 [00:00<00:00, 100.50it/s]

    Skipping existing: adm0_length30_pct97_win30.parquet
    Skipping existing: adm0_length30_pct98_win10.parquet
    Skipping existing: adm0_length30_pct98_win15.parquet
    Skipping existing: adm0_length30_pct98_win20.parquet
    Skipping existing: adm0_length30_pct98_win25.parquet
    Skipping existing: adm0_length30_pct98_win30.parquet
    Skipping existing: adm0_length30_pct99_win10.parquet
    Skipping existing: adm0_length30_pct99_win15.parquet
    Skipping existing: adm0_length30_pct99_win20.parquet
    Skipping existing: adm0_length30_pct99_win25.parquet
    Skipping existing: adm0_length30_pct99_win30.parquet
    Skipping existing: adm1_length15_pct95_win10.parquet
    Skipping existing: adm1_length15_pct95_win15.parquet
    Skipping existing: adm1_length15_pct95_win20.parquet
    Skipping existing: adm1_length15_pct95_win25.parquet
    Skipping existing: adm1_length15_pct95_win30.parquet
    

                                                                  

    Skipping existing: adm1_length15_pct96_win10.parquet
    

    Grid Search:  44%|████▍     | 66/150 [00:00<00:00, 103.12it/s]

    Skipping existing: adm1_length15_pct96_win15.parquet
    Skipping existing: adm1_length15_pct96_win20.parquet
    Skipping existing: adm1_length15_pct96_win25.parquet
    Skipping existing: adm1_length15_pct96_win30.parquet
    Skipping existing: adm1_length15_pct97_win10.parquet
    Skipping existing: adm1_length15_pct97_win15.parquet
    Skipping existing: adm1_length15_pct97_win20.parquet
    Skipping existing: adm1_length15_pct97_win25.parquet
    Skipping existing: adm1_length15_pct97_win30.parquet
    Skipping existing: adm1_length15_pct98_win10.parquet
    Skipping existing: adm1_length15_pct98_win15.parquet
    Skipping existing: adm1_length15_pct98_win20.parquet
    Skipping existing: adm1_length15_pct98_win25.parquet
    Skipping existing: adm1_length15_pct98_win30.parquet
    Skipping existing: adm1_length15_pct99_win10.parquet
    Skipping existing: adm1_length15_pct99_win15.parquet
    Skipping existing: adm1_length15_pct99_win20.parquet
    Skipping existing: adm1_length15_pct99_win25.parquet
    Skipping existing: adm1_length15_pct99_win30.parquet
    Skipping existing: adm1_length30_pct95_win10.parquet
    Skipping existing: adm1_length30_pct95_win15.parquet
    

    Grid Search:  44%|████▍     | 66/150 [00:00<00:00, 103.12it/s]

    Skipping existing: adm1_length30_pct95_win20.parquet
    Skipping existing: adm1_length30_pct95_win25.parquet
    

    Grid Search:  61%|██████▏   | 92/150 [00:00<00:00, 111.78it/s]

    Skipping existing: adm1_length30_pct95_win30.parquet
    Skipping existing: adm1_length30_pct96_win10.parquet
    Skipping existing: adm1_length30_pct96_win15.parquet
    Skipping existing: adm1_length30_pct96_win20.parquet
    Skipping existing: adm1_length30_pct96_win25.parquet
    Skipping existing: adm1_length30_pct96_win30.parquet
    Skipping existing: adm1_length30_pct97_win10.parquet
    Skipping existing: adm1_length30_pct97_win15.parquet
    Skipping existing: adm1_length30_pct97_win20.parquet
    Skipping existing: adm1_length30_pct97_win25.parquet
    Skipping existing: adm1_length30_pct97_win30.parquet
    Skipping existing: adm1_length30_pct98_win10.parquet
    Skipping existing: adm1_length30_pct98_win15.parquet
    Skipping existing: adm1_length30_pct98_win20.parquet
    Skipping existing: adm1_length30_pct98_win25.parquet
    Skipping existing: adm1_length30_pct98_win30.parquet
    Skipping existing: adm1_length30_pct99_win10.parquet
    Skipping existing: adm1_length30_pct99_win15.parquet
    Skipping existing: adm1_length30_pct99_win20.parquet
    Skipping existing: adm1_length30_pct99_win25.parquet
    

                                                                  

    Skipping existing: adm1_length30_pct99_win30.parquet
    Skipping existing: adm2_length15_pct95_win10.parquet
    Skipping existing: adm2_length15_pct95_win15.parquet
    

    Grid Search:  77%|███████▋  | 116/150 [00:01<00:00, 112.23it/s]

    Skipping existing: adm2_length15_pct95_win20.parquet
    Skipping existing: adm2_length15_pct95_win25.parquet
    Skipping existing: adm2_length15_pct95_win30.parquet
    Skipping existing: adm2_length15_pct96_win10.parquet
    Skipping existing: adm2_length15_pct96_win15.parquet
    Skipping existing: adm2_length15_pct96_win20.parquet
    Skipping existing: adm2_length15_pct96_win25.parquet
    Skipping existing: adm2_length15_pct96_win30.parquet
    Skipping existing: adm2_length15_pct97_win10.parquet
    Skipping existing: adm2_length15_pct97_win15.parquet
    Skipping existing: adm2_length15_pct97_win20.parquet
    Skipping existing: adm2_length15_pct97_win25.parquet
    Skipping existing: adm2_length15_pct97_win30.parquet
    Skipping existing: adm2_length15_pct98_win10.parquet
    Skipping existing: adm2_length15_pct98_win15.parquet
    Skipping existing: adm2_length15_pct98_win20.parquet
    Skipping existing: adm2_length15_pct98_win25.parquet
    

    Grid Search:  77%|███████▋  | 116/150 [00:01<00:00, 112.23it/s]

    Skipping existing: adm2_length15_pct98_win30.parquet
    Skipping existing: adm2_length15_pct99_win10.parquet
    Skipping existing: adm2_length15_pct99_win15.parquet
    

    Grid Search:  85%|████████▌ | 128/150 [00:01<00:00, 111.21it/s]

    Skipping existing: adm2_length15_pct99_win20.parquet
    Skipping existing: adm2_length15_pct99_win25.parquet
    Skipping existing: adm2_length15_pct99_win30.parquet
    Skipping existing: adm2_length30_pct95_win10.parquet
    Skipping existing: adm2_length30_pct95_win15.parquet
    Skipping existing: adm2_length30_pct95_win20.parquet
    Skipping existing: adm2_length30_pct95_win25.parquet
    Skipping existing: adm2_length30_pct95_win30.parquet
    Skipping existing: adm2_length30_pct96_win10.parquet
    Skipping existing: adm2_length30_pct96_win15.parquet
    Skipping existing: adm2_length30_pct96_win20.parquet
    Skipping existing: adm2_length30_pct96_win25.parquet
    Skipping existing: adm2_length30_pct96_win30.parquet
    Skipping existing: adm2_length30_pct97_win10.parquet
    Skipping existing: adm2_length30_pct97_win15.parquet
    Skipping existing: adm2_length30_pct97_win20.parquet
    

    Grid Search:  93%|█████████▎| 140/150 [00:01<00:00, 103.90it/s]

    Skipping existing: adm2_length30_pct97_win25.parquet
    Skipping existing: adm2_length30_pct97_win30.parquet
    

    Grid Search: 100%|██████████| 150/150 [00:01<00:00, 104.84it/s]

    Skipping existing: adm2_length30_pct98_win10.parquet
    Skipping existing: adm2_length30_pct98_win15.parquet
    Skipping existing: adm2_length30_pct98_win20.parquet
    Skipping existing: adm2_length30_pct98_win25.parquet
    Skipping existing: adm2_length30_pct98_win30.parquet
    Skipping existing: adm2_length30_pct99_win10.parquet
    Skipping existing: adm2_length30_pct99_win15.parquet
    Skipping existing: adm2_length30_pct99_win20.parquet
    Skipping existing: adm2_length30_pct99_win25.parquet
    Skipping existing: adm2_length30_pct99_win30.parquet
    
    Completed! Results saved in: grid_search_results/
    

    
    

## Model Selection: Bayesian Information Criterion (BIC)

### Why BIC?

BIC (Schwarz, 1978) provides a principled framework for model selection by penalizing
both **poor fit** and **excessive complexity**:

$$
BIC = \underbrace{k \cdot \ln(n)}_{\text{Complexity Penalty}} + \underbrace{n \cdot \ln\left(\frac{SS_W}{n}\right)}_{\text{Fit Term (negative log-likelihood)}}
$$

**Lower BIC** indicates better trade-off between fit and complexity. 

Remark. In cases of perfect within-run homogeneity (SS_W ≈ 0), a variance floor of 10^-10 is applied to ensure numerical stability.

### How BIC Addresses Our Objective

| Objective | BIC Component | Mechanism |
|-----------|---------------|-----------|
| **Internal Cohesion** | $SS_W$ (Within-run variance) | Small $SS_W$ → homogeneous probability values within runs → more cohesive periods |
| **Model Parsimony** | $k \cdot \ln(n)$ | Penalty increases with number of runs → discourages fragmentation |
| **Structural Validity** | Pre-filtering ($L_{\min}$) | Only runs ≥ $L_{\min}$ days are considered valid |

### Notation and Components

- $\mathcal{R} = \{R_1, R_2, \ldots, R_k\}$: Set of $k$ valid runs (length $\geq L_{\min}$)
- $R_i$: The $i$-th run (set of day indices belonging to run $i$)
- $|R_i|$: Number of days in run $R_i$
- $y(x)$: Original continuous probability value for day $x$

**$k$** = Number of valid runs (model complexity)
- Interpretation: Number of distinct OOS periods identified
- Larger $k$ → higher complexity penalty → BIC increases

**$n$** = Total days across all valid runs (effective sample size)
$$
n = \sum_{i=1}^{k} |R_i|
$$
- Counts only days classified as OOS (not all 365 days)
- Larger $n$ → more data supporting the model → stronger complexity penalty

**$SS_W$** = Within-run sum of squares (measure of fit quality)
$$
SS_W = \sum_{i=1}^{k} \sum_{j \in R_i} \left(y(j) - \bar{y}_i\right)^2
$$

where $\bar{y}_i = \frac{1}{|R_i|} \sum_{j \in R_i} y(j)$ is the mean probability for run $i$.

- **Lower $SS_W$**: Probability values are stable within each run → good internal cohesion → better fit
- **Higher $SS_W$**: High variability within runs → poor cohesion → worse fit

### Model Selection Procedure

1. Generate candidate segmentations for all $(\theta, w)$ combinations
2. Filter runs to keep only those with length $\geq L_{\min}$
3. Compute BIC for each configuration
4. **Select the configuration with minimum BIC**

This identifies the segmentation that best captures genuine OOS periods without 
over-fragmenting the time series.


```python
from utils.oos_validation import run_comprehensive_bic_analysis

run_comprehensive_bic_analysis()
```

    Processing adm_level=0, length=15...
    Found 25 parquet files
    Combined DataFrame shape: (109800, 13)
      ✗ Skipped: No parameter combinations with valid BIC for adm_level=0, length=15
    
    Processing adm_level=0, length=30...
    Found 25 parquet files
    Combined DataFrame shape: (109800, 13)
      ✗ Skipped: No parameter combinations with valid BIC for adm_level=0, length=30
    
    Processing adm_level=1, length=15...
    Found 25 parquet files
    Combined DataFrame shape: (1674450, 13)
      ✓ Best config: threshold=99%, window=10 days, BIC=-534.68
    
    Processing adm_level=1, length=30...
    Found 25 parquet files
    Combined DataFrame shape: (1674450, 13)
      ✓ Best config: threshold=99%, window=10 days, BIC=-643.96
    
    Processing adm_level=2, length=15...
    Found 25 parquet files
    Combined DataFrame shape: (15481800, 13)
      ✓ Best config: threshold=99%, window=10 days, BIC=-1726.71
    
    Processing adm_level=2, length=30...
    Found 25 parquet files
    Combined DataFrame shape: (15481800, 13)
      ✓ Best config: threshold=99%, window=10 days, BIC=-1812.71
    
    




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>adm_level</th>
      <th>length</th>
      <th>percentage_threshold</th>
      <th>context_window_days</th>
      <th>avg_BIC</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2</td>
      <td>30</td>
      <td>99</td>
      <td>10</td>
      <td>-1812.712999</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2</td>
      <td>15</td>
      <td>99</td>
      <td>10</td>
      <td>-1726.711951</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>30</td>
      <td>99</td>
      <td>10</td>
      <td>-643.956871</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>15</td>
      <td>99</td>
      <td>10</td>
      <td>-534.683829</td>
    </tr>
  </tbody>
</table>
</div>




```python
from utils.oos_validation import analyze_bic_grid_search, get_bic_summary_stats, plot_bic_components, print_bic_analysis_report

results = analyze_bic_grid_search(length=15, adm_level=2)

display(results)
```

    Found 25 parquet files
    Combined DataFrame shape: (15481800, 13)
    


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>iso3</th>
      <th>pcode</th>
      <th>adm_level</th>
      <th>rolling_sum_days</th>
      <th>context_window_days</th>
      <th>percentage_threshold</th>
      <th>min_oos_run_length</th>
      <th>data</th>
      <th>k</th>
      <th>n</th>
      <th>SS_W</th>
      <th>BIC</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>BFA</td>
      <td>BF1300</td>
      <td>2</td>
      <td>5</td>
      <td>10</td>
      <td>95</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>235</td>
      <td>197.358220</td>
      <td>-30.103618</td>
    </tr>
    <tr>
      <th>1</th>
      <td>BFA</td>
      <td>BF1300</td>
      <td>2</td>
      <td>5</td>
      <td>10</td>
      <td>96</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>230</td>
      <td>110.491026</td>
      <td>-157.747192</td>
    </tr>
    <tr>
      <th>2</th>
      <td>BFA</td>
      <td>BF1300</td>
      <td>2</td>
      <td>5</td>
      <td>10</td>
      <td>97</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>224</td>
      <td>48.114955</td>
      <td>-333.700581</td>
    </tr>
    <tr>
      <th>3</th>
      <td>BFA</td>
      <td>BF1300</td>
      <td>2</td>
      <td>5</td>
      <td>10</td>
      <td>98</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>220</td>
      <td>26.476082</td>
      <td>-455.037615</td>
    </tr>
    <tr>
      <th>4</th>
      <td>BFA</td>
      <td>BF1300</td>
      <td>2</td>
      <td>5</td>
      <td>10</td>
      <td>99</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>214</td>
      <td>15.377892</td>
      <td>-552.739710</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>42295</th>
      <td>TCD</td>
      <td>TD2303</td>
      <td>2</td>
      <td>5</td>
      <td>30</td>
      <td>95</td>
      <td>15</td>
      <td>dev</td>
      <td>1</td>
      <td>366</td>
      <td>577.353758</td>
      <td>172.733428</td>
    </tr>
    <tr>
      <th>42296</th>
      <td>TCD</td>
      <td>TD2303</td>
      <td>2</td>
      <td>5</td>
      <td>30</td>
      <td>96</td>
      <td>15</td>
      <td>dev</td>
      <td>1</td>
      <td>366</td>
      <td>577.353758</td>
      <td>172.733428</td>
    </tr>
    <tr>
      <th>42297</th>
      <td>TCD</td>
      <td>TD2303</td>
      <td>2</td>
      <td>5</td>
      <td>30</td>
      <td>97</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>320</td>
      <td>109.345176</td>
      <td>-332.082995</td>
    </tr>
    <tr>
      <th>42298</th>
      <td>TCD</td>
      <td>TD2303</td>
      <td>2</td>
      <td>5</td>
      <td>30</td>
      <td>98</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>306</td>
      <td>34.539169</td>
      <td>-656.089104</td>
    </tr>
    <tr>
      <th>42299</th>
      <td>TCD</td>
      <td>TD2303</td>
      <td>2</td>
      <td>5</td>
      <td>30</td>
      <td>99</td>
      <td>15</td>
      <td>dev</td>
      <td>2</td>
      <td>292</td>
      <td>5.575837</td>
      <td>-1144.473395</td>
    </tr>
  </tbody>
</table>
<p>42300 rows × 12 columns</p>
</div>



```python
plot_bic_components(results, length=15, admin_level=2, save_plot=False)
```


    
![png](OOS_validation_files/OOS_validation_5_0.png)
    



```python
print_bic_analysis_report(results, adm_level=2, length=15)
```

    ======================================================================
    BEST CONFIGURATION (Minimum BIC across all pcodes)
    ======================================================================
    Pcode: CD5210
    Percentage Threshold: 95%
    Context Window: 10 days
    Number of runs (k): 1
    Total OOS days (n): 366
    Within-run variance (SS_W): 0.0000
    BIC: -8421.56
    
    ======================================================================
    BEST CONFIGURATION PER PCODE (Top 10)
    ======================================================================
        pcode  percentage_threshold  context_window_days  k    n          BIC
    0  BF1300                    99                   15  2  202  -612.680916
    1  BF4601                    99                   25  2   97  -363.452577
    2  BF4602                    99                   10  2   93  -309.415148
    3  BF4603                    99                   20  3   51  -249.101778
    4  BF4604                    99                   15  2   86  -195.389302
    5  BF4605                    99                   10  2  214 -1085.573979
    6  BF4606                    97                   30  2   82   -98.358213
    7  BF4702                    99                   30  2   84  -294.175622
    8  BF4801                    99                   10  3  143  -426.595501
    9  BF4802                    99                   25  1   74  -318.952537
    
    ======================================================================
    MOST COMMON BEST PARAMETERS
    ======================================================================
    
    Most common threshold:
    percentage_threshold
    99    994
    98    220
    97    111
    95    104
    96     93
    Name: count, dtype: int64
    
    Most common window:
    context_window_days
    10    585
    30    393
    25    205
    15    193
    20    146
    Name: count, dtype: int64
    
    Most common combination:
    percentage_threshold  context_window_days
    99                    10                     475
                          30                     154
                          15                     140
                          25                     133
                          20                      92
    dtype: int64
    
    ======================================================================
    AVERAGE BIC BY PARAMETER COMBINATION
    ======================================================================
                                                  avg_BIC
    percentage_threshold context_window_days             
    99                   10                  -1726.711951
                         15                  -1706.217849
                         20                  -1572.786838
                         30                  -1375.023603
    98                   10                  -1356.523137
    99                   25                  -1355.997504
    98                   30                  -1163.854701
                         25                  -1134.670998
                         20                  -1127.054629
                         15                  -1107.509960
    97                   30                  -1026.503957
                         25                   -997.528035
                         20                   -982.475788
                         15                   -977.201110
                         10                   -939.417183
    96                   30                   -918.860020
                         25                   -892.312708
                         20                   -876.776347
                         15                   -858.787819
                         10                   -856.092410
    95                   30                   -815.134211
                         25                   -799.504399
                         20                   -790.215133
                         15                   -775.523033
                         10                   -741.667771
    
    Best average configuration:
      Admin Level: 2
      Length: 15
      Threshold: 99%
      Window: 10 days
      Avg BIC: -1726.71
    
    ======================================================================
    SUMMARY STATISTICS BY PARAMETER COMBINATION
    ======================================================================
                                                 k             n            SS_W  \
                                              mean   std    mean     std    mean   
    percentage_threshold context_window_days                                       
    95                   10                   1.87  0.88  252.79  107.00  220.18   
                         15                   1.72  0.75  252.52  107.34  205.51   
                         20                   1.65  0.69  253.41  107.47  211.86   
                         25                   1.57  0.63  252.68  108.98  221.32   
                         30                   1.51  0.59  253.18  109.33  224.53   
    96                   10                   1.92  0.90  244.91  108.04  135.82   
                         15                   1.73  0.74  245.50  108.79  136.11   
                         20                   1.65  0.66  246.11  108.88  134.80   
                         25                   1.60  0.63  245.91  109.50  133.29   
                         30                   1.54  0.59  245.20  110.61  128.76   
    97                   10                   1.95  0.92  235.52  109.51   83.95   
                         15                   1.80  0.79  235.54  110.25   77.04   
                         20                   1.69  0.70  236.71  110.25   76.09   
                         25                   1.62  0.65  235.94  111.21   73.30   
                         30                   1.57  0.60  237.46  110.96   72.79   
    98                   10                   2.03  0.96  221.92  109.71   37.20   
                         15                   1.84  0.82  221.35  110.55   33.60   
                         20                   1.71  0.70  223.06  111.36   34.36   
                         25                   1.65  0.65  223.85  111.13   33.18   
                         30                   1.61  0.63  223.42  112.18   31.44   
    99                   10                   2.10  1.02  200.83  108.86    9.60   
                         15                   1.93  0.88  199.45  109.35    8.23   
                         20                   1.77  0.78  202.27  110.79    9.27   
                         25                   1.73  0.77  200.44  110.49    7.73   
                         30                   1.64  0.67  201.31  111.59    8.04   
    
                                                          BIC           
                                                 std     mean      std  
    percentage_threshold context_window_days                            
    95                   10                   168.94  -741.67  2294.62  
                         15                   165.58  -775.52  2300.83  
                         20                   181.19  -790.22  2313.76  
                         25                   202.73  -799.50  2321.95  
                         30                   210.00  -815.13  2334.67  
    96                   10                   109.70  -856.09  2285.66  
                         15                   111.62  -858.79  2294.53  
                         20                   114.37  -876.78  2307.02  
                         25                   114.02  -892.31  2318.67  
                         30                   117.34  -918.86  2328.84  
    97                   10                    67.72  -939.42  2279.30  
                         15                    64.71  -977.20  2285.92  
                         20                    64.28  -982.48  2302.79  
                         25                    62.35  -997.53  2312.89  
                         30                    65.86 -1026.50  2332.89  
    98                   10                    32.60 -1356.52  2512.89  
                         15                    28.26 -1107.51  2285.10  
                         20                    29.94 -1127.05  2300.37  
                         25                    28.26 -1134.67  2323.08  
                         30                    28.63 -1163.85  2338.17  
    99                   10                    10.37 -1726.71  2626.78  
                         15                     7.69 -1706.22  2599.53  
                         20                     9.20 -1572.79  2501.31  
                         25                     7.11 -1356.00  2352.29  
                         30                     7.81 -1375.02  2372.14  
    


```python
get_bic_summary_stats(results)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead tr th {
        text-align: left;
    }

    .dataframe thead tr:last-of-type th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th colspan="2" halign="left">k</th>
      <th colspan="2" halign="left">n</th>
      <th colspan="2" halign="left">SS_W</th>
      <th colspan="2" halign="left">BIC</th>
    </tr>
    <tr>
      <th></th>
      <th></th>
      <th>mean</th>
      <th>std</th>
      <th>mean</th>
      <th>std</th>
      <th>mean</th>
      <th>std</th>
      <th>mean</th>
      <th>std</th>
    </tr>
    <tr>
      <th>percentage_threshold</th>
      <th>context_window_days</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="5" valign="top">95</th>
      <th>10</th>
      <td>1.87</td>
      <td>0.88</td>
      <td>252.79</td>
      <td>107.00</td>
      <td>220.18</td>
      <td>168.94</td>
      <td>-741.67</td>
      <td>2294.62</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1.72</td>
      <td>0.75</td>
      <td>252.52</td>
      <td>107.34</td>
      <td>205.51</td>
      <td>165.58</td>
      <td>-775.52</td>
      <td>2300.83</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1.65</td>
      <td>0.69</td>
      <td>253.41</td>
      <td>107.47</td>
      <td>211.86</td>
      <td>181.19</td>
      <td>-790.22</td>
      <td>2313.76</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1.57</td>
      <td>0.63</td>
      <td>252.68</td>
      <td>108.98</td>
      <td>221.32</td>
      <td>202.73</td>
      <td>-799.50</td>
      <td>2321.95</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1.51</td>
      <td>0.59</td>
      <td>253.18</td>
      <td>109.33</td>
      <td>224.53</td>
      <td>210.00</td>
      <td>-815.13</td>
      <td>2334.67</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">96</th>
      <th>10</th>
      <td>1.92</td>
      <td>0.90</td>
      <td>244.91</td>
      <td>108.04</td>
      <td>135.82</td>
      <td>109.70</td>
      <td>-856.09</td>
      <td>2285.66</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1.73</td>
      <td>0.74</td>
      <td>245.50</td>
      <td>108.79</td>
      <td>136.11</td>
      <td>111.62</td>
      <td>-858.79</td>
      <td>2294.53</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1.65</td>
      <td>0.66</td>
      <td>246.11</td>
      <td>108.88</td>
      <td>134.80</td>
      <td>114.37</td>
      <td>-876.78</td>
      <td>2307.02</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1.60</td>
      <td>0.63</td>
      <td>245.91</td>
      <td>109.50</td>
      <td>133.29</td>
      <td>114.02</td>
      <td>-892.31</td>
      <td>2318.67</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1.54</td>
      <td>0.59</td>
      <td>245.20</td>
      <td>110.61</td>
      <td>128.76</td>
      <td>117.34</td>
      <td>-918.86</td>
      <td>2328.84</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">97</th>
      <th>10</th>
      <td>1.95</td>
      <td>0.92</td>
      <td>235.52</td>
      <td>109.51</td>
      <td>83.95</td>
      <td>67.72</td>
      <td>-939.42</td>
      <td>2279.30</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1.80</td>
      <td>0.79</td>
      <td>235.54</td>
      <td>110.25</td>
      <td>77.04</td>
      <td>64.71</td>
      <td>-977.20</td>
      <td>2285.92</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1.69</td>
      <td>0.70</td>
      <td>236.71</td>
      <td>110.25</td>
      <td>76.09</td>
      <td>64.28</td>
      <td>-982.48</td>
      <td>2302.79</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1.62</td>
      <td>0.65</td>
      <td>235.94</td>
      <td>111.21</td>
      <td>73.30</td>
      <td>62.35</td>
      <td>-997.53</td>
      <td>2312.89</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1.57</td>
      <td>0.60</td>
      <td>237.46</td>
      <td>110.96</td>
      <td>72.79</td>
      <td>65.86</td>
      <td>-1026.50</td>
      <td>2332.89</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">98</th>
      <th>10</th>
      <td>2.03</td>
      <td>0.96</td>
      <td>221.92</td>
      <td>109.71</td>
      <td>37.20</td>
      <td>32.60</td>
      <td>-1356.52</td>
      <td>2512.89</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1.84</td>
      <td>0.82</td>
      <td>221.35</td>
      <td>110.55</td>
      <td>33.60</td>
      <td>28.26</td>
      <td>-1107.51</td>
      <td>2285.10</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1.71</td>
      <td>0.70</td>
      <td>223.06</td>
      <td>111.36</td>
      <td>34.36</td>
      <td>29.94</td>
      <td>-1127.05</td>
      <td>2300.37</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1.65</td>
      <td>0.65</td>
      <td>223.85</td>
      <td>111.13</td>
      <td>33.18</td>
      <td>28.26</td>
      <td>-1134.67</td>
      <td>2323.08</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1.61</td>
      <td>0.63</td>
      <td>223.42</td>
      <td>112.18</td>
      <td>31.44</td>
      <td>28.63</td>
      <td>-1163.85</td>
      <td>2338.17</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">99</th>
      <th>10</th>
      <td>2.10</td>
      <td>1.02</td>
      <td>200.83</td>
      <td>108.86</td>
      <td>9.60</td>
      <td>10.37</td>
      <td>-1726.71</td>
      <td>2626.78</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1.93</td>
      <td>0.88</td>
      <td>199.45</td>
      <td>109.35</td>
      <td>8.23</td>
      <td>7.69</td>
      <td>-1706.22</td>
      <td>2599.53</td>
    </tr>
    <tr>
      <th>20</th>
      <td>1.77</td>
      <td>0.78</td>
      <td>202.27</td>
      <td>110.79</td>
      <td>9.27</td>
      <td>9.20</td>
      <td>-1572.79</td>
      <td>2501.31</td>
    </tr>
    <tr>
      <th>25</th>
      <td>1.73</td>
      <td>0.77</td>
      <td>200.44</td>
      <td>110.49</td>
      <td>7.73</td>
      <td>7.11</td>
      <td>-1356.00</td>
      <td>2352.29</td>
    </tr>
    <tr>
      <th>30</th>
      <td>1.64</td>
      <td>0.67</td>
      <td>201.31</td>
      <td>111.59</td>
      <td>8.04</td>
      <td>7.81</td>
      <td>-1375.02</td>
      <td>2372.14</td>
    </tr>
  </tbody>
</table>
</div>




```python
selected = results.loc[(results['percentage_threshold'] == 99) & 
            (results['context_window_days'] == 10) &
            (results['k'] > 0)]
```


```python
# 1. Visualize distribution
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
selected['BIC'].hist(bins=30, edgecolor='black')
plt.axvline(selected['BIC'].mean(), color='red', linestyle='--', label='Mean')
plt.axvline(selected['BIC'].median(), color='green', linestyle='--', label='Median')
plt.xlabel('BIC')
plt.ylabel('Frequency')
plt.title('BIC Distribution')
plt.legend()

plt.subplot(1, 2, 2)
selected.boxplot(column='BIC')
plt.ylabel('BIC')
plt.title('BIC Boxplot')

plt.tight_layout()
plt.show()

# 2. Outliers
print("\n" + "="*70)
print("EXTREME VALUES ANALYSIS")
print("="*70)

# Worst (most negative = best fit)
worst_5 = selected.nsmallest(5, 'BIC')
print("\nTop 5 BEST configurations (most negative BIC):")
print(worst_5[['pcode', 'percentage_threshold', 'context_window_days', 'k', 'n', 'BIC']])

# Check if outliers are concentrated in few pcodes
print(f"\nPcodes with extreme BIC: {worst_5['pcode'].unique()}")

# 3. Ovefitting check...
print("\n" + "="*70)
print("OVERFITTING CHECK")
print("="*70)
extreme_configs = selected[selected['BIC'] < selected['BIC'].quantile(0.1)]
print(f"\nConfigs with BIC < 10th percentile (n={len(extreme_configs)}):")
print(extreme_configs[['k', 'n']].describe())
```


    
![png](OOS_validation_files/OOS_validation_9_0.png)
    


    
    ======================================================================
    EXTREME VALUES ANALYSIS
    ======================================================================
    
    Top 5 BEST configurations (most negative BIC):
           pcode  percentage_threshold  context_window_days  k    n          BIC
    3129  CD5210                    99                   10  1  366 -8421.558807
    3154  CD5301                    99                   10  1  366 -8421.558807
    3429  CD5404                    99                   10  1  366 -8421.558807
    3529  CD5410                    99                   10  1  366 -8421.558807
    3729  CD6109                    99                   10  1  366 -8421.558807
    
    Pcodes with extreme BIC: ['CD5210' 'CD5301' 'CD5404' 'CD5410' 'CD6109']
    
    ======================================================================
    OVERFITTING CHECK
    ======================================================================
    
    Configs with BIC < 10th percentile (n=137):
                    k           n
    count  137.000000  137.000000
    mean     1.065693  362.773723
    std      0.248655    9.825681
    min      1.000000  323.000000
    25%      1.000000  366.000000
    50%      1.000000  366.000000
    75%      1.000000  366.000000
    max      2.000000  366.000000
    
