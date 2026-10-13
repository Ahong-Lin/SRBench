"""Build a portable ground-truth law from the exact packaged DataGenSpec."""
import numpy as np
import sympy
from sympy.core.function import AppliedUndef
from srbench.generation.data_generator import _lambdify


def compile_truth(contract):
    names = contract.features + list(contract.parameters)
    if contract.implicit_branch:
        from srbench.common.polynomial_equilibrium import compile_equilibrium
        return compile_equilibrium(contract.expression, contract.target, names)
    f, expr = _lambdify(contract.expression, names, force_symbols=set(names) | {contract.target})
    unknown = {str(s) for s in expr.free_symbols} - set(names)
    if unknown or expr.atoms(AppliedUndef) or expr.has(sympy.Derivative, sympy.Integral):
        raise ValueError(f"ground truth is not closed over the declared features/parameters: {unknown or expr}")
    return f


def truth_values(contract, frame):
    function = compile_truth(contract)
    # Pointwise evaluation handles Piecewise/Min/Max with scalar branches just
    # like the generated reference. The trusted formula needs no child process.
    parameters = list(contract.parameters.values())
    values = np.asarray([float(function(*row, *parameters))
                         for row in frame[contract.features].itertuples(index=False, name=None)])
    if not np.isfinite(values).all():
        raise ValueError("ground truth has nonfinite values in the requested domain")
    return values


def reference_source(contract):
    compile_truth(contract)
    if contract.implicit_branch:
        import inspect
        from srbench.common import polynomial_equilibrium
        return inspect.getsource(polynomial_equilibrium) + f"\nFEATURES = {contract.features!r}\nTARGET = {contract.target!r}\nPARAMETERS = {contract.parameters!r}\n_function = compile_equilibrium({contract.expression!r}, TARGET, FEATURES + list(PARAMETERS))\ndef law(rows):\n    return [{{TARGET: float(_function(*[float(row[n]) for n in FEATURES], *PARAMETERS.values()))}} for row in rows]\n"
    declared = contract.features + list(contract.parameters) + [contract.target]
    return f'''"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = {contract.features!r}
TARGET = {contract.target!r}
PARAMETERS = {contract.parameters!r}
_symbols = {{name: sympy.Symbol(name) for name in {declared!r}}}
_expression = sympy.sympify({contract.expression!r}, locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))}} for row in rows]
'''


def check_reference_source(source, frame, contract):
    namespace = {}
    exec(compile(source, "reference_law.py", "exec"), namespace)
    predictions = np.asarray([namespace["law"]([row])[0][contract.target]
                             for row in frame[contract.features].to_dict(orient="records")])
    expected = truth_values(contract, frame)
    if not np.allclose(predictions, expected, rtol=1e-10, atol=1e-12):
        raise ValueError("standalone reference does not reproduce ground truth")
    return predictions
