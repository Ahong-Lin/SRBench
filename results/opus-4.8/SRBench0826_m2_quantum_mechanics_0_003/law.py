"""Discovered law for the resonantly driven two-level system.

The rate of change of the excited-state population obeys, to machine
precision on the training data:

    dP/dt = 0.4 * (C - P) - 0.3 * P**2

Only the current population `P` and the coupling/coherence term `C` enter
the law; the inputs `W` and `N` are not needed.
"""

from typing import Dict, List


def law(input_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
    results = []
    for row in input_data:
        P = row["P"]
        C = row["C"]
        dP_dt = 0.4 * (C - P) - 0.3 * P * P
        results.append({"dP_dt": dP_dt})
    return results
