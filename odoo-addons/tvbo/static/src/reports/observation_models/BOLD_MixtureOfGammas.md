## BOLD_MixtureOfGammas

BOLD fMRI observation model using the canonical double-gamma hemodynamic response function (Glover 1999). Standard HRF used in most fMRI analysis packages (SPM, FSL, AFNI).

### Properties

- **Imaging modality:** BOLD

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| TR | 2000.0 | ms |  |

### Processing Pipeline

**1. temporal_average_interim**
  Output: `interim_averaged`
  ```
  mean(X.reshape(-1, stepsize, *X.shape[1:]), axis=1)
  ```
  - stepsize = 1 ()

**2. hemodynamic_response**
  Output: `hrf_kernel`
  ```
  a1 * t**(d1 - 1) * exp(-b1 * t) / gamma(d1) - c * a2 * t**(d2 - 1) * exp(-b2 * t) / gamma(d2)
  ```
  - a1 = 6.0 ()
  - b1 = 1.0 ()
  - d1 = 6.0 ()
  - c = 0.35 (Ratio of undershoot to positive response)
  - a2 = 1.0 ()
  - b2 = 1.0 ()
  - d2 = 16.0 ()
  - duration = 20 ()
  - stock_dt = 0.004 ()

**3. convolve**
  Output: `convolved`
  - in2 = hrf_kernel ()
  - mode = same ()

**4. subsample_to_period**
  Output: `Bold`
  ```
  X[::stepsize]
  ```
  - stepsize =  (TR / dt)
