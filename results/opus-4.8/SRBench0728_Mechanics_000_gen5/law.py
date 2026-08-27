import math

# Discovered law for the instantaneous acceleration dv_dt of the braking cart.
#
#   dv/dt = v * ( a + b*bt + A*sin(k*x) + B*cos(k*x) )
#
# where
#   v  = velocity
#   bt = brake_temperature
#   x  = cart_position
#
# Interpretation:
#   -a*v            : speed-proportional braking/drag deceleration
#   +b*(v*bt)       : brake "fade" -- the deceleration weakens as the brake heats
#   v*(A sin+B cos) : a position-periodic force (road grade / periodic track),
#                     whose amplitude scales with speed. k ~ 0.109 -> wavelength ~58.
#
# Coefficients fit on the full training trajectory (least squares).
A_V   = -0.06584050571947014   # coefficient of v
B_VBT =  0.00016346574483136844  # coefficient of v*bt
A_SIN = -0.014730840813842239  # coefficient of v*sin(k*x)
B_COS =  0.0036858107737160303  # coefficient of v*cos(k*x)
K     =  0.109                 # spatial angular frequency


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        v = row["v"]
        bt = row["brake_temperature"]
        x = row["cart_position"]
        kx = K * x
        dv_dt = v * (
            A_V
            + B_VBT * bt
            + A_SIN * math.sin(kx)
            + B_COS * math.cos(kx)
        )
        out.append({"dv_dt": dv_dt})
    return out
