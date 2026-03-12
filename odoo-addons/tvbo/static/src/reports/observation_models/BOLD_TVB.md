## BOLD_TVB

BOLD fMRI observation model using the Balloon-Windkessel hemodynamic model as implemented in The Virtual Brain (TVB). Transforms neural activity into simulated BOLD signal via hemodynamic convolution.

### Properties

- **Imaging modality:** BOLD

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| TR | 720.0 | ms | Repetition time |

### Processing Pipeline

**1. temporal_average_interim**
  Output: `interim_averaged`
  ```
  jnp.mean(X.reshape(-1, stepsize, *X.shape[1:]), axis=1)
  ```
  - stepsize = 1 (Interim averaging window (1 = no averaging, use raw dt=4ms))

**2. HemodynamicResponseFunctionTVB**
  Output: `hrf_kernel`
  ```
  1/3 * exp(-0.5*(t / tau_s)) * sin(sqrt(1/tau_f - 1/(4*tau_s**2)) * t) / sqrt(1/tau_f - 1/(4*tau_s**2))
  ```
  - tau_f = 0.4 ()
  - tau_s = 0.8 ()
  - duration = 20 (HRF kernel duration (TVB default hrf_length=20s))
  - stock_dt = 0.004 (Stock sample period = 4ms (1/_stock_sample_rate))

**3. fftconvolve**
  Output: `convolved`
  - in2 = hrf_kernel (HRF kernel reversed for convolution)
  - mode = same ()

**4. subsample_to_TR**
  Output: `bold_subsampled`
  ```
  X[::stepsize]
  ```
  - stepsize = 180 (TR / dt = 720ms / 4ms = 180)

**5. volterra_transform**
  Output: `Bold`
  ```
  (X - 1.0) * k_1 * V_0
  ```
  - k_1 = 5.6 (Intravascular signal contribution)
  - V_0 = 0.02 (Resting blood volume fraction)
