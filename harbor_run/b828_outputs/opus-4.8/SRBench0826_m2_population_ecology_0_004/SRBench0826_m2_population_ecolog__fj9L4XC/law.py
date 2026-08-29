"""Discovered law for dN1_dt.

Two-species competition (N1, N2) with a species-1 specialist enemy P1.

Model (competition + linear predation with a prey refuge):

    dN1/dt = r1 * N1 * (1 - (N1 + a12 * N2) / K1)  -  beta * P1 * (N1 - m)

Equivalently, the explicit pointwise polynomial actually evaluated:

    dN1/dt = c1*N1 + c2*N1^2 + c3*N1*N2 + c4*N1*P1 + c5*P1

with the constants below fitted from the training data. The mapping is
pointwise: each row -> one dN1_dt, using only (N1, N2, P1). (t is not
needed; the law is autonomous.)
"""

# Fitted constants (from /app/data/train_data.csv, least squares).
C1 = 0.5681122726513989    # r1
C2 = -0.005200688445443687  # -r1/K1        (self-crowding)
C3 = -0.0031362356578639415  # -r1*a12/K1   (suppression by N2)
C4 = -0.01951842812319324   # -beta         (predation/attack by P1)
C5 = 0.024884212864812426   # +beta*m       (prey-refuge offset)


def _predict(N1: float, N2: float, P1: float) -> float:
    return C1 * N1 + C2 * N1 * N1 + C3 * N1 * N2 + C4 * N1 * P1 + C5 * P1


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        N1 = row["N1"]
        N2 = row["N2"]
        P1 = row["P1"]
        out.append({"dN1_dt": _predict(N1, N2, P1)})
    return out


if __name__ == "__main__":
    # quick smoke test on the first training row
    print(law([{"t": 0.0, "N1": 20.0, "N2": 60.0, "P1": 5.0}]))  # ~3.7308
