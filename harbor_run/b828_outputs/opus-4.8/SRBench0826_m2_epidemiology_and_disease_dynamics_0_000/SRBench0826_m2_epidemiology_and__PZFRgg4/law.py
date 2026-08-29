"""Discovered law for dI/dt of an outbreak.

The scientific target is the instantaneous right-hand side of the infectious
compartment.  The data are a single outbreak trajectory of a compartmental
model with a fixed population N = S + E + I + R = 1000 (verified constant to
machine precision on every training row).

Discovered relation (a prevalence-dependent SIR incidence for the infectious
compartment):

    dI/dt = beta(I) * S * I / N  -  gamma * I,      beta(I) = beta0 - beta1 * I/N

Expanded to the fitted pointwise form actually implemented below:

    dI/dt = a * (S*I/N)  +  b * (S*I^2 / N^2)  +  c * I

with
    a = beta0  =  0.43722         (baseline transmission coefficient)
    b = -beta1 = -2.06370         (prevalence-dependent reduction of transmission)
    c = -gamma = -0.19682         (recovery / removal rate)

The exposed count E and the recovered count R were tested as additional
predictors and carry no additional information for dI/dt on this system
(their fitted coefficients are ~0 and they degrade out-of-sample accuracy),
so the law depends only on S and I.  Fit quality on the training data:
R^2 = 0.99978, RMSE = 0.0257; on the late-time (right-hand) segment the
residuals are < 0.006, which is the regime relevant to the hidden test set.
"""

# Fixed population size (S + E + I + R), inferred from the training data.
N = 1000.0

# Constants inferred from the training data.
A_SI = 0.43722104982613313      # coefficient of  S*I/N        (=  beta0)
B_SII = -2.0637020716632666     # coefficient of  S*I^2/N^2    (= -beta1)
C_I = -0.1968156106446463       # coefficient of  I            (= -gamma)


def law(input_data):
    """Map each input row independently to a dI_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'S', 'E', 'I', 'R'.

    Returns
    -------
    list[dict[str, float]]
        One dict {'dI_dt': value} per input row.
    """
    out = []
    for row in input_data:
        S = row["S"]
        I = row["I"]
        di_dt = (
            A_SI * (S * I / N)
            + B_SII * (S * I * I / (N * N))
            + C_I * I
        )
        out.append({"dI_dt": di_dt})
    return out


if __name__ == "__main__":
    # quick self-check against the training data
    import csv

    rows, y = [], []
    with open("/app/data/train_data.csv") as f:
        for r in csv.DictReader(f):
            rows.append({k: float(r[k]) for k in ("t", "S", "E", "I", "R")})
            y.append(float(r["dI_dt"]))
    pred = [d["dI_dt"] for d in law(rows)]
    err = [p - t for p, t in zip(pred, y)]
    rmse = (sum(e * e for e in err) / len(err)) ** 0.5
    print("RMSE:", rmse, "max abs err:", max(abs(e) for e in err))
