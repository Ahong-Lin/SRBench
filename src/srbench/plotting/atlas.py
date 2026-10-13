"""Draw ground-truth curves, multivariate slices and ODE trajectories for a run.

No submitted law or model call is needed. Packaged formulas are authoritative;
unpackaged candidates retain their explicit packaging status in the gallery.
"""
from __future__ import annotations

import argparse
import html
import itertools
import json
import math
import os
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm, Normalize, SymLogNorm
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

from srbench.common.contracts import contract_from_spec
from srbench.common.io import read_json, read_jsonl, write_json
from srbench.packaging.reference import compile_truth
from .paths import plot_directory

BLUE = "#2563a6"
ORANGE = "#d05d27"
INK = "#183247"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlepad": 12, "savefig.facecolor": "white"})


def coordinate(axis, normalized):
    low, high = map(float, axis["range"])
    u = np.asarray(normalized)
    if axis.get("scale") == "log":
        return 10.0 ** (np.log10(low) + u * (np.log10(high) - np.log10(low)))
    return low + u * (high - low)


def label(name):
    return "\n".join(textwrap.wrap(name, 30, break_long_words=True, break_on_hyphens=False))


def decorate(ax):
    ax.grid(alpha=.16)
    ax.tick_params(labelsize=8)
    if ax.get_yscale() == "linear":
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 4), useMathText=True)


def color_norm(values):
    finite = np.asarray(values)[np.isfinite(values)]
    if not len(finite):
        return Normalize(0, 1), "linear color"
    low, high = float(finite.min()), float(finite.max())
    if low == high:
        delta = max(abs(low) * .02, np.finfo(float).tiny)
        return Normalize(low - delta, high + delta), "linear color"
    if low > 0 and high / low > 1000:
        return LogNorm(low, high), "log color"
    magnitudes = np.abs(finite[finite != 0])
    if len(magnitudes) and np.max(magnitudes) / max(np.percentile(magnitudes, 10), 1e-300) > 1000:
        threshold = max(float(np.percentile(magnitudes, 10)), float(np.max(magnitudes)) * 1e-6)
        return SymLogNorm(threshold, vmin=low, vmax=high), "symlog color"
    return Normalize(low, high), "linear color"


def evaluate(function, contract, rows):
    parameters = [np.float64(v) for v in contract.parameters.values()]
    values = []
    with np.errstate(all="ignore"):
        for row in rows:
            try:
                values.append(float(function(*np.asarray(row, dtype=float), *parameters)))
            except (ValueError, TypeError, OverflowError, ZeroDivisionError, FloatingPointError):
                values.append(float("nan"))
    result = np.asarray(values)
    result[~np.isfinite(result)] = np.nan
    return result


def save_figure(fig, destination, name, atlas=None):
    fig.savefig(destination / f"{name}.png", dpi=155, bbox_inches="tight")
    fig.savefig(destination / f"{name}.pdf", bbox_inches="tight")
    if atlas is not None:
        atlas.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def shade_time(ax, axis):
    cut = float(coordinate(axis, .9))
    ax.axvspan(cut, axis["range"][1], color=ORANGE, alpha=.12)
    ax.axvline(cut, color=ORANGE, linestyle="--", lw=1)


def static_figures(task_id, spec, contract, destination, atlas):
    axes = spec["independent_variables"]
    names = contract.features
    function = compile_truth(contract)
    dimension = len(names)
    contexts = [.15, .5, .85] if dimension > 1 else [.5]
    fixed = {axis["symbol"]: float(coordinate(axis, .5)) for axis in axes}
    metadata = {"kind": "static_ground_truth", "target": contract.target,
                "input_dimension": dimension, "fixed_midpoint_values": fixed,
                "profile_contexts_normalized": contexts, "axes": axes,
                "meaning": "Each curve or heatmap fixes all unshown inputs. These are conditional slices, not marginal averages.",
                "nonfinite_plot_points": 0, "plots": []}
    ncols = min(dimension, 2)
    fig, panels = plt.subplots(math.ceil(dimension / ncols), ncols,
                              figsize=(7 * ncols, 3.8 * math.ceil(dimension / ncols)),
                              squeeze=False, constrained_layout=True)
    profiles = []
    for i, (axis, ax) in enumerate(zip(axes, panels.flat)):
        # Sample bin centers across the entire declared coordinate range.
        # This avoids requiring singular boundary values for a display grid.
        u = (np.arange(401) + .5) / 401
        x = coordinate(axis, u)
        for context, color in zip(contexts, ("#23856d", BLUE, "#aa4b8a") if dimension > 1 else (BLUE,)):
            base = np.asarray([coordinate(a, context) for a in axes], dtype=float)
            rows = np.tile(base, (len(x), 1))
            rows[:, i] = x
            y = evaluate(function, contract, rows)
            metadata["nonfinite_plot_points"] += int((~np.isfinite(y)).sum())
            ax.plot(x, y, color=color, lw=1.7, label=f"others at u={context:g}" if dimension > 1 else "ground truth")
            profiles.append(pd.DataFrame({"input": names[i], "context_u": context, "x": x, "output": y}))
        if axis.get("scale") == "log":
            ax.set_xscale("log")
        if dimension == 1:
            shade_time(ax, axis)
        ax.set(xlabel=label(names[i]), ylabel=label(contract.target))
        ax.legend(frameon=False, fontsize=8)
        decorate(ax)
    for ax in list(panels.flat)[dimension:]:
        ax.set_visible(False)
    fig.suptitle(f"{task_id}  |  {dimension} input(s)  |  ground-truth profiles\n"
                 "Unshown inputs held at indicated positions in their linear/log sampling coordinates", fontsize=13)
    save_figure(fig, destination, "profiles", atlas)
    metadata["plots"].append("profiles")
    pd.concat(profiles, ignore_index=True).to_csv(destination / "profile_values.csv", index=False)

    if dimension == 1:
        row = profiles[0]
        fig, ax = plt.subplots(figsize=(5.5, 3.5), constrained_layout=True)
        ax.plot(row.x, row.output, lw=2, color=BLUE)
        if axes[0].get("scale") == "log": ax.set_xscale("log")
        shade_time(ax, axes[0])
        ax.set(xlabel=label(names[0]), ylabel=label(contract.target), title=f"{task_id} | 1D static")
        decorate(ax)
        save_figure(fig, destination, "preview")
        metadata["primary"] = "profiles"
        return metadata

    pairs = list(itertools.combinations(range(dimension), 2))
    ncols = min(3, len(pairs))
    nrows = math.ceil(len(pairs) / ncols)
    fig, panels = plt.subplots(nrows, ncols, figsize=(5.6 * ncols, 4.7 * nrows),
                              squeeze=False, constrained_layout=True)
    cut = 1 - .1 ** (1 / dimension)
    surfaces = {}
    first_surface = None
    for ax, (i, j) in zip(panels.flat, pairs):
        u = (np.arange(65) + .5) / 65
        x, y = coordinate(axes[i], u), coordinate(axes[j], u)
        xx, yy = np.meshgrid(x, y)
        rows = np.tile([fixed[n] for n in names], (xx.size, 1))
        rows[:, i], rows[:, j] = xx.ravel(), yy.ravel()
        z = evaluate(function, contract, rows).reshape(xx.shape)
        metadata["nonfinite_plot_points"] += int((~np.isfinite(z)).sum())
        norm, scale = color_norm(z)
        cmap = plt.get_cmap("viridis").copy()
        cmap.set_bad("#dadfe4")
        image = ax.pcolormesh(x, y, np.ma.masked_invalid(z), norm=norm, cmap=cmap, shading="auto")
        if axes[i].get("scale") == "log": ax.set_xscale("log")
        if axes[j].get("scale") == "log": ax.set_yscale("log")
        ax.set(xlabel=label(names[i]), ylabel=label(names[j]), title=f"{label(names[i])} × {label(names[j])}\n{scale}")
        if all(.5 > cut for k in range(dimension) if k not in (i, j)):
            xc, yc = float(coordinate(axes[i], cut)), float(coordinate(axes[j], cut))
            ax.add_patch(Rectangle((xc, yc), axes[i]["range"][1] - xc, axes[j]["range"][1] - yc,
                                   fill=False, edgecolor="#ff934f", linewidth=1.5, linestyle="--"))
        fig.colorbar(image, ax=ax, shrink=.8, label=label(contract.target))
        surfaces[f"pair_{i}_{j}_x"] = x
        surfaces[f"pair_{i}_{j}_y"] = y
        surfaces[f"pair_{i}_{j}_z"] = z
        if first_surface is None:
            first_surface = (i, j, x, y, z, norm, scale)
    for ax in list(panels.flat)[len(pairs):]: ax.set_visible(False)
    fig.suptitle(f"{task_id}  |  {dimension}D static ground truth  |  all input pairs\n"
                 "Others fixed at u=0.5; orange outline = hidden region on this slice; gray = nonfinite", fontsize=13)
    save_figure(fig, destination, "pairwise_slices", atlas)
    np.savez_compressed(destination / "slice_values.npz", **surfaces)
    metadata["plots"].append("pairwise_slices")
    metadata["primary"] = "pairwise_slices"
    metadata["slice_grid"] = {"points_per_axis": 65, "positions": "normalized bin centers", "hidden_corner_boundary": cut}
    i, j, x, y, z, norm, scale = first_surface
    fig, ax = plt.subplots(figsize=(5.5, 3.5), constrained_layout=True)
    image = ax.pcolormesh(x, y, np.ma.masked_invalid(z), norm=norm, cmap="viridis", shading="auto")
    if axes[i].get("scale") == "log": ax.set_xscale("log")
    if axes[j].get("scale") == "log": ax.set_yscale("log")
    ax.set(xlabel=label(names[i]), ylabel=label(names[j]), title=f"{task_id} | {dimension}D static | {scale}")
    fig.colorbar(image, ax=ax, label=label(contract.target), shrink=.82)
    save_figure(fig, destination, "preview")
    return metadata


def ode_figures(task_id, spec, contract, frame, destination, atlas):
    axis = spec["independent_variables"][0]
    time = axis["symbol"]
    states = spec["state_variables"]
    ordered = frame.sort_values(time)
    n = len(states) + 2
    fig, panels = plt.subplots(math.ceil(n / 2), 2, figsize=(13.7, 3.3 * math.ceil(n / 2)),
                              squeeze=False, constrained_layout=True)
    panels = list(panels.flat)
    curves = [(contract.target, panels[0])] + list(zip(states, panels[2:]))
    for name, ax in curves:
        ax.plot(ordered[time], ordered[name], color=BLUE if name == contract.target else "#317d6c", lw=1.7)
        shade_time(ax, axis)
        if axis.get("scale") == "log": ax.set_xscale("log")
        ax.set(xlabel=label(time), ylabel=label(name), title="Benchmark derivative target" if name == contract.target else f"State: {label(name)}")
        decorate(ax)
    target_state = spec["benchmark_target_state"]
    phase = panels[1]
    phase.plot(ordered[target_state], ordered[contract.target], color="#89949e", lw=.6, alpha=.5)
    shown = ordered.iloc[::max(1, len(ordered) // 800)]
    cloud = phase.scatter(shown[target_state], shown[contract.target], c=shown[time], s=6, cmap="viridis")
    fig.colorbar(cloud, ax=phase, label=time, shrink=.85)
    phase.set(xlabel=label(target_state), ylabel=label(contract.target), title="Trajectory in state / derivative space (color = time)")
    decorate(phase)
    for ax in panels[n:]: ax.set_visible(False)
    fig.suptitle(f"{task_id}  |  {len(states)} ODE states  |  exact target: {contract.target}\n"
                 "Original initial conditions; orange shading = final 10% of time; each state uses its own y-axis", fontsize=13)
    save_figure(fig, destination, "trajectories", atlas)
    fig, ax = plt.subplots(figsize=(5.5, 3.5), constrained_layout=True)
    ax.plot(ordered[time], ordered[contract.target], color=BLUE, lw=1.8)
    shade_time(ax, axis)
    if axis.get("scale") == "log": ax.set_xscale("log")
    ax.set(xlabel=time, ylabel=label(contract.target), title=f"{task_id} | {len(states)} states | derivative target")
    decorate(ax)
    save_figure(fig, destination, "preview")
    ordered.to_csv(destination / "trajectory_values.csv", index=False)
    return {"kind": "ode_ground_truth", "target": contract.target, "states": states,
            "plots": ["trajectories"], "primary": "trajectories", "rows": len(frame),
            "meaning": "Observed trajectory of the closed system, not a sweep over independent state combinations.",
            "nonfinite_plot_points": 0}


def unsupported_figure(task_id, entry, spec, run, destination, atlas):
    frame = pd.read_csv(run / entry["data_csv"])
    target = spec["dependent_variable"]
    features = [a["symbol"] for a in spec["independent_variables"]]
    fig, panels = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for ax, name in zip(panels.flat, features):
        ax.scatter(frame[name], frame[target], s=3, color=ORANGE, alpha=.3)
        ax.set(xlabel=label(name), ylabel=label(target))
        decorate(ax)
    fig.suptitle(f"{task_id} | UNPACKAGED: implicit candidate diagnostics\n"
                 "Existing generated labels only; these points are not verified function values", color=ORANGE, fontsize=13)
    save_figure(fig, destination, "diagnostic", atlas)
    fig, ax = plt.subplots(figsize=(5.5, 3.5), constrained_layout=True)
    ax.scatter(frame[features[0]], frame[target], s=3, color=ORANGE, alpha=.3)
    ax.set(xlabel=label(features[0]), ylabel=label(target), title=f"{task_id} | Unverified implicit labels")
    decorate(ax)
    save_figure(fig, destination, "preview")
    return {"kind": "unverified_candidate_diagnostic", "plots": ["diagnostic"], "primary": "diagnostic",
            "target": target, "label_unique_values": int(frame[target].nunique()),
            "meaning": "No explicit branch contract; showing saved candidate labels does not establish valid roots."}


def relative_url(path, parent):
    return Path(os.path.relpath(path, parent)).as_posix()


def make_gallery(items, output, package_root):
    cards = []
    for item in items:
        task_id = item["task_id"]
        directory = output / task_id
        images = "".join(f'<a href="{p}.png">{p} PNG</a> · <a href="{p}.pdf">PDF</a><br>' for p in item["plots"])
        package = package_root / task_id
        diagnostic_kind = item["kind"] == "unverified_candidate_diagnostic"
        verified = item["packaged"] and not diagnostic_kind
        if diagnostic_kind:
            package_link = ('<b class="warn">隐式诊断：未验证数值根分支，不能作为已确认真值</b>'
                            + (f' · <a href="{html.escape(relative_url(package / "task/instruction.md", directory))}">题目说明</a>'
                               if item["packaged"] else ''))
        elif item["packaged"]:
            package_link = f'<a href="{html.escape(relative_url(package / "task/instruction.md", directory))}">Harbor 题目说明</a>'
        else:
            package_link = '<b class="warn">未包装：隐式方程与数值记录待修复</b>'
        details = f'''<p>{html.escape(item['meaning'])}</p><p>{package_link}</p>
<p>{images}</p><details><summary>原始公式、参数和坐标范围</summary><pre>{html.escape(item['formula'])}</pre>
<pre>{html.escape(json.dumps(item['view_spec'], ensure_ascii=False, indent=2))}</pre></details>'''
        if item.get("diagnostic_report"):
            details += '<p class="warn">该候选尚未通过数值解确认。下方诊断说明了具体原因；图中原始候选点不能作为已验证的真实解使用。</p>'
            details += '<details><summary>数值诊断记录</summary><pre>' + html.escape(json.dumps(item["diagnostic_report"], ensure_ascii=False, indent=2)) + '</pre></details>'
        body = f'<p><a href="../index.html">← 全部题目</a></p><h1>{task_id}</h1>{details}'
        for p in reversed(item["plots"]):
            body += f'<a href="{p}.png"><img class="full" src="{p}.png"></a>'
        (directory / "index.html").write_text(html_page(task_id, body), encoding="utf-8")
        badge = "已包装" if verified else "需修复"
        kind = "ODE" if item["kind"] == "ode_ground_truth" else "隐式诊断" if diagnostic_kind else f'{item["view_spec"]["dimension"]}D 静态'
        cards.append(f'''<article data-subject="{item['subject']}" data-kind="{item['kind']}" data-search="{html.escape(task_id+' '+item['target'])}">
<a href="{task_id}/index.html"><img loading="lazy" src="{task_id}/preview.png" alt="{task_id}"></a>
<h3><a href="{task_id}/index.html">{task_id}</a><span>{badge}</span></h3>
<p>{kind} · {html.escape(item['target'])}</p></article>''')
    count = sum(item["packaged"] and item["kind"] != "unverified_candidate_diagnostic" for item in items)
    body = f'''<p class="eyebrow">SRBench v7 · Ground truth atlas</p><h1>公式图册与 Harbor 题包</h1>
<p>{len(items)} 个候选 · {count} 个题包 · 无噪声 · 每题 4,500 训练点 + 500 隐藏测试点</p>
<p>静态高维：固定未显示变量后画二维切片，并用三个背景取值画单变量剖面。ODE：画实际轨迹、目标导数和相图。
图中展示公式真值；隐式异常题展示原数据诊断。切片不能代表整个高维函数。</p>
<p><a href="atlas.pdf">下载完整 PDF 图册</a> · <a href="biology_overview.png">生物总览</a> ·
<a href="physics_overview.png">物理总览</a> · <a href="{html.escape(relative_url(package_root / 'packaging_report.json',output))}">包装报告</a></p>
<div class="controls"><input id="search" placeholder="搜索题号或变量名"><select id="subject"><option value="">全部领域</option><option>biology</option><option>physics</option></select>
<select id="kind"><option value="">全部类型</option><option value="static_ground_truth">静态函数</option><option value="ode_ground_truth">ODE</option><option value="unverified_candidate_diagnostic">异常诊断</option></select></div>
<main class="grid">{''.join(cards)}</main>
<script>function filter(){{const q=document.querySelector('#search').value.toLowerCase(),s=document.querySelector('#subject').value,k=document.querySelector('#kind').value;
document.querySelectorAll('article').forEach(a=>a.hidden=!(a.dataset.search.toLowerCase().includes(q)&&(!s||a.dataset.subject===s)&&(!k||a.dataset.kind===k)));}}
document.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',filter));</script>'''
    (output / "index.html").write_text(html_page("SRBench formula atlas", body), encoding="utf-8")


def html_page(title, body):
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>
*{{box-sizing:border-box}}body{{font:16px/1.65 system-ui,sans-serif;color:#183247;background:#f4f7fa;max-width:1600px;margin:auto;padding:32px}}
h1{{font-size:32px;margin:8px 0}}h3{{font-size:17px;margin:6px 0}}a{{color:#245a95;text-decoration:none}}a:hover{{text-decoration:underline}}
.eyebrow{{color:#61778b;font-size:13px;letter-spacing:2px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:20px}}
article{{background:white;border:1px solid #dce4ec;border-radius:12px;padding:16px}}article[hidden]{{display:none}}article img{{width:100%;height:auto}}article p{{margin:2px 0;color:#61778b}}
span{{float:right;font-size:12px;color:#61778b}}.controls{{display:flex;gap:12px;margin:25px 0}}input,select{{font:inherit;padding:8px 12px;border:1px solid #cad5df;border-radius:6px}}input{{flex:1}}
.full{{display:block;width:100%;background:white;margin:24px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:16px;border-radius:8px;font-size:13px}}
.warn{{color:#aa4920}}details{{margin:16px 0}}@media(max-width:600px){{body{{padding:16px}}.grid{{grid-template-columns:1fr}}.controls{{flex-wrap:wrap}}}}
</style><body>{body}</body></html>'''


def contact_sheet(items, output, filename, title, columns=4):
    rows = math.ceil(len(items) / columns)
    fig, panels = plt.subplots(rows, columns, figsize=(5.5 * columns, 3.5 * rows), squeeze=False)
    for ax, item in zip(panels.flat, items):
        ax.imshow(plt.imread(output / item["task_id"] / "preview.png"))
        ax.axis("off")
    for ax in list(panels.flat)[len(items):]: ax.axis("off")
    fig.suptitle(title, fontsize=20, color=INK)
    fig.tight_layout(rect=(0, 0, 1, .985), pad=.4)
    save_figure(fig, output, filename)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="default: RUN/03_plots/solution_YYYYMMDD")
    args = parser.parse_args(argv)
    run, packages = args.run.resolve(), args.packages.resolve()
    output = args.output.resolve() if args.output else plot_directory(run)
    entries = read_json(packages / "source_index.json") if (packages / "source_index.json").exists() else read_jsonl(run / "01_generated/index.jsonl")
    output.mkdir(parents=True, exist_ok=True)
    items = []
    with PdfPages(output / "atlas.pdf") as atlas:
        for entry in entries:
            task_id = entry["candidate_id"]
            destination = output / task_id
            destination.mkdir(exist_ok=True)
            package = packages / task_id
            packaged = (package / "manifest.json").exists()
            spec = read_json(package / "ground_truth.json")["spec"] if packaged else read_json(run / entry["spec"])
            if spec["integrator"] == "root_solve_implicit":
                metadata = unsupported_figure(task_id, entry, spec, run, destination, atlas)
            else:
                contract = contract_from_spec(spec)
                if contract.family == "static":
                    metadata = static_figures(task_id, spec, contract, destination, atlas)
                else:
                    if packaged:
                        train = pd.read_csv(package / "task/environment/train_data.csv").assign(partition="train")
                        test = pd.read_csv(package / "task/tests/test_data.csv").assign(partition="test")
                        frame = pd.concat([train, test], ignore_index=True)
                    else:
                        frame = pd.read_csv(run / entry["data_csv"]).assign(partition="candidate")
                    metadata = ode_figures(task_id, spec, contract, frame, destination, atlas)
            metadata.update(task_id=task_id, subject=entry["subject"], packaged=packaged,
                            formula=spec["rhs_for_integrator"],
                            view_spec={"axes": spec["independent_variables"], "parameters": spec.get("parameters", []),
                                       "dimension": len(spec.get("state_variables") or spec["independent_variables"]),
                                       "state_rhs": spec.get("state_rhs", []), "initial_conditions": spec.get("initial_conditions", {})})
            diagnostic = packages / "blocked_candidates" / f"{task_id}.json"
            if diagnostic.exists():
                metadata["diagnostic_report"] = read_json(diagnostic)
            write_json(destination / "plot_metadata.json", metadata)
            items.append(metadata)
            print(f"{task_id}: {metadata['kind']}", flush=True)
    for subject in sorted({item["subject"] for item in items}):
        selected = [item for item in items if item["subject"] == subject]
        contact_sheet(selected, output, f"{subject}_overview", f"{subject.title()} | {len(selected)} candidates | ground truth / diagnostic previews")
    examples = [item for task_id in ("biology_013", "biology_002", "physics_007", "physics_017")
                for item in items if item["task_id"] == task_id]
    if examples:
        contact_sheet(examples, output, "examples", "SRBench v7 | Ground truth examples", columns=2)
    make_gallery(items, output, packages)
    write_json(output / "atlas_manifest.json", {"n_candidates": len(items),
               "n_packaged": sum(i["packaged"] for i in items),
               "n_verified": sum(i["packaged"] and i["kind"] != "unverified_candidate_diagnostic" for i in items),
               "solver_evaluated": False, "items": [{k: v for k, v in i.items() if k not in ("formula", "view_spec")} for i in items]})
    print(output / "index.html", flush=True)


if __name__ == "__main__":
    main()
