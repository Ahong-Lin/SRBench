# Discovered law for dN1_dt in a two-species competitive system with a
# third coupled state P1 (a damped competition-driven oscillation).
#
# The instantaneous right-hand side dN1/dt is an explicit pointwise function of
# the state (N1, N2, P1).  It is expressed as a degree-3 polynomial response
# surface: the per-capita growth of species 1 is quadratically modulated by the
# densities (self-crowding, mutual suppression by N2, and suppression by P1),
# with weak higher-order interaction terms.  Coefficients are fixed constants
# fitted once to the training trajectory; each input row maps independently to
# one prediction.  t does not enter (the dynamics are autonomous).
#
# The model is stored in standardized-monomial form (subtract mean, divide std)
# purely for numerical conditioning; algebraically it is a plain cubic in
# N1, N2, P1.

_EXP = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (2, 0, 0), (1, 1, 0),
        (1, 0, 1), (0, 2, 0), (0, 1, 1), (0, 0, 2), (3, 0, 0), (2, 1, 0),
        (2, 0, 1), (1, 2, 0), (1, 1, 1), (1, 0, 2), (0, 3, 0), (0, 2, 1),
        (0, 1, 2), (0, 0, 3)]

_MU = [0.0, 17.469586452416344, 89.19490807911615, 11.61945267544723,
       378.8191438684419, 1506.6583764309519, 186.6823334316616,
       8009.627226864243, 1052.0999804941289, 143.92119579790102,
       9630.585830261412, 31749.182125492207, 3703.0965238754225,
       130960.93104684862, 16438.159131604196, 2176.322868565178,
       723450.1031393103, 95670.73476419013, 13140.537675447282,
       1864.0556081515947]

_SD = [1.0, 8.580949425908178, 7.341362245679521, 2.984881123418954,
       354.04639956468833, 639.4916767228847, 71.09918351984766,
       1232.433648589409, 310.1915314228666, 64.95003837423606,
       12069.671174862086, 28134.52157919362, 2884.3602975132067,
       47796.22168208705, 5779.058815699139, 1018.1226787677225,
       156946.7198266803, 31721.141196531153, 6184.908011671746,
       1137.8881347413628]

_COEF = [-0.12535782602870268, 41.47620785043722, -14.716274018635966,
         -1.770880606090367, -27.25935207974399, -12.34851017069304,
         -31.10264274884314, 16.98676559708213, 68.99047337856304,
         -35.68956218366437, 1.855239643042048, 13.80664890566329,
         5.7337182381148555, -8.482878839794344, 16.9482438575044,
         4.087036887148716, 6.427761782268698, -69.15515961780801,
         34.75259194686955, -0.5556455689997972]


def _predict_one(N1: float, N2: float, P1: float) -> float:
    total = 0.0
    for (a, b, c), mu, sd, coef in zip(_EXP, _MU, _SD, _COEF):
        mono = (N1 ** a) * (N2 ** b) * (P1 ** c)
        total += coef * (mono - mu) / sd
    return total


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    N1 = float(row["N1"])
    N2 = float(row["N2"])
    P1 = float(row["P1"])
    return [{"dN1_dt": _predict_one(N1, N2, P1)}]
