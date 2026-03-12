## Linear

### Coupling Equation

$$c_i = b + a \sum_{j=0}^{-1 + N} x_{j} {w}_{i,j}$$

### Properties

- **Delayed:** Yes
- **Sparse:** No

### Parameters

| Name | Default | Description |
|------|---------|-------------|
| $b$ | 0.0 | Shifts the base of the connection strength while maintaining the absolute difference between different values. |
| $a$ | 0.00390625 | Linear scaling factor of the coupled (delayed) input. |
