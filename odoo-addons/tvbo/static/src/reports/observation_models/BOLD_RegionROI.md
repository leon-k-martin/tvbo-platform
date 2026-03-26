## BOLD_RegionROI

BOLD fMRI observation model that computes the hemodynamic response at each source location and spatially averages within brain regions using a parcellation mapping. Produces per-region BOLD signals suitable for comparison with parcellated empirical data.

### Properties

- **Imaging modality:** BOLD
- **Period:** 2000.0 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| hrf_length | 20000.0 | ms |  |

### Processing Pipeline

**1. temporal_average_interim**
  Output: `interim_averaged`
  ```
  mean(X.reshape(-1, window, *X.shape[1:]), axis=1)
  ```
  - window = 1 ()

**2. hemodynamic_response**
  Output: `hrf_kernel`
  ```
  1/3 * exp(-0.5*(t / tau_s)) * sin(sqrt(1/tau_f - 1/(4*tau_s**2)) * t) / sqrt(1/tau_f - 1/(4*tau_s**2))
  ```
  - tau_s = 0.8 ()
  - tau_f = 0.4 ()
  - duration = 20 ()
  - stock_dt = 0.004 ()

**3. convolve**
  Output: `convolved`
  - in2 = hrf_kernel ()
  - mode = same ()

**4. subsample_to_period**
  Output: `subsampled`
  ```
  X[::step]
  ```
  - step =  (Subsample factor)

**5. volterra_transform**
  Output: `bold_source`
  ```
  (X - 1.0) * k_1 * V_0
  ```
  - k_1 = 5.6 ()
  - V_0 = 0.02 ()

**6. region_average**
  Output: `Bold`
  ```
  spatial_mean @ X
  ```
  - spatial_mean =  (Region averaging matrix (n_regions, n_sources))
