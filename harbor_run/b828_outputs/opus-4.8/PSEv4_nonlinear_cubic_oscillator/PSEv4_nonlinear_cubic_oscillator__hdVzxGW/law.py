"""Discovered law for dv_dt.

Model (nonlinear damped oscillator with cubic restoring force and
position-dependent linear damping):

    dv_dt = a * x**3 + (b + c * |x|) * v

Parameters were fit by least squares on the training data:
    a = -2.25470818   (cubic restoring stiffness)
    b = -0.70501374   (base linear damping coefficient)
    c =  0.22267414   (position-dependent damping correction, in |x|)

Fit quality on training data: R2 = 0.9999956, RMSE = 7.5e-4.
"""

A = -2.25470818
B = -0.70501374
C = 0.22267414


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = row["x"]
        v = row["v"]
        dv_dt = A * x**3 + (B + C * abs(x)) * v
        out.append({"dv_dt": dv_dt})
    return out
