import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dNd_dt for a radioactive decay chain using the discovered mathematical law.

    The law models the rate of change of daughter nuclei population in a parent-daughter
    decay chain where both populations evolve simultaneously.

    Law: dNd_dt = λ_p * Np - λ_d * Nd + A * exp(-k * t)

    Where:
    - λ_p = 0.0591514665 (parent decay constant)
    - λ_d = 0.0868585518 (daughter decay constant)
    - A = 70.6641303820 (initial conditions amplitude)
    - k = 0.0425 (exponential decay rate of initial conditions effect)
    """

    # Physical parameters discovered from data
    lambda_p = 0.0591514665  # Parent decay rate
    lambda_d = 0.0868585518  # Daughter decay rate
    A = 70.6641303820        # Initial conditions amplitude
    k = 0.0425               # Exponential decay rate

    results = []
    for data_point in input_data:
        t = data_point['t']
        Np = data_point['Np']
        Nd = data_point['Nd']

        # Calculate dNd_dt using the discovered law
        dNd_dt = (lambda_p * Np
                  - lambda_d * Nd
                  + A * math.exp(-k * t))

        results.append({'dNd_dt': dNd_dt})

    return results
