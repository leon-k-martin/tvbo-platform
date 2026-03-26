## MEG

Forward solution for magnetoencephalography. Projects source neural activity through a lead field matrix to MEG sensor locations using oriented gradiometers. If no precomputed gain is available, uses the single-sphere analytic formula (Sarvas 1987, Eq. 25) for the magnetic field produced by current dipoles in a conducting sphere.

### Properties

- **Imaging modality:** MEG
- **Period:** 0.9765625 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| permeability | 1.25663706e-06 | H/m | Magnetic constant (permeability of free space) |

### Processing Pipeline

**1. compute_gain**
  Output: `gain`
  ```
  (mu / (4 * pi * F**2)) * (cross(F * Q, r_0) - sum(cross(Q, r_0) * (r_s * dF), axis=1))
  ```
  - mu = 1.25663706e-06 ()
  - Q =  (Source dipole orientations (n_sources, 3))
  - r_0 =  (Source dipole positions (n_sources, 3))
  - r_s =  (Sensor positions (n_sensors, 3))

**2. lead_field_projection**
  Output: `projected`
  ```
  gain @ sum(X, axis=-1) / period_steps
  ```
  - gain =  (Lead field matrix (n_sensors, n_sources))
  - period_steps =  (Number of integration steps per sampling period)

**3. add_noise**
  Output: `MEG`
  ```
  X + noise
  ```
  - noise =  (Observation noise (n_sensors, 1))
