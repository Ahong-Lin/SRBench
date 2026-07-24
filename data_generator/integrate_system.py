"""
一阶 ODE 系统 / 高阶 ODE 数值积分器（生成数据点）。
=====================================================

把一组耦合的一阶常微分方程

    d(state_1)/dt = f_1(t, state_1, ..., 参数)
    d(state_2)/dt = f_2(t, state_1, ..., 参数)
    ...

数值积分，输出 (t, state_1, state_2, ...) 数据点。

高阶 ODE 先化成一阶系统再积。默认预填的是受迫非线性振子（二阶 ODE）：

    x'' = F0*sin(t) - beta*sin(x') - omega0**2 * x**3 - omega0**2 * x * exp(-|x|)

引入 v = dx/dt 化为两个一阶方程：

    dx/dt = v
    dv/dt = F0*sin(t) - beta*sin(v) - omega0**2*x**3 - omega0**2*x*exp(-Abs(x))

用法
----
    # 直接用默认振子跑（开箱即用）
    python integrate_system.py

    # 改参数、区间、初值、采样
    python integrate_system.py \
        --params "F0=1.2, beta=0.3, omega0=1.0" \
        --y0 "0, 0" --t0 0 --t1 60 --n 2000 --plot

    # 积分你自己的系统：--state 给状态变量（逗号分隔），
    #   --rhs 给各自的导数表达式（用 ; 分隔，顺序与 --state 一致）
    python integrate_system.py \
        --state "x, v" \
        --rhs "v ; F0*sin(t) - beta*sin(v) - omega0**2*x**3 - omega0**2*x*exp(-Abs(x))" \
        --y0 "0.5, 0" \
        --params "F0=1.2, beta=0.3, omega0=1.0" \
        --t1 80 --n 3000 --plot

    # 一阶单方程也能用（state 只给一个）
    python integrate_system.py --state "y" --rhs "-k*y" --params "k=0.5" --y0 "1"

提示
----
- 表达式用 sympy 语法：** 乘方、Abs() 绝对值、sin/cos/exp/log/sqrt/tanh 等。
- 写 x(t)、v(t) 也可以，脚本会自动去掉 "(t)"。
- 自变量固定是 t；状态变量名由 --state 决定；其余符号都视为参数，必须在 --params 里赋值。

输出
----
    outputs/ode_data/system_{timestamp}.csv      列: t, <state...>[, <state>_noisy ...]
    （--plot 时额外存曲线图与相图 .png）
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp


# ============================================================
# 默认系统：受迫非线性振子（二阶 -> 两个一阶）
# ============================================================

DEFAULT_STATE = "x, v"
DEFAULT_RHS = "v ; F0*sin(t) - beta*sin(v) - omega0**2*x**3 - omega0**2*x*exp(-Abs(x))"
DEFAULT_Y0 = "0, 0"
DEFAULT_PARAMS = {
    "F0": 1.2,       # 外驱力幅值
    "beta": 0.3,     # 非线性阻尼强度
    "omega0": 1.0,   # 固有频率尺度
}


# ============================================================
# Helpers
# ============================================================

def _split_list(text: str, sep: str = ",") -> list[str]:
    return [s.strip() for s in text.split(sep) if s.strip()]


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
        try:
            params[name.strip()] = float(val.strip())
        except ValueError:
            raise SystemExit(f"参数值不是数字: '{chunk}'")
    return params


def _parse_floats(text: str, n_expected: int, what: str) -> list[float]:
    parts = _split_list(text)
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        raise SystemExit(f"{what} 必须是数字列表，收到: '{text}'")
    if len(vals) != n_expected:
        raise SystemExit(
            f"{what} 个数 ({len(vals)}) 与状态变量个数 ({n_expected}) 不一致"
        )
    return vals


def _strip_of_t(expr: str, state_names: list[str]) -> str:
    """把 x(t)、v(t) 这种写法里的 (t) 去掉，统一成 x、v。"""
    out = expr
    for s in state_names:
        out = re.sub(rf"\b{re.escape(s)}\s*\(\s*t\s*\)", s, out)
    return out


def _build_system(state_names: list[str], rhs_exprs: list[str],
                  param_names: list[str]):
    """把各导数表达式编译成数值函数 f(t, Y, params) -> list。"""
    import sympy

    t = sympy.Symbol("t")
    state_syms = [sympy.Symbol(s) for s in state_names]
    param_syms = [sympy.Symbol(p) for p in param_names]
    locals_map = {"t": t}
    for s, sym in zip(state_names, state_syms):
        locals_map[s] = sym
    for p, sym in zip(param_names, param_syms):
        locals_map[p] = sym

    compiled = []
    parsed_exprs = []
    allowed = {"t"} | set(state_names) | set(param_names)
    for i, raw in enumerate(rhs_exprs):
        cleaned = _strip_of_t(raw, state_names)
        try:
            expr = sympy.sympify(cleaned, locals=locals_map)
        except Exception as ex:
            raise SystemExit(
                f"无法解析第 {i+1} 个导数表达式 (d{state_names[i]}/dt):\n"
                f"  {raw}\n  {type(ex).__name__}: {ex}"
            )
        free = {str(s) for s in expr.free_symbols}
        unknown = free - allowed
        if unknown:
            raise SystemExit(
                f"d{state_names[i]}/dt 里出现未知符号 {sorted(unknown)}；"
                f"请在 --params 里赋值，或检查拼写。\n  表达式: {raw}"
            )
        f = sympy.lambdify([t] + state_syms + param_syms, expr, modules="numpy")
        compiled.append(f)
        parsed_exprs.append(expr)

    def system(tt, Y, params):
        pvals = [params[p] for p in param_names]
        return [f(tt, *Y, *pvals) for f in compiled]

    return system, parsed_exprs


# ============================================================
# Main
# ============================================================

def main() -> None:
    p = argparse.ArgumentParser(
        description="一阶 ODE 系统 / 高阶 ODE 数值积分，生成数据点",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--state", default=DEFAULT_STATE,
                   help="状态变量名，逗号分隔（如 'x, v'）")
    p.add_argument("--rhs", default=DEFAULT_RHS,
                   help="各状态导数表达式，用 ; 分隔，顺序与 --state 一致")
    p.add_argument("--y0", default=DEFAULT_Y0,
                   help="初值，逗号分隔，顺序与 --state 一致（如 '0, 0'）")
    p.add_argument("--params", default=None,
                   help="参数赋值，如 'F0=1.2, beta=0.3, omega0=1.0'（未给的用内置默认）")
    p.add_argument("--t0", type=float, default=0.0, help="积分起点")
    p.add_argument("--t1", type=float, default=60.0, help="积分终点")
    p.add_argument("--n", type=int, default=2000, help="输出采样点个数")
    p.add_argument("--method", default="RK45",
                   help="solve_ivp 积分方法 (RK45/Radau/LSODA/DOP853/...)")
    p.add_argument("--rtol", type=float, default=1e-8)
    p.add_argument("--atol", type=float, default=1e-10)
    p.add_argument("--noise", type=float, default=0.0,
                   help="相对高斯噪声标准差（如 0.02），>0 时对每个状态额外输出带噪列")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output-dir", default=None,
                   help="输出目录（默认 Auto-workflow-PSE/outputs/ode_data）")
    p.add_argument("--plot", action="store_true",
                   help="存时间序列图；若状态数>=2 再存一张相图")
    args = p.parse_args()

    if args.t1 <= args.t0:
        raise SystemExit("--t1 必须大于 --t0")
    if args.n < 2:
        raise SystemExit("--n 至少为 2")

    state_names = _split_list(args.state)
    if not state_names:
        raise SystemExit("--state 不能为空")
    rhs_exprs = _split_list(args.rhs, sep=";")
    if len(rhs_exprs) != len(state_names):
        raise SystemExit(
            f"--rhs 里有 {len(rhs_exprs)} 个表达式，但 --state 有 "
            f"{len(state_names)} 个变量；二者必须一一对应（用 ; 分隔导数）。"
        )

    params = _parse_params(args.params, DEFAULT_PARAMS)
    y0 = _parse_floats(args.y0, len(state_names), "--y0")
    system, exprs = _build_system(state_names, rhs_exprs, list(params.keys()))

    # 报告实际使用的参数（只列方程里真正出现的）
    used = sorted({str(s) for e in exprs for s in e.free_symbols}
                  - {"t"} - set(state_names))
    print("=" * 64, file=sys.stderr)
    print("ODE 系统:", file=sys.stderr)
    for sn, e in zip(state_names, exprs):
        print(f"  d{sn}/dt = {e}", file=sys.stderr)
    if used:
        print("参数: " + ", ".join(f"{k}={params[k]:g}" for k in used), file=sys.stderr)
    print(f"区间: t∈[{args.t0}, {args.t1}], 初值 {dict(zip(state_names, y0))}, "
          f"采样 {args.n} 点, method={args.method}", file=sys.stderr)
    print("=" * 64, file=sys.stderr)

    t_eval = np.linspace(args.t0, args.t1, args.n)
    sol = solve_ivp(
        fun=lambda tt, Y: system(tt, Y, params),
        t_span=(args.t0, args.t1),
        y0=y0,
        t_eval=t_eval,
        method=args.method,
        rtol=args.rtol,
        atol=args.atol,
    )
    if not sol.success:
        raise SystemExit(f"积分失败: {sol.message}")

    t = sol.t
    Y = sol.y  # shape (n_state, n_points)

    # 简单报告末态
    final = ", ".join(f"{sn}={Y[i, -1]:.4g}" for i, sn in enumerate(state_names))
    print(f"末态 (t={t[-1]:g}): {final}", file=sys.stderr)

    # 输出目录
    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parent / "outputs" / "ode_data"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"system_{timestamp}.csv"

    cols = ["t"] + state_names
    data = [t] + [Y[i] for i in range(len(state_names))]
    if args.noise > 0:
        rng = np.random.default_rng(args.seed)
        for i, sn in enumerate(state_names):
            scale = args.noise * (np.max(np.abs(Y[i])) or 1.0)
            cols.append(f"{sn}_noisy")
            data.append(Y[i] + rng.normal(0.0, scale, size=Y[i].shape))

    arr = np.column_stack(data)
    np.savetxt(csv_path, arr, delimiter=",", header=",".join(cols), comments="")
    print(f"\n写出 {len(t)} 个数据点 -> {csv_path}", file=sys.stderr)

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            # 时间序列
            fig, ax = plt.subplots(figsize=(8, 4))
            for i, sn in enumerate(state_names):
                ax.plot(t, Y[i], lw=1.5, label=sn)
            ax.set_xlabel("t")
            ax.set_ylabel("state")
            ax.set_title("time series")
            ax.legend()
            ax.grid(alpha=0.3)
            fig.tight_layout()
            ts_path = csv_path.with_name(csv_path.stem + "_timeseries.png")
            fig.savefig(ts_path, dpi=120)
            print(f"时间序列图 -> {ts_path}", file=sys.stderr)

            # 相图（前两个状态）
            if len(state_names) >= 2:
                fig2, ax2 = plt.subplots(figsize=(5, 5))
                ax2.plot(Y[0], Y[1], lw=0.8)
                ax2.set_xlabel(state_names[0])
                ax2.set_ylabel(state_names[1])
                ax2.set_title("phase portrait")
                ax2.grid(alpha=0.3)
                fig2.tight_layout()
                ph_path = csv_path.with_name(csv_path.stem + "_phase.png")
                fig2.savefig(ph_path, dpi=120)
                print(f"相图 -> {ph_path}", file=sys.stderr)
        except ImportError:
            print("（matplotlib 未安装，跳过画图）", file=sys.stderr)


if __name__ == "__main__":
    main()
