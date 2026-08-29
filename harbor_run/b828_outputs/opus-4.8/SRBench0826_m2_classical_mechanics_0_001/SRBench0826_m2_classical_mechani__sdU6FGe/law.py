"""
Discovered law for the vertically oscillating, viscously damped mass.

Target: instantaneous acceleration dv/dt as an explicit pointwise function of
the observed state (t, x, v, z).

Physical model (autonomous, no explicit t dependence):

    dv/dt = -k*x - beta*x**3 - c*v + g*z + a0

    -k*x            linear (Hooke) restoring force of the spring
    -beta*x**3      cubic hardening correction of the real spring (Duffing term)
    -c*v            linear viscous drag of the surrounding medium
    +g*z            slow "memory" contribution of the medium.  The auxiliary
                    variable z obeys dz/dt = -z - v (verified from the data to
                    ~5e-3, i.e. numerical-derivative noise), i.e. z is an
                    exponentially-relaxing filtered record of the velocity.
    +a0             constant offset: the mass hangs under gravity, so the
                    oscillation is centred on x_eq = a0/k != 0 rather than 0.

Constants were fitted once on the training trajectory and are frozen here.
Each row is mapped independently; no state is carried between calls.
"""

# Fitted constants (frozen).  dv/dt = C_X*x + C_X3*x**3 + C_V*v + C_Z*z + C_0
C_X = -1.816346   # -k
C_X3 = -0.427385  # -beta  (cubic hardening spring)
C_V = -0.459940   # -c     (linear viscous damping)
C_Z = 0.041067    # +g     (medium memory term, z' = -z - v)
C_0 = -0.181165   # gravity offset (equilibrium at x_eq = -C_0/C_X)


def law(input_data):
    """Map each input row to a single dv_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'x', 'v', 'z'.

    Returns
    -------
    list[dict[str, float]]
        One dict {'dv_dt': value} per input row.
    """
    out = []
    for row in input_data:
        x = row["x"]
        v = row["v"]
        z = row["z"]
        dv_dt = C_X * x + C_X3 * x * x * x + C_V * v + C_Z * z + C_0
        out.append({"dv_dt": dv_dt})
    return out
