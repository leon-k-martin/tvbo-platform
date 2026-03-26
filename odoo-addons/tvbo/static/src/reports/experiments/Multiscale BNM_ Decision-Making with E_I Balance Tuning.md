## Multiscale BNM: Decision-Making with E/I Balance Tuning

Multiscale brain network model coupling large-scale structural connectivity with a small-scale frontoparietal circuit for decision-making (DM) and working memory (WM). The large-scale model uses the Reduced Wong-Wang model (Deco et al., 2014, JNeurosci) with explicit excitatory and inhibitory populations. The functional circuit implements winner-take-all DM and persistent-activity WM based on Murray, Jaramillo & Wang (2017, JNeurosci).
Key innovation: The ratio of long-range excitation (LRE) to feedforward inhibition (FFI) controls functional connectivity between brain regions. This E/I balance tuning enables fitting personalized brain network models to empirical functional connectivity and explains individual differences in cognitive performance (speed-accuracy trade-off in intelligence tests).


### Dynamics

**ReducedWongWangEI**
: Dynamical mean field model with explicit excitatory (E) and inhibitory (I) populations derived from a spiking neuronal network. Extended with long-range excitation (LRE) and feedforward inhibition (FFI) pathways to enable E/I balance tuning for FC fitting.
  - Outputs: S_E, S_I, I_E, r_E, r_I

**MurrayWangDM**
: Two-module circuit for decision-making (DM) and working memory (WM). Module 1 (PPC - posterior parietal cortex): sensory evidence accumulation. Module 2 (PFC - prefrontal cortex): decision/action selection. Each module has two populations (A, B) competing via cross-inhibition. Winner-take-all dynamics for DM; persistent activity for WM.
  - Outputs: S_A1, S_B1, S_A2, S_B2, r_A1, r_B1, r_A2, r_B2

### Network

- **Label:** HCP MMP Connectome (379 regions)
- **Description:** Structural connectivity from Human Connectome Project dwMRI tractography. Uses the HCP multimodal parcellation (Glasser et al., 2016) with 379 regions. Connectivity matrices include streamline counts and tract lengths for delays.

- **Number Of Nodes:** 379

### Observations

- **S_E_timeseries**
- **I_E_timeseries**
- **mean_S_E**
- **mean_r_E**
- **input_correlation**
- **input_amplitude**
- **r_A1_timeseries**
- **r_B1_timeseries**
- **r_A2_timeseries**
- **r_B2_timeseries**

### Algorithms

- **fic**
- **eib**

### Explorations

- **EI_ratio_sweep**
- **contrast_sweep**

### Integration

- **Method:** euler
- **Description:** Forward Euler integration with dt = 1 ms
- **Step Size:** 1.0
- **Duration:** 30000.0
- **Transient Time:** 25000.0
- **Unit:** ms

### References

- Schirner, M., Deco, G., & Ritter, P. (2023). Learning how network structure shapes decision-making for bio-inspired computing. Nature Communications, 14(1), Article 2963. https://doi.org/10.1038/s41467-023-38626-y
- Murray, J.D., Jaramillo, J., & Wang, X.J. (2017). Working memory and decision-making in a frontoparietal circuit model. Journal of Neuroscience, 37(50), 12167-12186.
- Deco, G., Ponce-Alvarez, A., Hagmann, P., Romani, G.L., Mantini, D., & Corbetta, M. (2014). How local excitation-inhibition ratio impacts the whole brain dynamics. Journal of Neuroscience, 34(23), 7886-7898.
- Wong, K.F. & Wang, X.J. (2006). A recurrent network mechanism of time integration in perceptual decisions. Journal of Neuroscience, 26(4), 1314-1328.
- Vogels, T.P., Sprekeler, H., Zenke, F., Clopath, C., & Gerstner, W. (2011). Inhibitory plasticity balances excitation and inhibition in sensory pathways and memory networks. Science, 334(6062), 1569-1573.
