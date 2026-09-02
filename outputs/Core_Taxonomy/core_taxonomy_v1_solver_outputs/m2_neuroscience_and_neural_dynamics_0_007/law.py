"""Symbolic-regression law for the coupled-oscillator synchronization dataset.

The synchronization order parameter ``r`` is modeled as an explicit closed-form
Pade (rational) function of the coupling strength ``K``:

        r(K) = N(K) / D(K)

with

    N(K) = n0 + n1*K + n2*K^2 + n3*K^3 + n4*K^4
    D(K) = 1  + d1*K + d2*K^2 + d3*K^3 + d4*K^4

This form reproduces the three qualitative regimes of the collective phase-locking
transition:
  * a slow, near-linear onset at small coupling,
  * the steep rise through the transition region (K ~ 1-2),
  * the sub-unity saturation of the order parameter, with asymptote
    n4/d4 ~ 0.871 as K -> infinity.

The denominator has no real roots, so r(K) is smooth and pole-free for all K > 0,
and the fitted function is monotonically increasing over the measured range.
"""

# Fitted coefficients (least-squares over the full training set).
_NUM = (
    0.009370361818116818,   # n0
    0.03871992956912281,    # n1
    -0.04683712758621571,   # n2
    0.03779172871280115,    # n3
    0.14488039096464023,    # n4
)
_DEN = (
    1.0,                    # d0 (fixed to 1)
    -0.4955171941342682,    # d1
    0.39837994613991384,    # d2
    0.061400738068177495,   # d3
    0.1663442418112621,     # d4
)


def _poly(coeffs, x):
    """Evaluate a polynomial with the given ascending-order coefficients."""
    acc = 0.0
    for c in reversed(coeffs):
        acc = acc * x + c
    return acc


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    K = float(row["K"])
    r = _poly(_NUM, K) / _poly(_DEN, K)
    return [{"r": r}]
