## SigmoidalJansenRit

### Coupling Equation

$$c_i = a \sum_{j=0}^{-1 + N} \left(cmin + \frac{cmax - cmin}{e^{r \left(midpoint - \left({x_{j}}_{0} - {x_{j}}_{1}\right)\right)} + 1.0}\right) {w}_{i,j}$$

### Properties

- **Delayed:** Yes
- **Sparse:** No

### Parameters

| Name | Default | Description |
|------|---------|-------------|
| $a$ | 1.0 | Scaling of the coupling term |
| $midpoint$ | 6.0 | Midpoint of the linear portion of the sigmoid |
| $cmax$ | 0.005 | Maximum of the Sigmoid function |
| $r$ | 0.56 | The steepness of the sigmoidal transformation |
| $cmin$ | 0.0 | minimum of the Sigmoid function |
