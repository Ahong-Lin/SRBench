def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the rate of change of daughter nuclide population in a decay chain.

    The mathematical model discovered is:
    dNd_dt = 3.441268 + 0.065396*Np - 0.078779*Nd

    This represents a coupled radioactive decay system where:
    - The parent (Np) decays with rate λ_p ≈ 0.0654
    - The daughter (Nd) decays with rate λ_d ≈ 0.0788
    - The daughter accumulates from the parent decay and depletes from its own decay
    - The constant term captures initial conditions/constraints of the system
    """
    results = []
    for row in input_data:
        Np = row['Np']
        Nd = row['Nd']

        # Linear model: dNd_dt = constant + λ_p*Np - λ_d*Nd
        dNd_dt = 3.4412678356 + 0.0653958352 * Np - 0.0787793082 * Nd

        results.append({'dNd_dt': dNd_dt})

    return results
