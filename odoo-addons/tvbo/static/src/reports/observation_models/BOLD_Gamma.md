## BOLD_Gamma

BOLD fMRI observation model using a Gamma-shaped hemodynamic response function. Provides a simpler, unimodal HRF shape.

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
  ((var / mean**2) * t)**(var / mean) * exp(-(var / mean) * t) / abs(t)
  ```
  - mean = 3.0 ()
  - var = 1.5 ()
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
