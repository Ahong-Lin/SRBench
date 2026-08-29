import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dPr_dt from quantum tunneling oscillation parameters.

    Formula: dPr/dt = 6.2164 * |J| * sqrt(1-Pr) * (sin(K*t) + 0.2600*K*t) * N

    where:
    - J: tunneling coupling (can be negative)
    - Pr: probability in one well (0 to 1)
    - K: oscillation frequency/detuning parameter
    - t: time
    - N: damping/coherence factor
    """
    results = []

    for row in input_data:
        t = row['t']
        Pr = row['Pr']
        J = row['J']
        K = row['K']
        N = row['N']

        # Amplitude factor: |J| * sqrt(1-Pr)
        sqrt_1_minus_pr = math.sqrt(1.0 - Pr) if Pr < 1.0 else 0.0

        # Oscillatory component: sin(K*t)
        sin_kt = math.sin(K * t)

        # Linear component: 0.2600 * K * t
        linear_kt = 0.2599931735 * K * t

        # Overall formula: 6.2164 * |J| * sqrt(1-Pr) * (sin(K*t) + 0.2600*K*t) * N
        dpr_dt = 6.2164443305 * abs(J) * sqrt_1_minus_pr * (sin_kt + linear_kt) * N

        results.append({'dPr_dt': dpr_dt})

    return results
