import math

# Discovered law for the Brier vs. log-compute scaling relationship.
#
#   Brier(logC) = baseline(logC) + sum_i  G_i * exp(-((logC - mu_i)^2) / (2*s_i^2))
#
# where the smooth compute-scaling baseline is
#
#   baseline(logC) = c + A * exp(k * logC) + B * logC
#
# This is a gentle, slightly-super-linear "valley" in compute (a shallow,
# roughly-linear improvement on the low-compute side that turns into an
# accelerating exp-like increase on the high-compute side) on top of which sit
# a few *localized* Gaussian effects:
#   * a large calibration bump centred near logC = -1,
#   * two smaller localized features on the high-compute side (~1.75, ~2.29),
#   * a tiny broad correction near logC = -1.2.
#
# Parameters were obtained by non-linear least squares (scipy.curve_fit) on the
# full training set. Fit quality on training data: RMSE ~5.6e-5, max abs err ~3.5e-4.

# baseline params: c, A, k, B
_C = 0.07403
_A = 0.07420
_K = 0.68496
_B = -0.05971

# Gaussian bumps: (amplitude, center, sigma)
_GAUSSIANS = [
    (0.20027, -1.00028, 0.35376),
    (0.03193, 1.75338, 0.36930),
    (0.04693, 2.28638, 0.59103),
    (-0.00519, -1.20909, 0.77997),
]


def _predict(logc: float) -> float:
    val = _C + _A * math.exp(_K * logc) + _B * logc
    for amp, mu, sigma in _GAUSSIANS:
        val += amp * math.exp(-((logc - mu) ** 2) / (2.0 * sigma * sigma))
    return val


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return one `{"Brier": value}` prediction for every input row."""
    return [{"Brier": _predict(float(row["logC"]))} for row in input_data]


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = [d["Brier"] for d in preds]
    err = [pi - yi for pi, yi in zip(p, df["Brier"].tolist())]
    rmse = (sum(e * e for e in err) / len(err)) ** 0.5
    print("RMSE", rmse, "max", max(abs(e) for e in err))
