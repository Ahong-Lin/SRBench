import numpy as np

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dI_dt for a seasonally forced SIR model with periodic environmental forcing.

    The discovered law: A modified SIR dynamic with sinusoidal seasonal modulation
    of transmission rate, capturing yearly environmental cycles affecting
    disease transmissibility.
    """
    # Fitted coefficients from training data analysis
    c0 = 0.09965705486408948
    c_s = -0.0931335905513247
    c_i = -6.173050647478066
    c_si = 10.206908263691092
    c_si_cos = 0.844027310709899
    c_si_sin = -0.18697809821595995
    c_i_cos = 0.03247918107828856
    c_i_sin = 0.1394702045522766

    omega = 2 * np.pi  # Annual forcing frequency (period = 1 year)

    results = []
    for row in input_data:
        t = row['t']
        S = row['S']
        I = row['I']

        # Compute seasonal forcing terms
        cos_t = np.cos(omega * t)
        sin_t = np.sin(omega * t)

        # Linear combination of terms capturing:
        # - Baseline SIR dynamics (c_si*S*I - c_i*I)
        # - Seasonal modulation of transmission (S*I*cos and sin terms)
        # - Weak seasonal modulation of recovery (I*cos and sin terms)
        dI_dt = (
            c0
            + c_s * S
            + c_i * I
            + c_si * S * I
            + c_si_cos * S * I * cos_t
            + c_si_sin * S * I * sin_t
            + c_i_cos * I * cos_t
            + c_i_sin * I * sin_t
        )

        results.append({'dI_dt': float(dI_dt)})

    return results
