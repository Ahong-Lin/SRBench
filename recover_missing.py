"""Recreate the six recoverable submissions from their recorded trajectories."""

from __future__ import annotations

import base64
import json
import math
import pathlib
import struct
import zlib

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures


ROOT = pathlib.Path("outputs/bio_phys_30_gpt56sol_20260921")
EVAL = ROOT / "04_evaluations/gpt56sol_20260922_55x3"
PLOT = ROOT / "03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3"
PACK = ROOT / "02_packaged/20260922"


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "aggregated_output" and isinstance(item, str):
                yield item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def codex_outputs(trial: str) -> list[str]:
    path = EVAL / trial / "agent/codex.txt"
    outputs = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            outputs.extend(_walk(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return outputs


def write_submission(task: str, run: str, trial: str, law: str, explain: str) -> None:
    folder = PLOT / task / "solutions" / f"{run}_{trial}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "law.py").write_text(law)
    (folder / "explain.md").write_text(explain)


def biology005() -> None:
    task = "biology_005"
    trial = "task__42bwm9S"
    data = pd.read_csv(PACK / task / "task/environment/train_data.csv")
    raw = np.log10(data.iloc[:, :3].to_numpy())
    lo = np.array([-2.0, 2.0, math.log10(0.02)])
    hi = np.array([math.log10(200.0), 4.0, math.log10(200.0)])
    x = 2.0 * (raw - lo) / (hi - lo) - 1.0
    y = np.log(data.A.to_numpy() / (0.9 - data.A.to_numpy()))
    poly = PolynomialFeatures(16)
    design = poly.fit_transform(x)
    model = Ridge(alpha=1e-9, fit_intercept=False).fit(design, y)
    blob = base64.b85encode(zlib.compress(model.coef_.astype("<f8").tobytes(), 9)).decode()
    law = f'''"""Deterministic fitted law for ligand/receptor/competitor activity."""

import base64
import itertools
import math
import struct
import zlib

_COEFF_DATA = {blob!r}
_COEFFS = struct.unpack("<969d", zlib.decompress(base64.b85decode(_COEFF_DATA.encode("ascii"))))
_LOG_LO = (-2.0, 2.0, -1.6989700043360187)
_LOG_HI = (2.3010299956639813, 4.0, 2.3010299956639813)


def _predict(row):
    values = (float(row["L"]), float(row["R_tot"]), float(row["C_competitor"]))
    x = tuple(2.0 * (math.log10(value) - low) / (high - low) - 1.0
              for value, low, high in zip(values, _LOG_LO, _LOG_HI))
    score = _COEFFS[0]
    index = 1
    for degree in range(1, 17):
        for factors in itertools.combinations_with_replacement(range(3), degree):
            term = 1.0
            for factor in factors:
                term *= x[factor]
            score += _COEFFS[index] * term
            index += 1
    if score >= 0.0:
        e = math.exp(-score)
        return 0.9 / (1.0 + e)
    e = math.exp(score)
    return 0.9 * e / (1.0 + e)


def law(rows):
    return [_predict(row) for row in rows]
'''
    explain = "# Recovered fitted law\n\nThe recorded trajectory fit a degree-16 polynomial in scaled log-odds coordinates.\n"
    write_submission(task, "run_03", trial, law, explain)


def gng_blob() -> str:
    candidates = [x for x in codex_outputs("task__GNG3Gvu") if "B85 " in x]
    if not candidates:
        raise RuntimeError("translation B-spline blob is absent from the trajectory")
    return max(candidates, key=len).split("B85 ", 1)[1].strip().splitlines()[0]


def biology010() -> None:
    task = "biology_010"
    trial = "task__GNG3Gvu"
    blob = gng_blob()
    law = f'''"""Deterministic fitted law for the translation response."""

import base64
import struct
import zlib

_NA = 35
_NG = 40
_DEGREE = 3
_PACKED = {blob!r}
_RAW = zlib.decompress(base64.b85decode(_PACKED))
_COEF = struct.unpack("<1400d", _RAW)


def _basis(value, scale, count):
    x = min(1.0, max(0.0, float(value) / scale))
    intervals = count - _DEGREE
    knots = ([0.0] * (_DEGREE + 1)
             + [i / intervals for i in range(1, intervals)]
             + [1.0] * (_DEGREE + 1))
    values = [0.0] * (len(knots) - 1)
    if x == 1.0:
        values[count - 1] = 1.0
    else:
        for i in range(len(values)):
            if knots[i] <= x < knots[i + 1]:
                values[i] = 1.0
                break
    for degree in range(1, _DEGREE + 1):
        next_values = [0.0] * (len(values) - 1)
        for i in range(len(next_values)):
            left_den = knots[i + degree] - knots[i]
            right_den = knots[i + degree + 1] - knots[i + 1]
            if left_den:
                next_values[i] += (x - knots[i]) / left_den * values[i]
            if right_den:
                next_values[i] += (knots[i + degree + 1] - x) / right_den * values[i + 1]
        values = next_values
    return values[:count]


def law(rows):
    predictions = []
    for row in rows:
        a = float(row["A"])
        g = float(row["G"])
        envelope = 100.0 * a * a / (4.0 + a * a)
        if a > 7.0 and g > 20.5:
            predictions.append(float(envelope))
            continue
        ba = _basis(a, 10.0, _NA)
        bg = _basis(g, 30.0, _NG)
        total = 0.0
        for i, ai in enumerate(ba):
            if ai:
                offset = i * _NG
                for j, gj in enumerate(bg):
                    if gj:
                        total += ai * gj * _COEF[offset + j]
        predictions.append(float(min(envelope, max(0.0, total))))
    return predictions
'''
    explain = "# Recovered fitted law\n\nA tensor-product cubic B-spline was fit to the recorded two-input response.\n"
    write_submission(task, "run_02", trial, law, explain)


def physics004() -> None:
    task = "physics_004"
    trial = "task__wShKkmQ"
    data = pd.read_csv(PACK / task / "task/environment/train_data.csv")
    r = data.r_p.to_numpy()
    m_dot = data.m_dot.to_numpy()
    x = m_dot * np.sqrt(data.T0.to_numpy()) / (data.p0.to_numpy() * data.A.to_numpy())
    z = np.column_stack([
        (np.log10(data.p0.to_numpy()) - 2.0) / 2.0,
        (np.log10(data.T0.to_numpy()) - math.log10(800.0)) /
        (math.log10(5000.0) - math.log10(800.0)),
        (np.log10(data.A.to_numpy()) + 6.0) / 3.0,
    ])
    pc = PolynomialFeatures(7)
    xc = pc.fit_transform(z)
    bc = np.linalg.lstsq(xc[r < 0.48], x[r < 0.48], rcond=None)[0]

    def factor(gamma, ratio):
        critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
        if ratio <= critical:
            return 1.0
        fc = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
        unchoked = math.sqrt(max(0.0, 2.0 / (gamma - 1.0) *
            (ratio ** (2.0 / gamma) - ratio ** ((gamma + 1.0) / gamma))))
        return unchoked / fc

    # Infer gamma from the unchoked rows, matching the recorded bracketing fit.
    from scipy.optimize import brentq
    capacity = xc @ bc
    use = np.where(r > 0.72)[0]
    gammas = []
    kept = []
    for i in use:
        q = x[i] / capacity[i]
        try:
            g = brentq(lambda value: factor(value, r[i]) - q, 1.05, 2.5)
        except ValueError:
            continue
        kept.append(i)
        gammas.append(g)
    kept = np.asarray(kept, dtype=int)
    pg = PolynomialFeatures(6)
    xg = pg.fit_transform(z)
    bg = np.linalg.lstsq(xg[kept], np.asarray(gammas), rcond=None)[0]

    def fmt(values):
        return repr([float(v) for v in values.tolist()])

    law = f'''"""Calibrated compressible-flow law inferred from the observations."""

import math

_C_COEF = {fmt(bc)}
_G_COEF = {fmt(bg)}


def _poly3(x, y, z, degree, coef):
    xp = [1.0]
    yp = [1.0]
    zp = [1.0]
    for _ in range(degree):
        xp.append(xp[-1] * x)
        yp.append(yp[-1] * y)
        zp.append(zp[-1] * z)
    value = 0.0
    k = 0
    for total in range(degree + 1):
        for px in range(total, -1, -1):
            rest = total - px
            for py in range(rest, -1, -1):
                pz = rest - py
                value += coef[k] * xp[px] * yp[py] * zp[pz]
                k += 1
    return value


def law(rows):
    predictions = []
    log_t_span = math.log10(5000.0) - math.log10(800.0)
    for row in rows:
        p0 = float(row["p0"])
        t0 = float(row["T0"])
        area = float(row["A"])
        ratio = float(row["r_p"])
        u = (math.log10(p0) - 2.0) / 2.0
        v = (math.log10(t0) - math.log10(800.0)) / log_t_span
        w = (math.log10(area) + 6.0) / 3.0
        capacity = _poly3(u, v, w, 7, _C_COEF)
        gamma = _poly3(u, v, w, 6, _G_COEF)
        critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
        if ratio <= critical:
            ratio_factor = 1.0
        else:
            fc = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
            unchoked = math.sqrt(max(0.0, 2.0 / (gamma - 1.0) *
                (ratio ** (2.0 / gamma) - ratio ** ((gamma + 1.0) / gamma))))
            ratio_factor = unchoked / fc
        predictions.append(float(capacity * ratio_factor * p0 * area / math.sqrt(t0)))
    return predictions
'''
    explain = "# Recovered fitted law\n\nThe trajectory used an isentropic choked/unchoked flow law with polynomially calibrated capacity and gamma.\n"
    write_submission(task, "run_01", trial, law, explain)


def physics009_run01() -> None:
    task = "physics_009"
    trial = "task__vDVXSdD"
    data = pd.read_csv(PACK / task / "task/environment/train_data.csv")
    hbar = 1.054571817e-34
    e0 = math.pi ** 2 * hbar ** 2 * data.n.to_numpy() ** 2 / (2.0 * data.m.to_numpy() * data.L.to_numpy() ** 2)
    q = data.En.to_numpy() / e0
    x = np.column_stack([
        (data.L.to_numpy() - 3e-11) / 2e-11,
        (data.m.to_numpy() - 9.1e-31) / 0.92e-31,
        (data.barrier_softness.to_numpy() - 4.1e6) / 0.6e6,
    ])
    exps = []
    for total in range(11):
        for a in range(total + 1):
            for b in range(total - a + 1):
                exps.append((a, b, total - a - b))
    design = np.asarray([[u ** a * v ** b * w ** c for a, b, c in exps]
                         for u, v, w in x])
    coefficients = []
    for level in range(1, 9):
        mask = data.n.to_numpy() == level
        coefficients.append(np.linalg.lstsq(design[mask], q[mask], rcond=1e-11)[0])
    packed = struct.pack("<2288d", *(float(v) for row in coefficients for v in row))
    blob = base64.b85encode(zlib.compress(packed, 9)).decode()
    law = f'''"""Deterministic surrogate for the inferred soft-wall energy law."""

import base64
import math
import struct
import zlib

_BLOB = {blob!r}
_FLAT = struct.unpack("<2288d", zlib.decompress(base64.b85decode(_BLOB)))
_COEFS = tuple(_FLAT[i * 286:(i + 1) * 286] for i in range(8))
_HBAR = 1.054571817e-34


def _correction(level, length, mass, softness):
    x = (length - 3.0e-11) / 2.0e-11
    y = (mass - 9.1e-31) / 0.92e-31
    z = (softness - 4.1e6) / 0.6e6
    xp = [1.0]
    yp = [1.0]
    zp = [1.0]
    for _ in range(10):
        xp.append(xp[-1] * x)
        yp.append(yp[-1] * y)
        zp.append(zp[-1] * z)
    coeff = _COEFS[min(8, max(1, level)) - 1]
    value = 0.0
    k = 0
    for total in range(11):
        for a in range(total + 1):
            for b in range(total - a + 1):
                c = total - a - b
                value += coeff[k] * xp[a] * yp[b] * zp[c]
                k += 1
    return value


def law(rows):
    predictions = []
    for row in rows:
        n = float(row["n"])
        length = float(row["L"])
        mass = float(row["m"])
        softness = float(row["barrier_softness"])
        level = int(round(n))
        infinite_box = math.pi * math.pi * _HBAR * _HBAR * n * n / (2.0 * mass * length * length)
        predictions.append(float(infinite_box * _correction(level, length, mass, softness)))
    return predictions
'''
    explain = "# Recovered fitted law\n\nThe trajectory fitted a level-specific degree-10 polynomial correction to the infinite-well energy.\n"
    write_submission(task, "run_01", trial, law, explain)


def physics009_run03() -> None:
    task = "physics_009"
    trial = "task__UMz7XFm"
    outputs = [x for x in codex_outputs(trial) if "285 2280" in x]
    if not outputs:
        raise RuntimeError("soft-wall Chebyshev blob is absent from the trajectory")
    blob = max(outputs, key=len).splitlines()[1].strip()
    law = f'''"""Deterministic fitted governing law for the soft-wall energy data."""

import base64
import math
import struct

_HBAR = 1.054571817e-34
_SCALE = math.pi * math.pi * _HBAR * _HBAR / 2.0
_BOUNDS = ((1.0e-11, 5.0e-11), (8.1984e-31, 1.00204e-30), (3.5e6, 4.7e6))
_TERMS = tuple((i, j, k) for i in range(17) for j in range(9) for k in range(9)
               if i + 2 * j + 2 * k <= 16)
_BLOB = {blob!r}
_PACKED = base64.b85decode(_BLOB)
_COEF = struct.unpack("<" + "d" * (len(_PACKED) // 8), _PACKED)


def _chebyshev_values(value, bounds, degree):
    lower, upper = bounds
    x = 2.0 * (math.log(value) - math.log(lower)) / (math.log(upper) - math.log(lower)) - 1.0
    values = [1.0, x]
    for _ in range(2, degree + 1):
        values.append(2.0 * x * values[-1] - values[-2])
    return values


def law(rows):
    predictions = []
    width = len(_TERMS)
    for row in rows:
        n = int(round(float(row["n"])))
        length = float(row["L"])
        mass = float(row["m"])
        softness = float(row["barrier_softness"])
        level = min(8, max(1, n))
        tl = _chebyshev_values(length, _BOUNDS[0], 16)
        tm = _chebyshev_values(mass, _BOUNDS[1], 8)
        ts = _chebyshev_values(softness, _BOUNDS[2], 8)
        offset = (level - 1) * width
        correction = math.fsum(_COEF[offset + q] * tl[i] * tm[j] * ts[k]
                               for q, (i, j, k) in enumerate(_TERMS))
        predictions.append(float(_SCALE * n * n * correction / (mass * length * length)))
    return predictions
'''
    explain = "# Recovered fitted law\n\nThe trajectory used a Chebyshev expansion of a soft-wall correction to the box spectrum.\n"
    write_submission(task, "run_03", trial, law, explain)


def physics017() -> None:
    task = "physics_017"
    trial = "task__t28woao"
    outputs = [x for x in codex_outputs(trial) if len(x) > 40000]
    if not outputs:
        raise RuntimeError("transition ensemble blob is absent from the trajectory")
    blob = max(outputs, key=len).strip()
    law = f'''"""Fitted governing response for the transition experiment."""

import base64
import math
import struct
import zlib

_BLOB = {blob!r}


def _unpack_models():
    raw = zlib.decompress(base64.b85decode(_BLOB))
    return struct.unpack("<%df" % (len(raw) // 4), raw)


_P = _unpack_models()
del _BLOB


def _predict_with(row, pos):
    x = [(float(row["L"]) - _P[0]) / _P[4],
         (float(row["E_nu"]) - _P[1]) / _P[5],
         (float(row["theta_mix"]) - _P[2]) / _P[6],
         (float(row["delta_m2"]) - _P[3]) / _P[7]]
    for n_in, n_out, nonlinear in ((4, 50, True), (50, 50, True),
                                    (50, 50, True), (50, 1, False)):
        weights = pos
        biases = weights + n_in * n_out
        out = []
        for j in range(n_out):
            value = _P[biases + j]
            for i, xi in enumerate(x):
                value += xi * _P[weights + i * n_out + j]
            out.append(math.tanh(value) if nonlinear else value)
        x = out
        pos = biases + n_out
    return x[0]


def law(rows):
    return [float(0.5 * (_predict_with(row, 8) + _predict_with(row, 5409))) for row in rows]
'''
    explain = "# Recovered fitted law\n\nThe trajectory submitted an ensemble of two smooth tanh networks fit to the four-input response.\n"
    write_submission(task, "run_02", trial, law, explain)


if __name__ == "__main__":
    biology005()
    biology010()
    physics004()
    physics009_run01()
    physics009_run03()
    physics017()
    print("recovered six submissions")
