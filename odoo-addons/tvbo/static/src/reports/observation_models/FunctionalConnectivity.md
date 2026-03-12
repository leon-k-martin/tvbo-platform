## FunctionalConnectivity

Functional Connectivity (FC) observation model that computes pairwise Pearson correlation coefficients between regional time series. Commonly used to characterize the statistical dependencies between brain regions from fMRI or simulated neural activity.

### Properties

- **Period:** 720.0 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| TR | 720.0 | ms | Repetition time |
| fisher_z | True |  | Apply Fisher z-transformation to correlations |

### Processing Pipeline

**1. bandpass_filter**
  Output: `filtered`
  ```
  bandpass(X, low_freq, high_freq, fs)
  ```
  - low_freq = 0.01 (Low frequency cutoff)
  - high_freq = 0.1 (High frequency cutoff)
  - order = 2 (Filter order)

**2. zscore**
  Output: `normalized`
  ```
  (X - mean(X)) / std(X)
  ```
  - axis = 0 (Normalize along time axis)

**3. correlation**
  Output: `fc_matrix`
  ```
  corrcoef(X.T)
  ```
  - rowvar = False (Each column represents a variable (region))

**4. fisher_z_transform**
  Output: `FC`
  ```
  arctanh(X)
  ```
  - clip_value = 0.999 (Clip correlations to avoid infinity at r=±1)
  - apply = True (Whether to apply Fisher z-transformation)
