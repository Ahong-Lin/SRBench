"""Discovered law for diffusion-limited association rate vs. viscosity.

The effective bimolecular association rate `kon` decreases with solution
viscosity `eta` following a power-scaling behavior. The data are described to
R^2 = 0.99999 by a sum of two power laws:

    kon(eta) = A * eta^(-p) + B * eta^(-q)

A dominant power term (exponent ~0.57) governs the fall-off near the reference
viscosity, while a shallow power term (exponent ~0.14) sustains the slow decay
at high viscosity. Parameters were fit on /app/data/train_data.csv.
"""

# Fitted constants (nonlinear least squares on the training data).
A = 0.6422741314385214
P = 0.574189253601773
B = 0.0796516843746969
Q = 0.14098796468535632


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    eta = row["eta"]
    kon = A * eta ** (-P) + B * eta ** (-Q)
    return [{"kon": kon}]
