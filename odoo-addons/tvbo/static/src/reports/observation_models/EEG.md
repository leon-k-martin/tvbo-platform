## EEG

Forward solution for scalp electroencephalography. Projects source neural activity through a lead field (gain) matrix to electrode locations on the scalp. If no precomputed gain is available, uses a single-sphere analytic approximation (Sarvas 1987, Eq. 12). Supports re-referencing: common average, single-electrode, or ideal reference-free recording.

### Properties

- **Imaging modality:** EEG
- **Period:** 0.9765625 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| conductivity | 1.0 | S/m | Volume conductor conductivity for the single-sphere analytic approximation. Only used when no precomputed gain is available. |
| reference_electrode |  |  | Re-referencing scheme. Options: - Electrode label (e.g. "Cz"): subtract that electrode signal - "average": subtract mean across all channels - null: ideal reference-free recording |

### Processing Pipeline

**1. compute_gain**
  Output: `gain`
  ```
  sum(Q * (a / norm(a)**3), axis=1) / (4 * pi * sigma)
  ```
  - sigma = 1.0 ()
  - Q =  (Source dipole moment orientations (n_sources, 3))
  - a =  (Source-to-sensor vectors: r_sensor - r_source (n_sources, 3))

**2. lead_field_projection**
  Output: `projected`
  ```
  gain @ sum(X, axis=-1) / period_steps
  ```
  - gain =  (Lead field matrix (n_sensors, n_sources))
  - period_steps =  (Number of integration steps per sampling period)

**3. rereference**
  Output: `EEG`
