## iEEG

Forward solution for intracranial/stereoelectroencephalography (SEEG). Projects source activity through a lead field matrix to implanted depth electrode contacts. Uses the same single-sphere analytic formula as scalp EEG (Sarvas 1987, Eq. 12), but with electrode positions inside the brain volume.

### Properties

- **Imaging modality:** SEEG
- **Period:** 0.9765625 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| conductivity | 1.0 | S/m | Tissue conductivity for the analytic point-dipole approximation. Only used when no precomputed gain is available. |

### Processing Pipeline

**1. compute_gain**
  Output: `gain`
  ```
  sum(Q * (a / norm(a)**3), axis=1) / (4 * pi * sigma)
  ```
  - sigma = 1.0 ()
  - Q =  (Source dipole orientations (n_sources, 3))
  - a =  (Source-to-electrode vectors (n_sources, 3))

**2. lead_field_projection**
  Output: `projected`
  ```
  gain @ sum(X, axis=-1) / period_steps
  ```
  - gain =  (Lead field matrix (n_sensors, n_sources))
  - period_steps =  (Number of integration steps per sampling period)

**3. add_noise**
  Output: `iEEG`
  ```
  X + noise
  ```
  - noise =  (Observation noise (n_sensors, 1))
