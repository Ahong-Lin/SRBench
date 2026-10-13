---
name: srbench-harbor-pack
description: 将 SRBench 生成的公式或 DataGenSpec 封装为 Harbor 符号回归任务，并对比模型提交的 law.py 与 ground truth。适用于任意输入维数的显式静态函数、带导数目标的闭合 ODE 系统、单题或整批题目包装、5000 点训练外推划分，以及参考解与预测结果绘图。使用仓库内确定性命令完成包装，不重新演化公式。
---

# SRBench Harbor packaging

Use the v7 package implementation as the single source of truth. Read [the task contract](references/task-contract.md) when resolving symbol roles, split geometry, or output paths.

## Locate the implementation and input

1. Resolve this skill's real path (it may be a symlink); the repository is two levels above its directory. Confirm `pyproject.toml` and `src/srbench/packaging/pipeline.py` exist. An installed `srbench` package is also usable.
2. Use a Python environment containing this project. If needed, install it with `python -m pip install -e /path/to/llm-srbench-v7`.
3. Identify the requested run, candidate directory, or spec JSON. A generated candidate has `equation.json`, `spec.json`, `data.csv` and `lineage.jsonl`. The spec fixes the formula, parameters, variable roles and domain.
4. Read the declared inputs and target from the spec. Never infer features by taking every CSV column except the target; noisy labels and auxiliary outputs are not extra features.

## Package

Name batch directories by date only: `02_packaged/YYYYMMDD/`. Do not add prefixes such as `current_blind_`. The run command defaults to the local date. On same-day collisions, use `--resume` only for identical packages; never overwrite differing packages silently. An explicitly requested path takes precedence.

Default to 5,000 total points: 4,500 training and 500 hidden evaluation points. Both partitions contain exact formula outputs with no observation noise. The implementation ignores legacy nonzero `noise` settings and never selects a `_noisy` label column.

Solver instructions disclose input/target names and roles, training observations, and the submission contract, but not full sampling ranges, coordinate scales, hidden boundaries, split geometry or the 90/10 allocation rule. The evaluator independently applies the submitted function to the hidden inputs. Keep range/split metadata for packaging and plotting outside the solver environment. Preserve already evaluated task versions when revising instructions; write revised copies to a new dataset directory so recorded scores still refer to their original prompts.

Single spec:

```bash
python -m srbench package --spec /path/to/spec.json \
  --output outputs/manual/02_packaged/task_name \
  --n-total 5000 --test-points 500 --seed 0
```

Whole generation run:

```bash
python -m srbench package --run bio_phys_30 \
  --n-total 5000 --test-points 500 --seed 0
```

For a candidate folder use `--candidate /path/to/01_generated/candidate_id`.
To reuse existing partitions, pass both `--train-csv` and `--test-csv` for a single task. Otherwise packaging regenerates the split using the spec's unchanged formula, parameters and domain, with noise disabled; it does not partition the old candidate CSV. Supplied target columns must already match formula truth; mismatched labels are rejected.

Use `--resume` to reuse identical completed packages. The command checks configuration and artifact hashes; select a new output directory for a different split. Do not edit formulas or secretly change the domain to make an oracle test pass.

The implementation creates the reference solution, checks its values against clean mathematical truth, and writes portable metadata. It does not estimate model difficulty. An unsupported implicit equation needs an explicit branch or an appropriate row-wise observable before it can be packaged.

## Compare a submitted law

For a dedicated plotting workflow, use the companion [srbench-plot](../srbench-plot/SKILL.md)
skill. The commands below remain the deterministic packaging-integrated entry
point for a single comparison.

```bash
python -m srbench plot \
  --package outputs/manual/02_packaged/task_name \
  --law /path/to/model/law.py
```

The default covers both train and test. Use `--partition test` for a faster hidden-set-only comparison. The package supplies ground truth; no second answer file is required. An explicit `--reference` is checked against the packaged formula.

The command writes PNG, PDF, predictions CSV and metrics JSON under `03_plots/LLM_vs_truth_YYYYMMDD/task_name`. Treat nonfinite outputs and execution failures as failures; never score only the rows that survived.

### Plot directories and repeated evaluations

Use the local plot creation date, formatted `YYYYMMDD`, with exactly these prefixes:
- Ground truth only, for inspecting generated tasks: `03_plots/solution_YYYYMMDD/`.
- Ground truth versus model submissions: `03_plots/LLM_vs_truth_YYYYMMDD/`.

The atlas and comparison commands use these defaults; an explicit output path takes precedence. Group multiple datasets below the dated directory. For repeated history experiments, use `history/history_001/run_01`, `history/history_001/run_02`, through `history_005`, with a joint index, score table and per-task comparison. Preserve the original evaluation directory/trial identifiers and prompt versions in provenance; do not mix repetitions or overwrite different submissions. Reuse cached predictions for presentation-only changes. Archive superseded galleries within the appropriate dated directory, and update links and embedded paths when moving artifacts.

### Plot presentation

Use the existing `srbench.plotting.figures.make_figure` implementation. The default is a single truth/prediction overlay, without residual or parity panels: blue ground truth, orange LLM solution, and a pale-pink background for the test region on the right. Keep the train/test labels and counts visible.

For one-dimensional functions and single ODE trajectories, use the actual input/time coordinate when train and test form ordered, disjoint intervals. For multivariate or interleaved data, place train samples first and test samples last, sorting by ground truth separately within each partition; label the horizontal axis as sample rank, not a physical coordinate. Never connect multivariate samples into a supposed function curve or infer a spatial boundary from the 90/10 row ratio.

Preserve the sampling coordinate scale. Use `plot_metadata(split, ground["spec"])` before plotting: provided CSV split manifests may omit log-scale information that is still declared in the spec. Explain that counts describe samples, while widths on a physical axis describe coordinate intervals.

For two-input static functions, also generate `spatial.png` and `spatial.pdf` with `make_spatial_figure`. These compare truth and prediction on actual input coordinates, using heatmaps of sampled values with a common color scale, plus blue/orange triangulated surfaces with identical value limits. Mark the test sample hull in pink; this is an empirical footprint, not an inferred exact domain boundary. Surfaces interpolate cached samples for visualization, mask triangles crossing the train/test interface, and do not change evaluation scores. For more than two independent inputs, use conditional slices only when the other coordinates are explicitly fixed and both laws are evaluated there; label projected sample plots as projections rather than complete function surfaces.

Use `--title`, `--model` and `--score` to retain the task/model and verified test R² in the title. When only the presentation changes, reuse existing `predictions.csv` and `metrics.json` with `make_figure` rather than executing the submitted law again. Refresh any associated gallery and PDF so they show the same presentation. Residual values may remain in the predictions CSV; they are not plotted by default.

## Report

Provide the package path, actual row counts, split definition, oracle results, and comparison metrics if requested. Link the plot when available. Distinguish oracle correctness from actual model performance.

Harbor consumes the inner `task/` directory, or the `harbor_dataset/` directory of relative task links created by batch packaging. Its environment receives only training data. Keep ground truth and reference files out of the solver's build context. A packaging request does not itself request paid model generation or a Daytona evaluation run.
