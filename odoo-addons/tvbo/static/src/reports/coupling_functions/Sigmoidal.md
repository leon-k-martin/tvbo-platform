## Sigmoidal

### Coupling Equation

$$c_i = \sum_{j=0}^{-1 + N} H \left(Q + \tanh{\left(G \left(P x_{j} - \theta\right) \right)}\right) {w}_{i,j}$$

### Properties

- **Delayed:** Yes
- **Sparse:** No

### Parameters

| Name | Default | Description |
|------|---------|-------------|
| $midpoint$ | 0.0 |  |
| $cmax$ | 1.0 | Maximum of the sigmoid function |
| $\sigma$ | 230.0 |  |
| $cmin$ | -1.0 | Minimum of sigmoid function |
| $a$ | 1.0 | Scaling of sigmoidal |
