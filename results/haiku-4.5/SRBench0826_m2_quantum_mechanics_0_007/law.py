def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Quantum tunneling oscillation law: predicts dPr/dt from system parameters.

    The discovered law models coherent tunneling between degenerate quantum states:
    dPr/dt = K*N - 0.1*Pr + 0.05

    Where:
    - K: tunneling coupling strength
    - N: quantum state population normalization factor
    - Pr: current probability in the second well
    """
    results = []
    for point in input_data:
        K = point['K']
        N = point['N']
        Pr = point['Pr']

        dPr_dt = K * N - 0.1 * Pr + 0.05

        results.append({'dPr_dt': dPr_dt})

    return results
