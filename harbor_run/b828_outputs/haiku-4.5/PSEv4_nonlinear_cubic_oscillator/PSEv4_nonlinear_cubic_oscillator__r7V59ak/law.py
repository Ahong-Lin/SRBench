def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt using a degree-3 polynomial model fitted to the training data.

    The model is based on the formula:
    dv_dt = intercept + sum of polynomial terms up to degree 3 in (x, v, t)
    """
    # Coefficients derived from polynomial fitting (degree 3)
    intercept = 0.108186622253

    # Linear terms
    coef_x = -0.604287908362
    coef_v = -0.132695926029
    coef_t = 0.020811074265

    # Quadratic terms
    coef_x2 = -0.811565409592
    coef_xv = -0.072809261688
    coef_xt = 0.335316713279
    coef_v2 = 0.112028930806
    coef_vt = -0.161854067940
    coef_t2 = 0.005332191369

    # Cubic terms
    coef_x3 = -1.186289056002
    coef_x2v = 0.158432511997
    coef_x2t = 0.270397366349
    coef_xv2 = 0.097388003991
    coef_xvt = -0.102583994632
    coef_xt2 = -0.083370400482
    coef_v3 = -0.199886719358
    coef_v2t = -0.176664488897
    coef_vt2 = -0.073393667063
    coef_t3 = -0.000034312603

    result = []
    for row in input_data:
        x = row['x']
        v = row['v']
        t = row['t']

        # Compute the polynomial
        dv_dt = (
            intercept +
            # Linear terms
            coef_x * x +
            coef_v * v +
            coef_t * t +
            # Quadratic terms
            coef_x2 * (x * x) +
            coef_xv * (x * v) +
            coef_xt * (x * t) +
            coef_v2 * (v * v) +
            coef_vt * (v * t) +
            coef_t2 * (t * t) +
            # Cubic terms
            coef_x3 * (x * x * x) +
            coef_x2v * (x * x * v) +
            coef_x2t * (x * x * t) +
            coef_xv2 * (x * v * v) +
            coef_xvt * (x * v * t) +
            coef_xt2 * (x * t * t) +
            coef_v3 * (v * v * v) +
            coef_v2t * (v * v * t) +
            coef_vt2 * (v * t * t) +
            coef_t3 * (t * t * t)
        )

        result.append({'dv_dt': dv_dt})

    return result
