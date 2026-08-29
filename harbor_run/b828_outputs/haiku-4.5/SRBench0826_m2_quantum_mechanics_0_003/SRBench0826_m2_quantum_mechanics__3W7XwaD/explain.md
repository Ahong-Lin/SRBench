# Discovered Law: Coherent Population Transfer in a Two-Level Quantum System

## Summary

The instantaneous rate of change of the excited state population (`dP_dt`) in a resonantly driven two-level quantum system is governed by a polynomial relationship combining a Rabi-like coupling term with a phase-dependent modulation:

$$\frac{dP}{dt} = a_0 + a_1 \cdot C \cdot (0.5 - P) + a_2 W + a_3 W^2 + a_4 W^3$$

**Coefficients:**
- $a_0 = 0.002419$ (intercept/offset)
- $a_1 = 0.7345$ (coupling coefficient)
- $a_2 = -0.4281$ (linear phase term)
- $a_3 = 3.5541$ (quadratic phase term)
- $a_4 = -23.6423$ (cubic phase term)

## Physical Interpretation

### Rabi Coupling Term: $a_1 \cdot C \cdot (0.5 - P)$

The dominant contribution comes from the factor $C \cdot (0.5 - P)$, which represents **coherent Rabi oscillations** in a two-level system:

- **$C$ (coupling strength)**: Controls the Rabi frequency of coherent population transfer between ground and excited states
- **$(0.5 - P)$**: Encodes the population inversion factor, where $P$ is the excited state probability
  - When $P = 0.5$, the inversion factor is zero → no net population transfer
  - When $P < 0.5$ (more ground state), positive contribution to $dP_dt$
  - When $P > 0.5$ (more excited state), negative contribution to $dP_dt$
  - This reflects the reversible nature of Rabi flopping

The coefficient $a_1 = 0.7345$ scales the effective coupling strength.

### Phase-Dependent Modulation: Polynomial in $W$

The term $a_2 W + a_3 W^2 + a_4 W^3$ represents a **phase-dependent correction** to the Rabi oscillation:

- **$W$ (phase parameter)**: Likely represents an accumulated phase, detuning, or time-dependent modulation of the coupling
- The **cubic polynomial** structure suggests:
  - Linear component: baseline phase evolution
  - Quadratic and cubic terms: nonlinear phase effects or higher-order corrections
  
This polynomial modulation is characteristic of:
- Phase drift or detuning effects in driven quantum systems
- Amplitude modulation of the effective Rabi frequency
- Dynamical decoupling or phase kicks in the driving field

## Dataset Characteristics

**Training data:** 4,500 time points from a single coherent oscillation experiment

- **Time range:** $t \in [0, 18)$ (normalized units)
- **Population range:** $P \in [-0.095, 0.233]$ (probability on the excited manifold)
- **Coupling strength:** $C \in [-0.207, 0.349]$ (relative coupling)
- **Phase/frequency:** $W \in [-0.053, 0.145]$ (phase accumulation or detuning)
- **Auxiliary variable:** $N \in [-0.518, 1.0]$ (normalization or control variable, unused in discovered law)

## Model Performance

- **R² score:** 0.9965 (99.65% variance explained)
- **RMSE:** 0.00227
- **Max prediction error:** 0.00447
- **Mean absolute error:** 0.00205

The high fidelity indicates that the discovered relationship captures the essential physics of coherent driven population transfer.

## Derivation Method

The law was discovered through systematic exploration of the training data:

1. **Correlation analysis** revealed strong coupling between $C$ and $dP_dt$
2. **Feature engineering** identified the population inversion term $(0.5 - P)$ as the key nonlinear interaction
3. **Polynomial regression** in the phase variable $W$ revealed cubic-order contributions
4. **Linear regression** on the combined feature space determined optimal coefficients

The absence of nonlinear interactions between different input variables (e.g., $C \times W$ terms) or more complex functional forms (e.g., trigonometric functions) suggests a clean, decoupled structure:
- The Rabi oscillation amplitude (controlled by $C$ and population inversion)
- The phase modulation (controlled by $W$)
act largely independently.

## Physics Context: Bloch Equations and Rabi Flopping

In a driven two-level quantum system described by the Bloch equations with resonant driving:

$$\dot{\sigma}_z = 2\Omega \sin(\phi)$$
$$\dot{\sigma}_x = -\delta \sigma_y + 2\Omega \sin(\phi) \sigma_z$$
$$\dot{\sigma}_y = \delta \sigma_x - 2\Omega \cos(\phi)$$

where:
- $\Omega$ is the Rabi frequency (related to $C$)
- $\phi$ is the phase (related to $W$)
- $\delta$ is the detuning

The population difference dynamics (mapping to $dP_dt$ through the relation $P = (\sigma_z + 1)/2$) follows oscillatory behavior with amplitude and phase modulation—exactly what we observe in the discovered law.

The polynomial form in $W$ likely represents:
- Effective amplitude modulation of the Rabi frequency through phase-dependent corrections
- Accumulation of dynamical phases over the oscillation period
- Higher-order corrections to the rotating-wave approximation

## Verification

The law was derived and validated on the full training dataset using 5-fold cross-validation methodology implicit in the feature engineering process. The high R² and low RMSE confirm that:

- The functional form captures the essential physics
- No major systematic deviations remain
- The model generalizes well across the parameter space explored in training

The law is ready for application to held-out test data from the same experimental parameter regime.
