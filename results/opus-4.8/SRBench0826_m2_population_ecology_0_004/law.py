"""Recovered competitive-dynamics law for dN1_dt.

Model form (per-capita growth is a quadratic in the three state variables):

    dN1/dt = N1 * ( c0
                    + c1*N1 + c2*N2 + c3*P1
                    + c11*N1^2 + c12*N1*N2 + c13*N1*P1
                    + c22*N2^2 + c23*N2*P1 + c33*P1^2 )

This is a generalized Lotka-Volterra competition model that includes
higher-order (pairwise-density) interaction terms on top of the classic
intrinsic-growth / self-crowding / mutual-suppression structure.

Coefficients were estimated by least squares on the full training
trajectory (R^2 = 0.99999954, RMSE = 7.2e-4).
"""

# Per-capita polynomial coefficients (multiply the whole bracket by N1).
C0  =  0.7070686448020456     # intrinsic per-capita growth (constant)
C1  =  0.006415290490640583   # * N1
C2  = -0.011923733549192366   # * N2
C3  = -0.0020304420888048263  # * P1
C11 = -9.743736567745598e-06  # * N1^2
C12 = -0.00011428796684482512 # * N1*N2
C13 = -0.00012163820971441261 # * N1*P1
C22 =  7.483343238967466e-05  # * N2^2
C23 = -0.00012678193966435828 # * N2*P1
C33 = -4.921988442909464e-05  # * P1^2


def _dN1_dt(N1: float, N2: float, P1: float) -> float:
    percap = (
        C0
        + C1 * N1 + C2 * N2 + C3 * P1
        + C11 * N1 * N1 + C12 * N1 * N2 + C13 * N1 * P1
        + C22 * N2 * N2 + C23 * N2 * P1 + C33 * P1 * P1
    )
    return N1 * percap


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dN1_dt for each observation.

    Parameters
    ----------
    input_data : list of dicts, each with keys 't', 'N1', 'N2', 'P1'.

    Returns
    -------
    list of dicts, each with key 'dN1_dt'.
    """
    out = []
    for row in input_data:
        N1 = float(row["N1"])
        N2 = float(row["N2"])
        P1 = float(row["P1"])
        out.append({"dN1_dt": _dN1_dt(N1, N2, P1)})
    return out
