## PreSigmoidal

### Coupling Equation

$$c_i = \sum_{j=0}^{-1 + N} H \left(Q + \tanh{\left(G \left(P x_{j} - \theta\right) \right)}\right) {w}_{i,j}$$

### Properties

- **Delayed:** Yes
- **Sparse:** No

### Parameters

| Name | Default | Description |
|------|---------|-------------|
| $\theta$ | 0.5 | Threshold |
| $P$ | 1.0 | Excitation-Inhibition ratio |
| $Q$ | 1.0 | Average |
| $H$ | 0.5 | Global Factor |
| $G$ | 60.0 | Gain |
