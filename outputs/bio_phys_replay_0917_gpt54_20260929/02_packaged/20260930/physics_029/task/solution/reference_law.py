"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['E_cm', 'beam_energy_spread', 'channel_threshold_energy']
TARGET = 'sigma'
PARAMETERS = {'sigma_peak': 12.0, 'resonance_mass': 1.0, 'intrinsic_width': 0.05, 'width_relaxation_scale': 0.3, 'coupling_drift_scale': 0.6, 'coupling_width_mix': 2.0, 'threshold_width_strength': 0.7}
_symbols = {name: sympy.Symbol(name) for name in ['E_cm', 'beam_energy_spread', 'channel_threshold_energy', 'sigma_peak', 'resonance_mass', 'intrinsic_width', 'width_relaxation_scale', 'coupling_drift_scale', 'coupling_width_mix', 'threshold_width_strength', 'sigma']}
_expression = sympy.sympify('((sigma_peak*(1 + coupling_drift_scale*((E_cm/resonance_mass) - 1)*(1 + coupling_width_mix*intrinsic_width/resonance_mass)))*(resonance_mass**2*(intrinsic_width*(E_cm/resonance_mass)*(1 + width_relaxation_scale*((E_cm/resonance_mass)**2 - 1) + threshold_width_strength*sqrt(Piecewise((0, E_cm < channel_threshold_energy), (E_cm/channel_threshold_energy - 1, True)))))**2)/((E_cm**2 - resonance_mass**2)**2 + resonance_mass**2*(intrinsic_width*(E_cm/resonance_mass)*(1 + width_relaxation_scale*((E_cm/resonance_mass)**2 - 1) + threshold_width_strength*sqrt(Piecewise((0, E_cm < channel_threshold_energy), (E_cm/channel_threshold_energy - 1, True)))))**2))/(1 + beam_energy_spread**2/((intrinsic_width*(E_cm/resonance_mass)*(1 + width_relaxation_scale*((E_cm/resonance_mass)**2 - 1) + threshold_width_strength*sqrt(Piecewise((0, E_cm < channel_threshold_energy), (E_cm/channel_threshold_energy - 1, True)))))**2 + (E_cm - resonance_mass)**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
