"""
Basset–Boussinesq–Oseen (BBO) 积分-微分方程数值积分器。
======================================================

求解 sphere-in-fluid 进化谱系 gen5 的方程（含 Basset 历史/记忆力）：

    M dv/dt = G - b_K*|v|^(n_pl-1)*v - c_q*|v|*v
              - K_B * ∫_0^t  v'(τ) / sqrt(t-τ)  dτ

    M = m + C_a*rho_f*V_s   （有效惯性：球 + 附加质量）
    G = (m - rho_f*V_s)*g    （净重力 = 重力 - 浮力）

最后一项是 Basset 历史力：当前阻力依赖整个过去的加速度历史，核为 1/sqrt(t-τ)。
这是积分-微分方程（IDE），普通 solve_ivp 无法处理。

数值方法
--------
- 均匀时间网格 t_n = n*h（记忆格式要求等步长）。
- Basset 积分用 product-integration（分段常数 v'）离散：
      ∫_0^{t_n} v'(τ)/sqrt(t_n-τ) dτ ≈ (2/sqrt(h)) Σ_{j=0}^{n-1} (v_{j+1}-v_j) * w_{n-j}
      w_k = sqrt(k) - sqrt(k-1)
  这是 Basset 力的标准乘积积分格式（弱奇异核可解析积分）。
- 局部导数用隐式（后向）Euler，每步对非线性阻力做标量求根（brentq）。
- K_B=0、n_pl=1、c_q=0 时退化为线性 ODE，脚本会自动对比解析解验证精度。

用法
----
    # 开箱即用（默认参数）
    python integrate_basset.py

    # 改参数 / 区间 / 采样 / 画图
    python integrate_basset.py \
        --params "m=0.05, g=9.81, rho_f=1000, V_s=4e-5, C_a=0.5, c_q=0.1, b_K=0.8, n_pl=1.0, K_B=0.5" \
        --t1 5 --n 2000 --plot

    # 关掉 Basset（K_B=0）对比"无记忆"情形
    python integrate_basset.py --params "K_B=0" --plot

输出
----
    outputs/ode_data/basset_{timestamp}.csv     列: t, v[, v_noisy]
    （--plot 时存曲线图；若 K_B=0 且线性，叠加解析解）
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import brentq


# ============================================================
# 默认参数（Newtonian 起步：n_pl=1）
# ============================================================

DEFAULT_PARAMS = {
    "m": 0.05,        # 球质量 (kg)
    "g": 9.81,        # 重力加速度 (m/s^2)
    "rho_f": 1000.0,  # 流体密度 (kg/m^3)
    "V_s": 4e-5,      # 球体积 (m^3)
    "C_a": 0.5,       # 附加质量系数
    "c_q": 0.1,       # 二次（形阻）系数
    "b_K": 0.8,       # 广义 Stokes 阻力系数（n_pl=1 时退化为线性 b）
    "n_pl": 1.0,      # 幂律指数（<1 剪切变稀, =1 牛顿, >1 剪切变稠）
    "K_B": 0.5,       # Basset 历史力系数
}


def _parse_params(text: str | None, defaults: dict) -> dict:
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


def _drag(v: float, b_K: float, n_pl: float, c_q: float) -> float:
    """瞬时阻力：广义 Stokes（幂律）+ 二次形阻。"""
    av = abs(v)
    return b_K * (av ** (n_pl - 1.0)) * v + c_q * av * v


def solve_bbo(params: dict, t0: float, t1: float, n: int, v0: float):
    """
    product-integration + 隐式 Euler 求解 BBO-IDE。
    返回 (t, v)。
    """
    m, g = params["m"], params["g"]
    rho_f, V_s, C_a = params["rho_f"], params["V_s"], params["C_a"]
    c_q, b_K, n_pl, K_B = params["c_q"], params["b_K"], params["n_pl"], params["K_B"]

    M = m + C_a * rho_f * V_s
    G = (m - rho_f * V_s) * g
    if M <= 0:
        raise SystemExit(f"有效惯性 M = m + C_a*rho_f*V_s = {M:g} 必须 > 0")

    t = np.linspace(t0, t1, n)
    h = (t1 - t0) / (n - 1)
    sqrt_h = np.sqrt(h)

    # Basset 权重 w_k = sqrt(k) - sqrt(k-1), k = 1..n-1
    k = np.arange(0, n)
    sqrt_k = np.sqrt(k)
    w = np.empty(n)            # w[k] 对应 w_k；w[0] 不用
    w[1:] = sqrt_k[1:] - sqrt_k[:-1]

    v = np.zeros(n)
    v[0] = v0
    dv = np.zeros(n)           # 增量 dv[j] = v[j+1]-v[j]

    coef = K_B * 2.0 / sqrt_h  # Basset 当前步系数

    for nn in range(1, n):
        v_prev = v[nn - 1]
        # 历史部分 H_n = (2/sqrt h) Σ_{j=0}^{n-2} dv[j] * w[n-j]
        if nn >= 2:
            j = np.arange(0, nn - 1)            # 0..nn-2
            H_n = (2.0 / sqrt_h) * np.dot(dv[:nn - 1], w[nn - j])
        else:
            H_n = 0.0

        # 残差: R(vn) = M*(vn - v_prev)/h - G + drag(vn)
        #               + K_B*[ (2/sqrt h)(vn - v_prev) + H_n ]
        def R(vn):
            return (M * (vn - v_prev) / h - G
                    + _drag(vn, b_K, n_pl, c_q)
                    + coef * (vn - v_prev) + K_B * H_n)

        # 用 brentq 求根：从 v_prev 出发向外扩张找到变号区间
        lo, hi = v_prev - 1e-6, v_prev + 1e-6
        f_lo, f_hi = R(lo), R(hi)
        grow = 0
        while f_lo * f_hi > 0 and grow < 200:
            span = (hi - lo) * 2.0 + 1e-3
            lo -= span
            hi += span
            f_lo, f_hi = R(lo), R(hi)
            grow += 1
        if f_lo * f_hi > 0:
            raise SystemExit(f"第 {nn} 步求根失败：无法包住根（检查参数是否发散）")
        vn = brentq(R, lo, hi, xtol=1e-12, rtol=1e-12, maxiter=200)

        v[nn] = vn
        dv[nn - 1] = vn - v_prev

    return t, v


def _analytic_linear(params: dict, v0: float):
    """K_B=0, n_pl=1, c_q=0 时的线性闭式解，用于精度验证。"""
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

    def sol(t):
        return v_inf + (v0 - v_inf) * np.exp(-t / tau)

    return sol, v_inf


def main() -> None:
    p = argparse.ArgumentParser(
        description="BBO 积分-微分方程（含 Basset 历史力）数值积分",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--params", default=None,
                   help="参数赋值（未给的用内置默认），如 'K_B=0.5, n_pl=0.8'")
    p.add_argument("--t0", type=float, default=0.0)
    p.add_argument("--t1", type=float, default=5.0, help="积分终点")
    p.add_argument("--n", type=int, default=2000, help="均匀网格点数（记忆格式需等步长）")
    p.add_argument("--y0", type=float, default=0.0, help="初速 v(t0)（从静止释放=0）")
    p.add_argument("--noise", type=float, default=0.0,
                   help="相对高斯噪声标准差（如 0.02），>0 时额外输出带噪列")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--plot", action="store_true")
    args = p.parse_args()

    if args.t1 <= args.t0:
        raise SystemExit("--t1 必须大于 --t0")
    if args.n < 3:
        raise SystemExit("--n 至少为 3")

    params = _parse_params(args.params, DEFAULT_PARAMS)
    M = params["m"] + params["C_a"] * params["rho_f"] * params["V_s"]
    G = (params["m"] - params["rho_f"] * params["V_s"]) * params["g"]

    print("=" * 64, file=sys.stderr)
    print("BBO 方程: M dv/dt = G - b_K|v|^(n_pl-1)v - c_q|v|v - K_B ∫ v'(τ)/√(t-τ) dτ",
          file=sys.stderr)
    print(f"参数: " + ", ".join(f"{k}={params[k]:g}" for k in DEFAULT_PARAMS),
          file=sys.stderr)
    print(f"有效惯性 M={M:g}, 净重力 G={G:g}", file=sys.stderr)
    print(f"区间 t∈[{args.t0},{args.t1}], v(0)={args.y0}, {args.n} 点 (h={(args.t1-args.t0)/(args.n-1):.2e})",
          file=sys.stderr)
    print("=" * 64, file=sys.stderr)

    t, v = solve_bbo(params, args.t0, args.t1, args.n, args.y0)
    print(f"末态: v(t={t[-1]:g}) = {v[-1]:.6g}", file=sys.stderr)

    # 精度验证（线性情形）
    lin = _analytic_linear(params, args.y0)
    if lin is not None:
        sol_fn, v_inf = lin
        err = float(np.max(np.abs(v - sol_fn(t))))
        print(f"[验证] K_B=0 线性情形：解析终端 v_inf={v_inf:.6g}, "
              f"数值 vs 解析 最大误差={err:.3e}", file=sys.stderr)

    # 输出
    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parent / "outputs" / "ode_data"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"basset_{timestamp}.csv"

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
            ax.plot(t, v, "-", lw=2, label="v(t) numeric (with Basset)")
            if args.noise > 0:
                ax.plot(t, data[-1], ".", ms=3, alpha=0.4, label="noisy samples")
            if lin is not None:
                ax.plot(t, lin[0](t), "--", lw=1, label="analytic (linear, K_B=0)")
            ax.set_xlabel("t")
            ax.set_ylabel("v")
            ax.set_title("BBO falling sphere with Basset history force")
            ax.legend()
            ax.grid(alpha=0.3)
            fig.tight_layout()
            png_path = csv_path.with_suffix(".png")
            fig.savefig(png_path, dpi=120)
            print(f"曲线图 -> {png_path}", file=sys.stderr)
        except ImportError:
            print("（matplotlib 未安装，跳过画图）", file=sys.stderr)


if __name__ == "__main__":
    main()
