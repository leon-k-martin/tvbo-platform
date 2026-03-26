## SubSample

Temporal decimation of selected state variables. Records every N-th integration step without any averaging or smoothing.

### Properties

- **Period:** 0.9765625 ms

### Processing Pipeline

**1. subsample**
  Output: `subsampled`
  ```
  X[::step]
  ```
  - step =  (Decimation factor = period / dt)
