## TemporalAverage

Running temporal mean over a sliding window of configurable length. Returns one averaged sample per period.

### Properties

- **Period:** 0.9765625 ms

### Processing Pipeline

**1. temporal_average**
  Output: `averaged`
  ```
  mean(X.reshape(-1, window_size, *X.shape[1:]), axis=1)
  ```
  - window_size =  (Number of integration steps per averaging window = period / dt)
