## AfferentCouplingTemporalAverage

Temporally averaged afferent coupling input at each node. Combines coupling input recording with temporal averaging.

### Properties

- **Period:** 0.9765625 ms

### Processing Pipeline

**1. temporal_average**
  Output: `averaged_coupling`
  ```
  mean(X.reshape(-1, window_size, *X.shape[1:]), axis=1)
  ```
  - window_size =  (Number of integration steps per averaging window = period / dt)
