"""The row-wise regression interface, independent of scientific evolution."""
from dataclasses import asdict, dataclass
import math


def noiseless_spec(spec):
    """Apply the exact-output policy to current and legacy DataGenSpecs."""
    normalized = dict(spec)
    normalized["noise"] = 0.0
    normalized.pop("excitation_ok", None)
    normalized.pop("excitation_report", None)
    return normalized


@dataclass(frozen=True)
class LawContract:
    features: list[str]
    target: str
    family: str
    expression: str
    parameters: dict[str, float]
    implicit_branch: str | None = None

    def to_dict(self):
        return asdict(self)


def contract_from_spec(spec):
    integrator = spec.get("integrator")
    axes = spec.get("independent_variables") or []
    features = [axis["symbol"] for axis in axes]
    params = {p["symbol"]: float(p["value"]) for p in spec.get("parameters", [])}
    if len(params) != len(spec.get("parameters", [])) or not all(map(math.isfinite, params.values())):
        raise ValueError("parameters must be unique and finite")
    if not axes:
        raise ValueError("spec needs independent_variables with sampling ranges")
    for axis in axes:
        low, high = map(float, axis["range"])
        if not math.isfinite(low) or not math.isfinite(high) or low >= high:
            raise ValueError(f"invalid range for {axis['symbol']}")
        if axis.get("scale", "linear") not in {"linear", "log"}:
            raise ValueError("supported coordinate scales are linear and log")
        if axis.get("scale") == "log" and low <= 0:
            raise ValueError("log scale needs a positive range")
    if integrator == "root_solve_implicit" and spec.get("implicit_branch") == "global_minimum_polynomial_potential":
        target = spec["dependent_variable"]
        expression = spec["rhs_for_integrator"]
        family = "static"
    elif integrator == "evaluate_explicit":
        target = spec["dependent_variable"]
        expression = spec["rhs_for_integrator"]
        family = "static"
    elif integrator == "integrate_system":
        states = spec.get("state_variables") or []
        rhss = spec.get("state_rhs") or []
        target_state = spec.get("benchmark_target_state")
        target = spec.get("benchmark_output")
        if len(axes) != 1 or not states or len(states) != len(rhss) or target_state not in states or not target:
            raise ValueError("ODE packaging needs a closed system and explicit derivative benchmark metadata")
        if set(states) != set(spec.get("initial_conditions", {})):
            raise ValueError("every ODE state needs its own initial condition")
        if not all(math.isfinite(float(v)) for v in spec["initial_conditions"].values()):
            raise ValueError("ODE initial conditions must be finite")
        features += states
        expression = rhss[states.index(target_state)]
        family = "ode"
    else:
        raise ValueError(f"packaging does not support integrator {integrator!r}; use explicit static or typed ODE derivative specs. Implicit laws require an explicit branch.")
    if len(set(features)) != len(features) or target in features or set(features) & set(params) or target in params:
        raise ValueError("feature, target and parameter roles must be distinct")
    return LawContract(features, target, family, expression, params, spec.get("implicit_branch"))
