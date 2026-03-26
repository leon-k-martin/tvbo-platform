## GlobalAverage

Spatial mean across all network nodes at each sampling period. Reduces spatial dimension to a single global signal per state variable.

### Properties

- **Period:** 0.9765625 ms

### Processing Pipeline

**1. global_mean**
  Output: `global_averaged`
  ```
  mean(X, axis=-2, keepdims=True)
  ```
