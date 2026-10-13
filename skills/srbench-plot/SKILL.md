---
name: srbench-plot
description: 为 SRBench/Harbor 题目生成真值图或 LLM 与 ground truth 对比图，复用已有预测缓存，支持一维、二维曲面和三维以上静态函数，并采用 0920 的无 residual 展示风格。
---

# SRBench plotting

Use the repository plotting implementation as the source of truth. This skill is
for inspecting generated formulas and comparing an existing `law.py` with a
packaged task. It does not regenerate equations, rerun evaluations, or change
official scores.

## Choose the input

- Generated tasks only: use the generated run and its packaged task directory.
- Model comparison: use a packaged task and the existing `predictions.csv` and
  `metrics.json` when they already exist. A presentation change must not call
  the model again.
- A Harbor evaluation directory can be mapped to its task package and cached
  prediction folders; preserve the original task and run identifiers.

Use date-only plot roots:

```text
03_plots/solution_YYYYMMDD/       # ground truth only
03_plots/LLM_vs_truth_YYYYMMDD/   # model versus ground truth
```

## Ground-truth atlas

For a generated run and its package directory:

```bash
python -m srbench.plotting.atlas \
  --run outputs/<run> \
  --packages outputs/<run>/02_packaged/YYYYMMDD \
  --output outputs/<run>/03_plots/solution_YYYYMMDD
```

The atlas is authoritative for formula inspection. Static multivariate plots
are conditional slices: unshown inputs are fixed at declared normalized
positions. They are not marginal averages and do not represent the whole
high-dimensional function. ODE plots use the integrated trajectory and keep
the original initial conditions.

## Compare a model

For a single task, use the standard comparison command:

```bash
python -m srbench plot \
  --package outputs/<run>/02_packaged/YYYYMMDD/<task_id> \
  --law /path/to/law.py \
  --output outputs/<run>/03_plots/LLM_vs_truth_YYYYMMDD/<task_id>
```

The standard figure has blue ground truth, orange LLM solution, visible train
and test counts, and a pale-pink held-out region. Residuals may remain in
`predictions.csv` and metrics, but are not drawn. Use the verified test score
in the title when a score is available:

```bash
python -m srbench plot ... --model gpt-5.6-sol --score 0.90349
```

For exactly two independent static inputs, `srbench plot` also writes
`spatial.png` and `spatial.pdf` using the 0920 layout:

- top row: truth and prediction sampled in the same input coordinates;
- bottom row: blue/orange triangulated surfaces with shared target limits;
- the held-out sample hull is shown in pale pink;
- triangles crossing the train/test interface are masked;
- the figure is a visualization, not a replacement for the official metric.

To compare two independent runs in the same 0920-style figure, use the
bundled helper (the two runs must contain the same two feature columns):

```bash
python skills/srbench-plot/scripts/plot_two_runs_spatial.py \
  --predictions path/to/run_01/predictions.csv path/to/run_02/predictions.csv \
  --features x1 x2 --labels run_01 run_02 \
  --output outputs/<plot_dir>/history_002
```

The resulting `two_runs_spatial.png` is a 2x4 figure: each run has sampled
truth values, sampled LLM values, a blue truth surface, and an orange LLM
surface. Truth and prediction share a color scale within each run; different
runs may use different scales. The pink floor/hull marks held-out samples.
This helper only restyles cached predictions and never averages or rescoring
runs.

## Three or more inputs

Do not connect arbitrary multivariate rows into a fake one-dimensional curve.
Use the supplied cached predictions and the bundled helper for a comparison
overview:

```bash
python skills/srbench-plot/scripts/plot_cached_highdim.py \
  --predictions outputs/<plot_dir>/predictions.csv \
  --features x1 x2 x3 [x4 ...] \
  --output outputs/<plot_dir> \
  --title '<task_id> | <run> | test R² = <score>'
```

The helper normalizes coordinates only for display and records the original
min/max values. It uses the first two inputs as surface coordinates and
selects a narrow band of existing rows for the other inputs:

- three inputs: conditioning values near normalized `0.2`, `0.5`, and `0.8`;
- four or more inputs: low/high combinations near `0.2` and `0.8` for the
  first two conditioning inputs, while any remaining inputs are near the
  midpoint of the selected band.

Each condition produces a blue ground-truth and orange LLM triangulated
surface. Held-out points are shown on a pale-pink floor/hull, and triangles
that cross the train/test boundary are masked. The output is
`conditional_slices.png` (also copied to `highdim.png` for gallery
compatibility), with `highdim_metadata.json` recording the condition values,
band size, and original coordinate ranges. It never displays a residual
panel. These are conditional-band surfaces from sampled data, not a complete
d-dimensional surface or a newly evaluated grid.

## Reuse and naming rules

- `solution_YYYYMMDD` is for formula inspection only.
- `LLM_vs_truth_YYYYMMDD` is for a model comparison.
- Keep repeated trials below the existing evaluation name, for example
  `history/history_003/run_01`.
- Reuse cached predictions for styling changes. Do not rescore or overwrite an
  evaluated directory merely to change colors or panels.
- Keep raw R², RMSE and failure information in `metrics.json`; plotting must
  not hide nonfinite predictions or silently drop rows.
