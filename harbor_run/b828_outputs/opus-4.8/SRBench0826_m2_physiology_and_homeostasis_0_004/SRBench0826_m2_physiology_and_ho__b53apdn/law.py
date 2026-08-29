"""
Discovered law for the glucose--insulin regulation experiment.

Scientific target
------------------
The instantaneous right-hand side of the plasma-glucose ODE:

    dG/dt = f(G, Ia)

Although the dataset also reports plasma insulin `I` and time `t`, the reference
`dG_dt` turns out to be an *exact* pointwise function of glucose `G` and insulin
action `Ia` alone (see explain.md).  `I` acts on glucose only indirectly, through
the remote insulin-action compartment `Ia` (whose own law is dIa/dt = 0.2*I - 0.1*Ia).

Functional form
---------------
Grouping by powers of the insulin-action variable Ia:

    dG/dt =  P0(G)              # net glucose appearance (insulin-independent)
           + Ia   * P1(G)       # insulin-action-dependent disposal (leading term)
           + Ia^2 * P2(G)       # saturation correction of insulin action

where each Pk(G) is a cubic polynomial in glucose:

    Pk(G) = c[k,0] + c[k,1]*G + c[k,2]*G^2 + c[k,3]*G^3

The dominant balance is a net appearance term that grows with G and an
insulin-dependent clearance ~ -0.13 * Ia * G (mass-action uptake promoted by
insulin action), plus small higher-order glucose/insulin-action corrections.

All coefficients are fixed constants fitted once to the training data.
The function maps each input row independently to one dG_dt value; it holds
no state, reads no files, and does no ordering/interpolation.
"""

# c[a][b] multiplies  Ia**a * G**b
_C = [
    # Ia^0 : net glucose appearance, insulin-independent
    [0.4217906536965669, 0.015882039407585778, 0.023104323193589422, -0.0023898493676830683],
    # Ia^1 : insulin-action-dependent glucose disposal (leading)
    [-0.1606662876980709, -0.13058352815171126, -0.03268139197911016, 0.0031522394210186534],
    # Ia^2 : saturation / higher-order correction of insulin action
    [0.020741204827366865, -0.005911524430834088, 0.011442183752595095, -0.0006178880217587287],
]


def _dG_dt(G: float, Ia: float) -> float:
    # Horner in G for each insulin-action power, then combine over powers of Ia.
    total = 0.0
    ia_pow = 1.0
    for a in range(len(_C)):
        row = _C[a]
        # polynomial in G (cubic) via Horner
        pg = row[3]
        pg = pg * G + row[2]
        pg = pg * G + row[1]
        pg = pg * G + row[0]
        total += ia_pow * pg
        ia_pow *= Ia
    return total


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map a single-row input list to a single-row output list.

    Each dict must contain keys 'G' and 'Ia' (other keys such as 't', 'I'
    are accepted but not used, since dG/dt depends only on G and Ia).
    """
    out = []
    for row in input_data:
        G = float(row["G"])
        Ia = float(row["Ia"])
        out.append({"dG_dt": _dG_dt(G, Ia)})
    return out


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = [d["dG_dt"] for d in preds]
    import numpy as np

    y = df["dG_dt"].values
    p = np.array(p)
    ss = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
    print("R2", ss, "maxerr", np.max(np.abs(y - p)))
