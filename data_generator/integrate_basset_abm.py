"""
分数阶 Adams–Bashforth–Moulton 预估-校正法求解 Basset (BBO) 方程。
====================================================================

sphere-in-fluid 进化谱系 gen5 的方程含 Basset 历史力，是积分-微分方程。
利用恒等式

    ∫_0^t v'(τ)/sqrt(t-τ) dτ = sqrt(pi) * D^{1/2} v(t)          (Caputo 1/2 阶导)

整条方程是一个含 1 阶与 1/2 阶导的多项分数阶微分方程：

    M D^1 v + K_B*sqrt(pi) D^{1/2} v = G - b_K|v|^(n_pl-1)v - c_q|v|v
    M = m + C_a*rho_f*V_s,   G = (m - rho_f*V_s)*g

化为 α = 1/2 的同阶(commensurate)系统，令 y0 = v, y1 = D^{1/2} v：

    D^{1/2} y0 = y1
    D^{1/2} y1 = (G - drag(y0) - K_B*sqrt(pi)*y1) / M

用 Diethelm–Ford–Freed 分数阶 Adams–Bashforth–Moulton 预估-校正(PECE)算法求解，
收敛阶 min(2, 1+α) = 1.5，是分数阶微分方程的标准数值方法（非标准 ODE 求解器）。

预估(分数阶 Adams-Bashforth):
    y^P_{n+1} = y0 + 1/Γ(α) * Σ_{j=0}^{n} b_{j,n+1} f_j
    b_{j,n+1} = h^α/α * [(n+1-j)^α - (n-j)^α]
校正(分数阶 Adams-Moulton):
    y_{n+1} = y0 + h^α/Γ(α+2) * [ f(t_{n+1}, y^P_{n+1}) + Σ_{j=0}^{n} a_{j,n+1} f_j ]
    a_{0,n+1}   = n^{α+1} - (n-α)(n+1)^α
    a_{j,n+1}   = (n-j+2)^{α+1} + (n-j)^{α+1} - 2(n-j+1)^{α+1},  1≤j≤n

用法
----
    # 开箱即用，生成 5000 个点 + 画图
    python integrate_basset_abm.py --n 5000 --plot

    # 改参数 / 区间 / 校正迭代次数
    python integrate_basset_abm.py \
        --params "K_B=0.5, n_pl=0.8, c_q=0.1" --t1 8 --n 5000 --corrector-iters 2 --plot

    # 自检（跑两个解析解验证，不生成数据）
    python integrate_basset_abm.py --selftest

输出
----
    outputs/ode_data/basset_abm_{timestamp}.csv     列: t, v[, v_noisy]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.special import gamma, erfc


# ============================================================
# 默认参数
# ============================================================

DEFAULT_PARAMS = {
    "m": 0.05,        # 球质量 (kg)
    "g": 9.81,        # 重力加速度 (m/s^2)
    "rho_f": 1000.0,  # 流体密度 (kg/m^3)
    "V_s": 4e-5,      # 球体积 (m^3)
    "C_a": 0.5,       # 附加质量系数
    "c_q": 0.1,       # 二次（形阻）系数
    "b_K": 0.8,       # 广义 Stokes 阻力系数（n_pl=1 时为线性 b）
    "n_pl": 1.0,      # 幂律指数
    "K_B": 0.5,       # Basset 历史力系数
}

ALPHA = 0.5


# ============================================================
# 分数阶 ABM 预估-校正核（同阶系统 D^α y = f(t, y)）
# ============================================================

def _w_predictor(n: int, alpha: float, ha: float) -> np.ndarray:
    jj = np.arange(0, n + 1, dtype=float)
    return (ha / alpha) * ((n + 1 - jj) ** alpha - (n - jj) ** alpha)


def _w_corrector(n: int, alpha: float) -> np.ndarray:
    a = np.empty(n + 1)
    nf = float(n)
    a[0] = nf ** (alpha + 1) - (nf - alpha) * (nf + 1) ** alpha
    if n >= 1:
        j = np.arange(1, n + 1, dtype=float)
        a[1:] = ((nf - j + 2) ** (alpha + 1)
                 + (nf - j) ** (alpha + 1)
                 - 2 * (nf - j + 1) ** (alpha + 1))
    return a


def frac_pece(alpha, f, y0_vec, t, corrector_iters: int = 1) -> np.ndarray:
    """
    Diethelm–Ford–Freed 分数阶 Adams PECE，求解 D^α y = f(t, y)，0<α<1。
    y0_vec: 初值向量 (d,)；返回 Y 形状 (len(t), d)。
    """
    N = len(t)
    h = t[1] - t[0]
    ha = h ** alpha
    ga = gamma(alpha)
    ga2 = gamma(alpha + 2)
    y0_vec = np.asarray(y0_vec, dtype=float)
    d = y0_vec.size

    Y = np.zeros((N, d))
    F = np.zeros((N, d))
    Y[0] = y0_vec
    F[0] = f(t[0], Y[0])

    for n in range(N - 1):
        b = _w_predictor(n, alpha, ha)            # (n+1,)
        yP = y0_vec + (b @ F[:n + 1]) / ga        # (d,)
        a = _w_corrector(n, alpha)                # (n+1,)
        hist = a @ F[:n + 1]                       # (d,)
        fP = f(t[n + 1], yP)
        y_new = y0_vec + (ha / ga2) * (fP + hist)
        for _ in range(corrector_iters - 1):
            fC = f(t[n + 1], y_new)
            y_new = y0_vec + (ha / ga2) * (fC + hist)
        Y[n + 1] = y_new
        F[n + 1] = f(t[n + 1], Y[n + 1])
    return Y


# ============================================================
# Basset 物理：构造同阶系统的 f
# ============================================================

def _make_basset_f(params: dict):
    m, g = params["m"], params["g"]
    rho_f, V_s, C_a = params["rho_f"], params["V_s"], params["C_a"]
    c_q, b_K, n_pl, K_B = params["c_q"], params["b_K"], params["n_pl"], params["K_B"]
    M = m + C_a * rho_f * V_s
    G = (m - rho_f * V_s) * g
    if M <= 0:
        raise SystemExit(f"有效惯性 M={M:g} 必须 > 0")
    KB_sqrt_pi = K_B * np.sqrt(np.pi)

    def drag(v: float) -> float:
        av = abs(v)
        if av == 0.0:
            stokes = 0.0
        else:
            stokes = b_K * av ** (n_pl - 1.0) * v
        return stokes + c_q * av * v

    def f(_t, y):
        y0, y1 = y[0], y[1]
        f0 = y1
        f1 = (G - drag(y0) - KB_sqrt_pi * y1) / M
        return np.array([f0, f1])

    return f, M, G


def _analytic_linear(params: dict, v0: float):
    """K_B=0, n_pl=1, c_q=0 时退化为线性 ODE，给闭式解验证。"""
    if params["K_B"] != 0 or params["n_pl"] != 1.0 or params["c_q"] != 0:
        return None
    m, g = params["m"], params["g"]
    rho_f, V_s, C_a, b_K = params["rho_f"], params["V_s"], params["C_a"], params["b_K"]
    M = m + C_a * rho_f * V_s
    G = (m - rho_f * V_s) * g
    if b_K == 0:
        return None
    v_inf = G / b_K
    tau = M / b_K
    return (lambda tt: v_inf + (v0 - v_inf) * np.exp(-tt / tau)), v_inf


# ============================================================
# 自检：两个有解析解的测试
# ============================================================

def _selftest() -> None:
    print("=" * 64, file=sys.stderr)
    print("自检 1: Mittag-Leffler  D^{1/2}y = -y, y(0)=1  ->  y=e^t·erfc(√t)",
          file=sys.stderr)
    for N in (1000, 5000):
        t = np.linspace(0, 3, N)
        Y = frac_pece(ALPHA, lambda _t, y: np.array([-y[0]]), [1.0], t)
        exact = np.exp(t) * erfc(np.sqrt(t))
        err = float(np.max(np.abs(Y[:, 0] - exact)))
        print(f"   N={N:>5}: 最大误差 = {err:.3e}", file=sys.stderr)

    print("自检 2: Basset 退化 (K_B=0,n_pl=1,c_q=0) 对比线性指数解", file=sys.stderr)
    params = dict(DEFAULT_PARAMS, K_B=0.0, n_pl=1.0, c_q=0.0)
    f, M, G = _make_basset_f(params)
    lin = _analytic_linear(params, 0.0)
    for N in (1000, 5000):
        t = np.linspace(0, 10, N)
        Y = frac_pece(ALPHA, f, [0.0, 0.0], t)
        exact = lin[0](t)
        err = float(np.max(np.abs(Y[:, 0] - exact)))
        print(f"   N={N:>5}: v_inf={lin[1]:.6g}, 最大误差 = {err:.3e}", file=sys.stderr)
    print("=" * 64, file=sys.stderr)


# ============================================================
# Main
# ============================================================

def _parse_params(text, defaults):
    params = dict(defaults)
    if not text:
        return params
    for chunk in text.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise SystemExit(f"参数格式错误（应为 name=value）: '{chunk}'")
        name, val = chunk.split("=", 1)
        name = name.strip()
        if name not in defaults:
            raise SystemExit(f"未知参数 '{name}'（可用: {', '.join(defaults)}）")
        try:
            params[name] = float(val.strip())
        except ValueError:
            raise SystemExit(f"参数值不是数字: '{chunk}'")
    return params


def main() -> None:
    p = argparse.ArgumentParser(
        description="分数阶 ABM 预估-校正法求解 Basset 方程",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--params", default=None,
                   help="参数赋值（未给的用默认），如 'K_B=0.5, n_pl=0.8'")
    p.add_argument("--t0", type=float, default=0.0)
    p.add_argument("--t1", type=float, default=5.0)
    p.add_argument("--n", type=int, default=5000, help="均匀网格点数（默认 5000）")
    p.add_argument("--y0", type=float, default=0.0, help="初速 v(0)（从静止=0）")
    p.add_argument("--corrector-iters", type=int, default=1,
                   help="校正迭代次数（PECE=1, P(EC)^k E = k）")
    p.add_argument("--noise", type=float, default=0.0,
                   help="相对高斯噪声标准差，>0 时额外输出带噪列")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--plot", action="store_true")
    p.add_argument("--selftest", action="store_true",
                   help="只跑解析解验证，不生成数据")
    args = p.parse_args()

    if args.selftest:
        _selftest()
        return

    if args.t1 <= args.t0:
        raise SystemExit("--t1 必须大于 --t0")
    if args.n < 3:
        raise SystemExit("--n 至少为 3")
    if args.corrector_iters < 1:
        raise SystemExit("--corrector-iters 至少为 1")

    params = _parse_params(args.params, DEFAULT_PARAMS)
    f, M, G = _make_basset_f(params)

    print("=" * 64, file=sys.stderr)
    print("方法: 分数阶 Adams-Bashforth-Moulton 预估-校正 (PECE), α=1/2", file=sys.stderr)
    print("方程: M D¹v + K_B√π D^{1/2}v = G - b_K|v|^(n_pl-1)v - c_q|v|v", file=sys.stderr)
    print("参数: " + ", ".join(f"{k}={params[k]:g}" for k in DEFAULT_PARAMS), file=sys.stderr)
    print(f"有效惯性 M={M:g}, 净重力 G={G:g}", file=sys.stderr)
    h = (args.t1 - args.t0) / (args.n - 1)
    print(f"区间 t∈[{args.t0},{args.t1}], v(0)={args.y0}, {args.n} 点 (h={h:.2e}), "
          f"校正迭代={args.corrector_iters}", file=sys.stderr)
    print("=" * 64, file=sys.stderr)

    t = np.linspace(args.t0, args.t1, args.n)
    Y = frac_pece(ALPHA, f, [args.y0, 0.0], t, corrector_iters=args.corrector_iters)
    v = Y[:, 0]
    print(f"末态: v(t={t[-1]:g}) = {v[-1]:.6g}", file=sys.stderr)

    lin = _analytic_linear(params, args.y0)
    if lin is not None:
        err = float(np.max(np.abs(v - lin[0](t))))
        print(f"[验证] K_B=0 线性情形：v_inf={lin[1]:.6g}, 最大误差={err:.3e}", file=sys.stderr)

    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parent / "outputs" / "ode_data"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"basset_abm_{timestamp}.csv"

    cols = ["t", "v"]
    data = [t, v]
    if args.noise > 0:
        rng = np.random.default_rng(args.seed)
        scale = args.noise * (np.max(np.abs(v)) or 1.0)
        data.append(v + rng.normal(0.0, scale, size=v.shape))
        cols.append("v_noisy")

    np.savetxt(csv_path, np.column_stack(data), delimiter=",",
               header=",".join(cols), comments="")
    print(f"\n写出 {len(t)} 个数据点 -> {csv_path}", file=sys.stderr)

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(t, v, "-", lw=2, label="v(t) fractional ABM (with Basset)")
            if args.noise > 0:
                ax.plot(t, data[-1], ".", ms=3, alpha=0.4, label="noisy samples")
            if lin is not None:
                ax.plot(t, lin[0](t), "--", lw=1, label="analytic (linear, K_B=0)")
            ax.set_xlabel("t"); ax.set_ylabel("v")
            ax.set_title("Basset falling sphere — fractional Adams-Bashforth-Moulton")
            ax.legend(); ax.grid(alpha=0.3)
            fig.tight_layout()
            png = csv_path.with_suffix(".png")
            fig.savefig(png, dpi=120)
            print(f"曲线图 -> {png}", file=sys.stderr)
        except ImportError:
            print("（matplotlib 未安装，跳过画图）", file=sys.stderr)


if __name__ == "__main__":
    main()
