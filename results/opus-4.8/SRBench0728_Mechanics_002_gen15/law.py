import math


# Coefficients fitted by least squares on the full training trajectory.
# Model (see explain.md):
#   dvx_dt = c_vy*vy + c_g*x/r^3 + c_gy*y/r^3
#            + c_dx*r^2*vx + c_dy*r^2*vy      (van der Pol-type radial damping)
#            + c_vx*vx + c_v2vy*v^2*vy        (velocity damping / turning)
#            + c_x*x + const
# where r = sqrt(x^2 + y^2), v^2 = vx^2 + vy^2.
C_VY   = 0.47418978366579734
C_G    = -0.33374573002336444
C_GY   = -1.0592127490277727
C_DX   = 0.04437866852770396
C_DY   = 0.06309032860902093
C_VX   = -0.8684674240164326
C_V2VY = -1.3844288000150904
C_X    = -0.10566885831214926
CONST  = 0.0006159098145316561


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = row["x"]
        y = row["y"]
        vx = row["vx"]
        vy = row["vy"]

        r2 = x * x + y * y
        r = math.sqrt(r2)
        r3 = r2 * r if r > 1e-9 else 1e-27
        v2 = vx * vx + vy * vy

        dvx_dt = (
            C_VY * vy
            + C_G * x / r3
            + C_GY * y / r3
            + C_DX * r2 * vx
            + C_DY * r2 * vy
            + C_VX * vx
            + C_V2VY * v2 * vy
            + C_X * x
            + CONST
        )
        out.append({"dvx_dt": dvx_dt})
    return out
