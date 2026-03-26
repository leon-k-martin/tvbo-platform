## QIF neural mass — bifurcation in η̄

Quadratic integrate-and-fire population model. Continuation of equilibria in the mean neural excitability η̄, reproducing the fold bifurcation diagram from Montbrió et al. (2015).

### Model

**{'name': 'QIF', 'parameters': {'tau': {'value': 1.0}, 'eta_bar': {'value': -5.0}, 'Delta': {'value': 1.0}, 'J': {'value': 15.0}}, 'state_variables': {'r': {'equation': {'rhs': '(Delta/(pi*tau) + 2*r*v) / tau'}, 'initial_value': 0.01}, 'v': {'equation': {'rhs': '(v**2 + eta_bar + J*r*tau - (pi*r*tau)**2) / tau'}, 'initial_value': -2.0}}}**

### Continuations

**Equilibrium branch in η̄**
