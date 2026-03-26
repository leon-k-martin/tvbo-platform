## EI Tuning: Functional Connectivity Fitting

Fitting functional connectivity using the two-population Reduced Wong-Wang model with explicit excitatory and inhibitory populations. Combines Feedback Inhibition Control (FIC) to maintain local E-I balance with EIB tuning to globally optimize network connectivity. Supports both iterative (FIC+EIB) and gradient-based optimization approaches.


### Dynamics

**ReducedWongWangEIB**
: Biophysically-based neural mass model with explicit excitatory (E) and inhibitory (I) populations. Each population has separate synaptic gating variables (S_e, S_i) and transfer functions. Enables independent control of E-I balance via the J_i parameter.
  - Outputs: S_e, S_i, H_e, H_i

### Network

- **Label:** Desikan-Killiany
- **Description:** Structural connectivity from dk_average dataset
- **Bids Dir:** ../networks/bids/dk_average

### Observations

- **bold**
- **mean_S_e**
- **mean_S_e_final**
- **mean_S_i**
- **fc_target**

### Algorithms

- **fic**
- **fic_eib**

### Integration

- **Method:** Heun
- **Description:** Heun integrator
- **Step Size:** 4.0
- **Duration:** 300000
- **Transient Time:** 300000

### References

- Schirner, M., Deco, G., & Ritter, P. (2023). Learning how network structure shapes decision-making for bio-inspired computing. Nature Communications, 14(1), Article 1.
- Wong, K.-F., & Wang, X.-J. (2006). A recurrent network mechanism of time integration in perceptual decisions. J Neurosci, 26:1314-1328.
- Deco, G., Ponce-Alvarez, A., Mantini, D., Romani, G.L., Hagmann, P., & Corbetta, M. (2013). Resting-state functional connectivity emerges from structurally and dynamically shaped slow linear fluctuations. J Neurosci, 33(27):11239-11252.
