## BOLD_DoubleExponential

BOLD fMRI observation model using a Double Exponential hemodynamic response function.

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
  A1 * exp(-t / tau_1) + A2 * exp(-t / tau_2)
  ```
  - A1 = 3.87 ()
  - tau_1 = 0.9 ()
  - A2 = 0.18 ()
  - tau_2 = 9.5 ()
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
