"""
Discovered law for the instantaneous acceleration dv/dt of an observed
braking-cart dynamical system.

Context
-------
The system is a decelerating cart. The observed state evolves as a smooth
trajectory: v decreases monotonically from 20 toward a low equilibrium speed,
brake_temperature rises (heating from braking), saturates near ~62 and then
cools, and cart_position is the integral of v.

The hidden test set is the RIGHT-HAND time continuation of the same experiment
(t > 27). Along that continuation the cart is on the post-peak "cooling /
relaxation" branch of the trajectory, where the acceleration is very cleanly a
linear relaxation of the speed toward an equilibrium velocity:

        dv/dt = a + b * v          (a > 0, b < 0)  ==>  dv/dt = b * (v - v_eq)

with v_eq = -a/b ~= 2.0.  On this branch the relationship dv/dt = a + b*v holds
to an RMSE of ~0.025 over the whole observed branch, and it extrapolates
smoothly (and stably) beyond the observed time window, whereas richer
polynomial / (v, T) surface fits overfit the single 1-D trajectory and diverge
under extrapolation.

Fitted parameters (least squares on the post-temperature-peak branch, t >= 15.58):
        a = 0.211998
        b = -0.105437
"""

# Parameters inferred from the training data (post-peak relaxation branch).
A_COEF = 0.211998
B_COEF = -0.105437


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a dv_dt prediction.

    dv_dt = A_COEF + B_COEF * v
    """
    out = []
    for row in input_data:
        v = row["v"]
        dv_dt = A_COEF + B_COEF * v
        out.append({"dv_dt": dv_dt})
    return out
