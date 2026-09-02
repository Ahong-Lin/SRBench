def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Apparent velocity of an enzyme assay as a reversible inhibitor is titrated
    in at fixed substrate.

    The velocity declines hyperbolically with inhibitor concentration from an
    inhibitor-free value V0 toward a non-zero floor Vf (partial/hyperbolic
    inhibition), with a half-maximal effect at I50:

        v = Vf + (V0 - Vf) / (1 + I / I50)

    Fitted constants (train data, exact to machine precision):
        Vf  = 45.0      (residual velocity floor as I -> infinity)
        V0  = 66.666667 (velocity with no inhibitor)
        I50 = 15.0      (inhibitor concn giving half the maximal decline)

    Equivalent closed forms:
        v = 45 + 325 / (I + 15)
        v = (45*I + 1000) / (I + 15)
    """
    I = input_data[0]["I"]
    v = 45.0 + 325.0 / (I + 15.0)
    return [{"v": v}]
