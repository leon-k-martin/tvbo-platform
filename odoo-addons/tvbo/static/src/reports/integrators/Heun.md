## Heun

### Properties

- **Step size:** 0.01220703125
- **Duration:** 1000.0
- **Number of stages:** 1
- **Delayed:** Yes

### Intermediate Expressions

**X1:**
```
X + dX0 * dt + noise + stimulus * dt
```

### Update Rule

**X_{t+1}:**
```
(dX0 + dX1) * (dt / 2)
```
