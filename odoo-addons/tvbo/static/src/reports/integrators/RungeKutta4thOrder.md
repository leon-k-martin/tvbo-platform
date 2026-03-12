## RungeKutta4thOrder

### Properties

- **Step size:** 0.01220703125
- **Duration:** 1000.0
- **Number of stages:** 4
- **Delayed:** Yes

### Intermediate Expressions

**X1:**
```
X + (dt / 2) * dX0
```

**X2:**
```
X + (dt / 2) * dX1
```

**X3:**
```
X + dt * dX2
```

### Update Rule

**X_{t+1}:**
```
(dt / 6) * (dX0 + 2.0 * dX1 + 2.0 * dX2 + dX3)
```
