

**JR peak-frequency — my run**

Customized Jansen-Rit experiment from the knowledge graph.



**Local Dynamics: Jansen-Rit Neural Mass Model**

Neural mass model with three populations (pyramidal, excitatory interneurons, inhibitory interneurons). Produces characteristic alpha-band oscillations.
# --- PARAMETERS (from JansenRit.DEFAULT_PARAMS in JR.qmd) ---

system: continuous; autonomous: True; modes: 1; state variables: 6; parameters: 13; derived variables: 3.

**State Equations**


$$\dot{y_{0}} = y_{3}$$

$$\dot{y_{1}} = y_{4}$$

$$\dot{y_{2}} = y_{5}$$

$$\dot{y_{3}} = - y_{0} \cdot a^{2} - 2.0 \cdot a \cdot y_{3} + A \cdot a \cdot sigm_{y1 y2}$$

$$\dot{y_{4}} = - y_{1} \cdot a^{2} - 2.0 \cdot a \cdot y_{4} + A \cdot a \cdot \left(DelayedSigmoidalJansenRit + \mu + J \cdot a_{2} \cdot sigm_{y0 1}\right)$$

$$\dot{y_{5}} = - y_{2} \cdot b^{2} - 2.0 \cdot b \cdot y_{5} + B \cdot J \cdot a_{4} \cdot b \cdot sigm_{y0 3}$$

where

$$sigm_{y0 1} = \frac{2.0 \cdot \nu_{max}}{1.0 + e^{r \cdot \left(v_{0} - J \cdot a_{1} \cdot y_{0}\right)}}$$

*Sigmoid of a_1*J*y0*

$$sigm_{y0 3} = \frac{2.0 \cdot \nu_{max}}{1.0 + e^{r \cdot \left(v_{0} - J \cdot a_{3} \cdot y_{0}\right)}}$$

*Sigmoid of a_3*J*y0*

$$sigm_{y1 y2} = \frac{2.0 \cdot \nu_{max}}{1.0 + e^{r \cdot \left(v_{0} + y_{2} - y_{1}\right)}}$$

*Sigmoid of y1-y2*



**State Variables**

| Variable | Initial Value | Unit | Equation | Domain / Sampling | Flags | Description |
|:---------|:--------------|:-----|:---------|:------------------|:------|:------------|
| $y_{0}$ | 0.0 | — | differential (order 1) | — | VOI, recorded |  |
| $y_{1}$ | 5.0 | — | differential (order 1) | — | VOI, recorded |  |
| $y_{2}$ | 5.0 | — | differential (order 1) | — | VOI, recorded |  |
| $y_{3}$ | 0.0 | — | differential (order 1) | — | VOI, recorded |  |
| $y_{4}$ | 0.0 | — | differential (order 1) | — | VOI, coupling, recorded |  |
| $y_{5}$ | 0.0 | — | differential (order 1) | — | VOI, recorded |  |

**Parameters**

| Parameter | Value | Default | Unit | Domain / Sampling | Flags | Description |
|:----------|------:|:--------|:-----|:------------------|:------|:------------|
| $A$ | 3.25 | — | $\mathrm{mV}$ | — | optimum=0.0 | Maximum amplitude of EPSP [mV] |
| $B$ | 22.0 | — | $\mathrm{mV}$ | — | optimum=0.0 | Maximum amplitude of IPSP [mV] |
| $J$ | 135.0 | — | — | — | optimum=0.0 | Average number of synapses |
| $a$ | 0.065 | — | $\mathrm{ms}^{-1}$ | [0.001, 0.2], n=0 | optimum=0.0 | Reciprocal of membrane time constant (excitatory) |
| $a_{1}$ | 1.0 | — | — | — | optimum=0.0 | Excitatory feedback probability |
| $a_{2}$ | 0.8 | — | — | — | optimum=0.0 | Slow excitatory feedback probability |
| $a_{3}$ | 0.25 | — | — | — | optimum=0.0 | Inhibitory feedback probability |
| $a_{4}$ | 0.25 | — | — | — | optimum=0.0 | Slow inhibitory feedback probability |
| $b$ | 0.065 | — | $\mathrm{ms}^{-1}$ | [0.001, 0.2], n=0 | optimum=0.0 | Reciprocal of membrane time constant (inhibitory) |
| $\mu$ | 0.15 | — | — | — | optimum=0.0 | Mean input firing rate |
| $\nu_{max}$ | 0.0025 | — | $\mathrm{ms}^{-1}$ | — | optimum=0.0 | Maximum firing rate |
| $r$ | 0.56 | — | $\mathrm{mV}^{-1}$ | — | optimum=0.0 | Steepness of sigmoid |
| $v_{0}$ | 5.52 | — | $\mathrm{mV}$ | — | optimum=0.0 | Firing threshold [mV] |



**Coupling Inputs**

| Input | Source | Dimension | Keys | Description |
|:------|:-------|----------:|:-----|:------------|
| DelayedSigmoidalJansenRit | — | 1 | — |  |

**Coupling Terms**

| Term | Value | Domain / Sampling | Flags | Description |
|:-----|------:|:------------------|:------|:------------|
| $DelayedSigmoidalJansenRit$ | None | — | — |  |


**Brain Network: Desikan-Killiany**

Structural connectivity from dk_average dataset


| Setting | Value |
|:--------|:------|
| Regions | 84 |
| Conduction velocity | 3.0 mm_per_ms |
| Distance unit | mm |
| Time unit | ms |
| Data file | connectome.h5 |
| Transform (weight) | $M_{\text{out}} = \frac{W}{W_{max}}$ |
| Structural measures | streamlineCount, tractLength |
| Nodes | 84 explicit nodes |
| Weights | shape=84x84, format=Format(layout=Layout(major_to_minor=(0, 1), tiling=(), sub_byte_element_size_in_bits=0), sharding=SingleDeviceSharding(device=CpuDevice(id=0), memory_kind=device)), dtype=float32 |


**Coupling: Delayed Sigmoidal Jansen-Rit Coupling**

Sigmoidal Jansen-Rit coupling function with delays

$$c = G \cdot \sum_{j=0}^{-1 + N} \left(cmin + \frac{cmax - cmin}{1.0 + e^{r \cdot \left(midpoint - \left({y_{1}}_{j} - {y_{2}}_{j}\right)\right)}}\right) \cdot {w}_{i,j}$$

| Property | Value |
|:---------|:------|
| Incoming states | $y_{1}$, $y_{2}$ |
| Delays | enabled |
| Symmetry | directed |

Receives $y_{1}$, $y_{2}$ from connected regions with conduction delays.

**Pre-synaptic:** $c_{\text{pre}} = cmin + \frac{cmax - cmin}{1.0 + e^{r \cdot \left(midpoint + y_{2} - y_{1}\right)}}$

**Post-synaptic:** $c_{\text{post}} = G \cdot gx$


| Parameter | Value | Unit | Domain / Sampling | Flags | Description |
|:----------|------:|:-----|:------------------|:------|:------------|
| $G$ | 15.0 | — | — | free, optimum=0.0 | Global coupling strength |
| $cmax$ | 0.005 | — | — | optimum=0.0 | 2 * nu_max from TVB default |
| $cmin$ | None | — | — | optimum=0.0 |  |
| $midpoint$ | 6.0 | — | — | optimum=0.0 |  |
| $r$ | 0.56 | — | — | optimum=0.0 |  |


**Numerical Integration**

| Setting | Value |
|:--------|:------|
| Method | Heun |
| Time step | $\Delta t = 1.0$ ms |
| Duration | 1000.0 ms |
| Transient | 20000.0 ms discarded |
| Absolute tolerance | 1e-10 |
| Relative tolerance | 1e-10 |
| Stages | 2 |
| Delayed state history | True |

**Integration Update Expressions**

$$X_{1} = X + noise + dX_{0} \cdot dt + dt \cdot stimulus$$
$$dX = \frac{dt \cdot \left(dX_{0} + dX_{1}\right)}{2}$$


Additive Gaussian noise: $d\mathbf{x} = f(\mathbf{x},t)\,dt + \sigma\,d\mathbf{W}_t$

type=gaussian, seed=42.

| Parameter | Value | Unit | Domain / Sampling | Description |
|:----------|------:|:-----|:------------------|:------------|
| $\sigma$ | 0.0001 | — | — |  |

**Observations**

*Primary Observations*

| Name | Source | Sampling / Window | Pipeline | Description |
|:-----|:-------|:------------------|:---------|:------------|
| **Simulated Power Spectral Density** | $['y0']$ | scale=ms, VOI=0, skip=0, tail=0, window=0 | subsample → transpose → welch | Power spectral density using Welch's method on simulated y0 |

*Derived Observations*

| Name | Source Observations | Sampling / Window | Pipeline | Description |
|:-----|:-------------------|:------------------|:---------|:------------|
| **Average Spectrum** | simulated_psd | skip=0, tail=0, window=0, scale=ms | mean | Mean power spectrum across all regions |
| **Peak Frequencies per Region** | simulated_psd | skip=0, tail=0, window=0, scale=ms | argmax → squeeze → index_at | Peak frequency for each brain region from its PSD |
| **Peak Frequency** | avg_spectrum, simulated_psd | skip=0, tail=0, window=0, scale=ms | argmax → index_at | Extract peak frequency from average spectrum |


*Processing Pipelines*

**Simulated Power Spectral Density:**

| Step | Function | Input | Output | Arguments | Description |
|-----:|:---------|:------|:-------|:----------|:------------|
| 1 | `subsample` | None | None | data=integration.result (Input time series from simulation) |  |
| 2 | `transpose` | None | transposed | a=subsample (Subsampled time series) |  |
| 3 | `welch` | None | frequencies, psd | x=transposed (Transposed time series (nodes, time)), fs=100.0 (Sampling frequency (Hz)), nperseg=256 (Segment length for Welch) |  |

**Average Spectrum:**

| Step | Function | Input | Output | Arguments | Description |
|-----:|:---------|:------|:-------|:----------|:------------|
| 1 | `mean` | None | avg_psd | a=simulated_psd.psd (Power spectrum from simulated_psd observation), axis (Average over regions dimension) |  |

**Peak Frequencies per Region:**

| Step | Function | Input | Output | Arguments | Description |
|-----:|:---------|:------|:-------|:----------|:------------|
| 1 | `argmax` | None | peak_indices | a=simulated_psd.psd (PSD array (regions, 1, frequencies)), axis=-1 (Find max along frequency axis) |  |
| 2 | `squeeze` | None | peak_indices_squeezed | a=peak_indices |  |
| 3 | `index_at` | None | peak_frequencies | arr=simulated_psd.frequencies (Frequency array from PSD), idx=peak_indices_squeezed (Indices of peak frequencies per region) |  |

**Peak Frequency:**

| Step | Function | Input | Output | Arguments | Description |
|-----:|:---------|:------|:-------|:----------|:------------|
| 1 | `argmax` | None | peak_idx | a=avg_spectrum (Average power spectrum (output of jnp.mean)) |  |
| 2 | `index_at` | None | None | arr=simulated_psd.frequencies (Frequency array from PSD), idx=peak_idx (Index of peak frequency) |  |


**Parameter Explorations**


*Frequency Landscape Exploration*

Grid search over a and b parameters to map the relationship between time constants and peak oscillation frequency. Used to understand the parameter landscape before optimization.
# Parameters with grid specifications (use domain with n for grid points)

| Setting | Value |
|:--------|:------|
| Mode | product |
| Parallel evaluations | 1 |

| Parameter | Values / Range | Steps |
|:----------|:---------------|------:|
| $a$ | [0.001, 0.2] | 32 |
| $b$ | [0.001, 0.2] | 32 |


**Observable:** `peak_frequency`


**Optimization**


*Spectral Gradient Fitting*

Fit region-specific a and b parameters to reproduce the MEG frequency gradient. Target frequencies range from 11 Hz (visual cortex) to 7 Hz (most distant regions from lateral occipital gyrus).
# Free parameters to optimize (references to dynamics.parameters by name)

**Loss function:** `spectral_loss`

| Argument | Value | Description |
|:---------|:------|:------------|
| simulated | observations.simulated_psd.psd | Simulated power spectrum from observation (n_regions, n_freqs) |
| target | None | Target power spectrum (passed to optimizer at runtime) |

**Free parameters:** $JansenRit.a$, $JansenRit.b$


| Setting | Value |
|:--------|------:|
| Algorithm | adamaxw |
| Learning rate | 0.001 |
| Max iterations | 151 |


**Functions**


**cauchy_pdf**  —  Cauchy-Lorentz probability density function


Arguments: x, x0, gamma


$$cauchy_pdf(x, x0, gamma) = \frac{1}{\pi \cdot \gamma \cdot \left(1 + \frac{\left(x - x_{0}\right)^{2}}{\gamma^{2}}\right)}$$


**compute_target_frequencies**  —  Compute target frequencies from tract lengths to visual cortex


Arguments: d, f_min, f_max


$$compute_target_frequencies(d, f_min, f_max) = f_{max} - \frac{\left(d - \operatorname{min}{\left(d \right)}\right) \cdot \left(f_{max} - f_{min}\right)}{- \operatorname{min}{\left(d \right)} + \operatorname{max}{\left(d \right)}}$$


**correlation**  —  Pearson correlation coefficient


Arguments: x, y


$$correlation(x, y) = \frac{\sum_{i=0}^{-1 + n} \left(- \operatorname{mean}{\left(x \right)} + {x}_{i}\right) \cdot \left(- \operatorname{mean}{\left(y \right)} + {y}_{i}\right)}{\sqrt{\left(\sum_{i=0}^{-1 + n} \left(- \operatorname{mean}{\left(x \right)} + {x}_{i}\right)^{2}\right) \cdot \sum_{i=0}^{-1 + n} \left(- \operatorname{mean}{\left(y \right)} + {y}_{i}\right)^{2}}}$$


**spectral_loss**  —  1 - correlation between simulated and target spectra (per-element)


Arguments: simulated, target


$$spectral_loss(simulated, target) = 1 - \operatorname{correlation}{\left(simulated,target \right)}$$


**Execution**

| Setting | Value |
|:--------|------:|
| Workers | 8 |
| Precision | float64 |
| Random seed | 42 |

**References**

Jansen, B. & Rit, V. (1995). Electroencephalogram and visual evoked potential generation in a mathematical model of coupled cortical columns. *Biological Cybernetics*, 73(4), 357-366.

Jansen, B., Zouridakis, G., & Brandt, M. (1993). A neurophysiologically-based mathematical model of flash visual evoked potentials. *Biological Cybernetics*, 68(3), 275-283.
- Mahjoory et al. (2020) eLife 9:e53715 - MEG frequency gradient
- Jansen & Rit (1995) Biol Cybern 73:357-366 - Neural mass model
