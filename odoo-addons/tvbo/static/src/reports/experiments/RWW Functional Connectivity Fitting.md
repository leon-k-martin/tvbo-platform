## RWW Functional Connectivity Fitting

Fitting functional connectivity using the Reduced Wong-Wang model. Two-stage optimization: global parameters first, then regional heterogeneity. Based on tvboptim RWW.qmd tutorial.


### Dynamics

**ReducedWongWang**
: Biophysically-based neural mass model for BOLD FC fitting. Captures slow dynamics relevant for resting-state fMRI.
  - Outputs: S, H

### Network

- **Label:** Desikan-Killiany
- **Description:** Structural connectivity from dk_average dataset
- **Bids Dir:** ../networks/bids/dk_average

### Observations

- **empirical_fc**
- **bold**

### Explorations

**w-G Parameter Landscape**
: Grid search over excitatory recurrence (w) and global coupling (G) to understand the FC fitting landscape before optimization.

### Integration

- **Method:** Heun
- **Step Size:** 4.0
- **Duration:** 120000
- **Transient Time:** 120000

### References

- Wong & Wang (2006) J Neurosci 26:1314-1328 - Reduced Wong-Wang model
- Deco et al. (2014) J Neurosci 34:7886-7898 - Resting-state FC modeling
