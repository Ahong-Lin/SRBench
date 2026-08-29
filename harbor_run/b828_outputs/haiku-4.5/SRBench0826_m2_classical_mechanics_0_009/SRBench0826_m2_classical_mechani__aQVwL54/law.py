def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dv_dt from system state variables.

    Variables:
    - t: time
    - x: position
    - v: velocity
    - z: auxiliary state variable
    - e: energy variable
    """
    results = []
    for row in input_data:
        t = row["t"]
        x = row["x"]
        v = row["v"]
        z = row["z"]
        e = row["e"]

        dv_dt = (
            -2.062983824109 * (x * v * v) +
            1.426022064393 * (x * z) +
            0.527800288980 * (v * z) +
            0.483963249282 * (z * e) +
            0.277258417720 * (x * x * v) +
            0.063893164562 * v +
            -0.021212322991 * e +
            0.000117156006 * t +
            -0.214437122620 * x +
            -0.532901638461 * (x * x * x) +
            -0.544844416068 * (x * v) +
            -0.712582400596 * (x * e) +
            -0.256390900304 * (v * e) +
            -0.075329990082 * (v * v) +
            -0.741564554148 * (z * z) +
            -0.767748232406 * (x * x) +
            -1.645534621924 * z
        )

        results.append({"dv_dt": dv_dt})

    return results
