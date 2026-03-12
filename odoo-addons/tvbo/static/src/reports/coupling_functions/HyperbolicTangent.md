## HyperbolicTangent

### Coupling Equation

$$c_i = \sum_{j=0}^{-1 + N} a \left(\tanh{\left(\frac{b x_{j} - midpoint}{\sigma} \right)} + 1\right) {w}_{i,j}$$

### Properties

- **Delayed:** Yes
- **Sparse:** Yes

### Parameters

| Name | Default | Description |
|------|---------|-------------|
| $b$ | 1.0 | Scaling factor for the variable |
| $a$ | 1.0 | Minimum of the sigmoid function |
| $\sigma$ | 1.0 | Standard deviation of the coupling |
| $midpoint$ | 0.0 | Midpoint of the linear portion of the sigmoid |
