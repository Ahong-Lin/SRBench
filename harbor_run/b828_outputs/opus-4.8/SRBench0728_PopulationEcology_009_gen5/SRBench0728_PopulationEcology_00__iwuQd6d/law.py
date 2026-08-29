"""
Discovered law for the observed dynamical system.

The population N grows under a delayed-logistic (Hutchinson-type) mechanism in
which the effective crowding pressure is carried by the state variable
`crowding_load` (C).  C is an exponentially-weighted memory of N obeying
    dC/dt = 0.2 * (N - C)          (verified from the data to rmse ~8e-4)

so C acts as a smoothed/delayed density that feeds back on the growth rate.
The instantaneous right-hand side for N is an explicit autonomous function of
the current density N and the current crowding load C:

    dN/dt = N * ( a + b*N + c*C + d*C^2 )

This is a generalized delayed-logistic growth law: the per-capita growth rate
(a + b*N + c*C + d*C^2) is positive when crowding is low and becomes negative
once C exceeds the carrying capacity (~900), driving the damped oscillation
observed in the data toward the equilibrium N = C ~ 899.

Parameters were fit by linear least squares on the full training set.
No explicit time dependence is used (t was tested and found to only overfit
the initial transient while degrading extrapolation), so the law remains valid
on the held-out right-hand time segment.
"""

# Fitted parameters (linear least squares on the full training set)
A = 0.512297058      # constant per-capita growth term
B = 2.16994975e-05   # density self-term  (N)
C_COEF = -7.61344523e-04  # crowding pressure (C)
D = 1.89071570e-07   # crowding curvature (C^2)


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        N = row["N"]
        C = row["crowding_load"]
        dN_dt = N * (A + B * N + C_COEF * C + D * C * C)
        out.append({"dN_dt": dN_dt})
    return out
