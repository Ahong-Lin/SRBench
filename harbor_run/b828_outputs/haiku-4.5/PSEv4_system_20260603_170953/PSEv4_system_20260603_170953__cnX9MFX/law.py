import numpy as np


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Compute instantaneous acceleration (dv_dt) from position, velocity, and time.

    The discovered law is a driven damped oscillator:
    dv_dt = -2.2799*x - 0.1205*v + periodic_forcing(t)

    where periodic_forcing(t) is a sum of sin/cos terms at multiples of the time variable.
    """
    # Coefficients learned from training data
    coeff_x = -2.2799268420
    coeff_v = -0.1204778392

    # Fourier coefficients for forcing function
    forcing_sin = [1.6778228615, -0.0396714444, 0.3407460396, 0.1149385740, -0.0160820779, -0.0167599818]
    forcing_cos = [-0.3410729555, -0.0108079863, -0.3574580439, -0.0111039699, 0.1026603679, 0.0181069789]

    results = []
    for row in input_data:
        t = row["t"]
        x = row["x"]
        v = row["v"]

        # Main term: -k*x - c*v (spring + damping)
        dv_dt = coeff_x * x + coeff_v * v

        # Periodic forcing: sum of sin/cos terms
        for k in range(1, 7):
            dv_dt += forcing_sin[k-1] * np.sin(k * t) + forcing_cos[k-1] * np.cos(k * t)

        results.append({"dv_dt": float(dv_dt)})

    return results
