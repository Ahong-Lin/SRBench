"""
一阶 ODE 数值积分器（生成数据点）。
================================================

把形如  dy/dt = f(t, y, <参数...>)  的常微分方程数值积分，输出 (t, y) 数据点。
默认预填的是 sphere-in-fluid 进化谱系 gen2 的方程（浮力 + 附加质量）：

    (m + C_a*rho_f*V_s) * dv/dt = (m - rho_f*V_s)*g - b*v,   v(0) = 0

即

    dv/dt = ((m - rho_f*V_s)*g - b*v) / (m + C_a*rho_f*V_s)

该线性 ODE 有闭式解，脚本会在可行时顺便对比解析解，验证数值积分精度。

用法
----
    # 直接用默认方程和默认参数跑（开箱即用）
    python integrate_ode.py

    # 改积分区间、初值、步数
    python integrate_ode.py --t0 0 --t1 20 --y0 0 --n 400

    # 覆盖参数（任意一个，未给的用默认）
    python integrate_ode.py --params "m=0.05, b=0.8, g=9.81, rho_f=1000, V_s=4e-5, C_a=0.5"

    # 积分自己的方程（RHS 用 sympy 语法，自变量 t、因变量 y）
    python integrate_ode.py \
        --rhs "(m - rho_f*V_s)*g/(m + C_a*rho_f*V_s) - b/(m + C_a*rho_f*V_s)*y" \
        --params "m=0.05,b=0.8,g=9.81,rho_f=1000,V_s=4e-5,C_a=0.5" \
        --t0 0 --t1 30 --n 300 --yname v

    # 加观测噪声（相对高斯噪声，便于做符号回归数据）
    python integrate_ode.py --noise 0.02 --seed 0

输出
----
    outputs/ode_data/ode_{yname}_{timestamp}.csv     列: t, <yname>[, <yname>_noisy]
    （--plot 时额外存一张 .png 曲线图）
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp


# ============================================================
# 默认方程（gen2: 浮力 + 附加质量），dv/dt = f(t, v)
# ============================================================

DEFAULT_RHS = "((m - rho_f*V_s)*g - b*y) / (m + C_a*rho_f*V_s)"
DEFAULT_YNAME = "v"
DEFAULT_PARAMS = {
    "m": 0.05,        # 球质量 (kg)
    "b": 0.8,         # 线性 (Stokes) 阻力系数 (kg/s)
    "g": 9.81,        # 重力加速度 (m/s^2)
    "rho_f": 1000.0,  # 流体密度 (kg/m^3)
    "V_s": 4e-5,      # 球体积 (m^3)
    "C_a": 0.5,       # 附加质量系数（球的理论值 0.5）
}


# ============================================================
# Helpers
# ============================================================

def _parse_params(text: str | None, defaults: dict) -> dict:
    """解析 'm=0.05, b=0.8' 形式的参数字符串，未给的用默认值。"""
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
        try:
            params[name.strip()] = float(val.strip())
        except ValueError:
            raise SystemExit(f"参数值不是数字: '{chunk}'")
    return params


def _build_rhs(rhs_expr: str, yname: str, param_names: list[str]):
    """
    把 sympy 字符串编译成 f(t, y) 数值函数。
    表达式里允许出现: t（自变量）、y 或 yname（因变量）、各参数名、常见数学函数。
    返回 (func(t, y, **params), 用到的自由符号集合)。
    """
    import sympy
    from sympy import Symbol, Function  # noqa: F401

    t = sympy.Symbol("t")
    y = sympy.Symbol("y")
    # 允许用户用真实因变量名（如 v）书写，等价于 y
    locals_map = {"t": t, "y": y, yname: y}
    for p in param_names:
        locals_map[p] = sympy.Symbol(p)

    try:
        expr = sympy.sympify(rhs_expr, locals=locals_map)
    except Exception as ex:
        raise SystemExit(f"无法解析 RHS 表达式: {type(ex).__name__}: {ex}")

    # 把用户写的 yname 符号替换成统一的 y
    if yname != "y":
        expr = expr.subs(sympy.Symbol(yname), y)

    free = {str(s) for s in expr.free_symbols}
    unknown = free - {"t", "y"} - set(param_names)
    if unknown:
        raise SystemExit(
            f"RHS 里出现未知符号 {sorted(unknown)}；"
            f"请在 --params 里给它们赋值，或检查拼写。"
        )

    ordered_params = [p for p in param_names if p in free]
    f_lamb = sympy.lambdify([t, y] + [sympy.Symbol(p) for p in ordered_params],
                            expr, modules="numpy")

    def rhs(tt, yy, params):
        args = [params[p] for p in ordered_params]
        return f_lamb(tt, yy, *args)

    return rhs, free, expr


def _analytic_linear_solution(params: dict, y0: float):
    """
    若方程是默认线性形式 dv/dt = (A - b*v)/M，给出闭式解用于精度对比：
        v(t) = v_inf + (y0 - v_inf) * exp(-(b/M) t),  v_inf = A/b, M = m + C_a*rho_f*V_s
    返回 callable 或 None。
    """
    try:
        m, b, g = params["m"], params["b"], params["g"]
        rho_f, V_s, C_a = params["rho_f"], params["V_s"], params["C_a"]
    except KeyError:
        return None
    M = m + C_a * rho_f * V_s
    A = (m - rho_f * V_s) * g
    if b == 0 or M == 0:
        return None
    v_inf = A / b

    def sol(t):
        return v_inf + (y0 - v_inf) * np.exp(-(b / M) * t)

    return sol, v_inf


# ============================================================
# Main
# ============================================================

def main() -> None:
    p = argparse.ArgumentParser(
        description="一阶 ODE 数值积分，生成 (t, y) 数据点",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--rhs", default=DEFAULT_RHS,
                   help="dy/dt 的右端表达式（sympy 语法；自变量 t，因变量 y 或 --yname）")
    p.add_argument("--yname", default=DEFAULT_YNAME,
                   help="因变量名（仅影响输出列名与可读性）")
    p.add_argument("--params", default=None,
                   help="参数赋值，如 'm=0.05, b=0.8, g=9.81'（未给的用内置默认）")
    p.add_argument("--t0", type=float, default=0.0, help="积分起点")
    p.add_argument("--t1", type=float, default=15.0, help="积分终点")
    p.add_argument("--y0", type=float, default=0.0, help="初值 y(t0)")
    p.add_argument("--n", type=int, default=200, help="输出采样点个数")
    p.add_argument("--method", default="RK45",
                   help="solve_ivp 积分方法 (RK45/Radau/LSODA/...)")
    p.add_argument("--rtol", type=float, default=1e-8)
    p.add_argument("--atol", type=float, default=1e-10)
    p.add_argument("--noise", type=float, default=0.0,
                   help="相对高斯噪声标准差（如 0.02 = 2%%），>0 时额外输出带噪列")
    p.add_argument("--seed", type=int, default=0, help="噪声随机种子")
    p.add_argument("--output-dir", default=None,
                   help="输出目录（默认 Auto-workflow-PSE/outputs/ode_data）")
    p.add_argument("--plot", action="store_true", help="同时存一张曲线图 (.png)")
    args = p.parse_args()

    if args.t1 <= args.t0:
        raise SystemExit("--t1 必须大于 --t0")
    if args.n < 2:
        raise SystemExit("--n 至少为 2")

    params = _parse_params(args.params, DEFAULT_PARAMS)
    rhs, free, expr = _build_rhs(args.rhs, args.yname, list(params.keys()))

    print("=" * 60, file=sys.stderr)
    print(f"ODE: d{args.yname}/dt = {expr}", file=sys.stderr)
    used = sorted(free - {"t", "y"})
    print(f"参数: " + ", ".join(f"{k}={params[k]:g}" for k in used), file=sys.stderr)
    print(f"区间: t∈[{args.t0}, {args.t1}], {args.yname}(0)={args.y0}, "
          f"采样 {args.n} 点, method={args.method}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    t_eval = np.linspace(args.t0, args.t1, args.n)
    sol = solve_ivp(
        fun=lambda tt, yy: rhs(tt, yy[0] if np.ndim(yy) else yy, params),
        t_span=(args.t0, args.t1),
        y0=[args.y0],
        t_eval=t_eval,
        method=args.method,
        rtol=args.rtol,
        atol=args.atol,
    )
    if not sol.success:
        raise SystemExit(f"积分失败: {sol.message}")

    t = sol.t
    y = sol.y[0]

    # 若是默认线性方程，对比解析解，报告最大误差
    analytic = _analytic_linear_solution(params, args.y0)
    if args.rhs == DEFAULT_RHS and analytic is not None:
        sol_fn, v_inf = analytic
        y_exact = sol_fn(t)
        max_err = float(np.max(np.abs(y - y_exact)))
        print(f"解析解可用：终端速度 v_inf = {v_inf:.6g}", file=sys.stderr)
        print(f"数值解 vs 解析解 最大绝对误差 = {max_err:.3e}", file=sys.stderr)

    # 输出目录
    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parent / "outputs" / "ode_data"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"ode_{args.yname}_{timestamp}.csv"

    # 写 CSV
    cols = ["t", args.yname]
    data = [t, y]
    if args.noise > 0:
        rng = np.random.default_rng(args.seed)
        scale = args.noise * (np.max(np.abs(y)) or 1.0)
        y_noisy = y + rng.normal(0.0, scale, size=y.shape)
        cols.append(f"{args.yname}_noisy")
        data.append(y_noisy)

    arr = np.column_stack(data)
    header = ",".join(cols)
    np.savetxt(csv_path, arr, delimiter=",", header=header, comments="")
    print(f"\n写出 {len(t)} 个数据点 -> {csv_path}", file=sys.stderr)

    # 可选画图
    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(t, y, "-", lw=2, label=f"{args.yname}(t) numeric")
            if args.noise > 0:
                ax.plot(t, data[-1], ".", ms=4, alpha=0.5, label="noisy samples")
            ax.set_xlabel("t")
            ax.set_ylabel(args.yname)
            ax.set_title(f"d{args.yname}/dt = {expr}")
            ax.legend()
            ax.grid(alpha=0.3)
            png_path = csv_path.with_suffix(".png")
            fig.tight_layout()
            fig.savefig(png_path, dpi=120)
            print(f"曲线图 -> {png_path}", file=sys.stderr)
        except ImportError:
            print("（matplotlib 未安装，跳过画图）", file=sys.stderr)


if __name__ == "__main__":
    main()
