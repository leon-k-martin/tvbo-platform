## JR Peak Frequency Optimization

Reproducing MEG Resting-State Frequency Gradients with Network Dynamics. This experiment fits region-specific Jansen-Rit parameters to reproduce the empirical frequency gradient from visual cortex (11 Hz) to association areas (7 Hz).


### Dynamics

**JansenRit**
: Neural mass model with three populations (pyramidal, excitatory interneurons, inhibitory interneurons). Produces characteristic alpha-band oscillations.

### Network

- **Label:** Desikan-Killiany
- **Description:** Structural connectivity from dk_average dataset
- **Bids Dir:** ../networks/bids/dk_average

### Observations

- **simulated_psd**

### Explorations

- **frequency_landscape**

### Integration

- **Method:** Heun
- **Step Size:** 1.0
- **Duration:** 1000
- **Transient Time:** 20000

### References

- Mahjoory et al. (2020) eLife 9:e53715 - MEG frequency gradient
- Jansen & Rit (1995) Biol Cybern 73:357-366 - Neural mass model
