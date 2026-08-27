import math

# Newtonian inverse-square gravity toward a central body at the origin.
#   a = -G*M * r_vec / |r|^3
# so the x-component of acceleration is
#   dvx_dt = -G*M * x / (x^2 + y^2)^(3/2)
#
# G*M was fitted to the training data by least squares. The physical value
# implied by the initial condition (x=1, y=0, dvx_dt=-1.06) is G*M = 1.06;
# the least-squares value over the whole (noisy) trajectory is ~0.981, which
# minimizes prediction error on the recorded targets.
GM = 0.9810385816378295


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = row["x"]
        y = row["y"]
        r = math.sqrt(x * x + y * y)
        dvx_dt = -GM * x / (r ** 3)
        out.append({"dvx_dt": dvx_dt})
    return out
