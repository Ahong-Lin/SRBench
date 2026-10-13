"""Deterministic global minima of coercive polynomial free energies."""
import numpy as np
import sympy

def compile_equilibrium(expression, target, names):
    symbols = {n: sympy.Symbol(n) for n in names + [target]}
    residual = sympy.sympify(expression, locals=symbols)
    if residual.free_symbols - set(symbols.values()):
        raise ValueError("Undeclared symbols in equilibrium residual")
    poly = sympy.Poly(residual, symbols[target])
    coefficients = sympy.lambdify([symbols[n] for n in names], poly.all_coeffs(), modules="numpy")
    def evaluate(*values):
        c = np.trim_zeros(np.asarray(coefficients(*values), dtype=float), "f")
        if len(c) < 2 or not np.isfinite(c).all() or (len(c)-1) % 2 != 1 or c[0] <= 0:
            raise ValueError("Equilibrium requires a coercive even-degree polynomial potential")
        roots = np.roots(c / np.max(np.abs(c)))
        real = roots.real[np.abs(roots.imag) <= 1e-9 * (1 + np.abs(roots.real))]
        stable = real[np.polyval(np.polyder(c), real) > 0]
        if not len(stable):
            raise ValueError("No strictly stable equilibrium")
        energy = np.polyval(np.polyint(c), stable)
        order = np.argsort(energy)
        if len(order) > 1 and abs(energy[order[1]]-energy[order[0]]) <= 1e-12 * max(float(np.max(np.abs(energy))), np.finfo(float).tiny):
            raise ValueError("Degenerate global equilibrium; specify an unambiguous domain")
        root = float(stable[order[0]])
        scale = float(np.polyval(np.abs(c), abs(root)))
        if abs(np.polyval(c,root)) > 1e-9 * max(scale,np.finfo(float).tiny):
            raise ValueError("Equilibrium residual is too large")
        return root
    return evaluate
