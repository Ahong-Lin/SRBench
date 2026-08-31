# SRBench v6

SRBench 是一个用大语言模型生成符号回归候选题的流水线。它覆盖物理、生物和 AI Scaling Laws；方程演化与数据生成由 pipeline 完成，Harbor 出题和实际解题评测可在候选题生成后另行进行。

## 核心 Pipeline

普通学科从固定 taxonomy 开始：

```text
subject
  -> fixed subfields
  -> scientific scenarios
  -> gen0 equations
  -> evolve
  -> novelty_check
  -> DataGenSpec
  -> deterministic data generation
  -> 5,000-point candidate package
  -> human-chosen Harbor split and evaluation protocol
```

最终候选的完整流程为：

```text
gen0 -> gen1 -> ... -> gen5
  -> novelty_check
  -> if No: continue evolving until Yes or max-steps
  -> DataSpec Agent
  -> 5000 total points
  -> candidate package (formula, spec, CSV, lineage, novelty record)
```

`evolution_pipeline.py` 默认以 `candidate` 模式产出候选题。它以完整谱系为选择单位，而不是逐代单独接受题目；不会自动切分训练/测试数据，也不会调用 Harbor 或 solver。

## 演化机制

每一代在 `change_assumption` 与 `add_term` 之间选择。前者可在科学上合理时把原先固定的外部条件提升为一个可观测输入（静态模型），或把省略的内部量提升为 ODE state；后者不允许增加输入或 state，只能加入一个缺失的生成机制。场景还会声明 `dimension_track`：`fixed_univariate` 永不提升输入维度，`promotable_multivariate` 只允许有科学依据的条件/状态 promotion，`multiway` 用于本质上需要多量耦合的机制。

`add_term` 统一从跨学科 ontology 的结构角色中选择：`contribution`、`response_law`、`modulation`、`interaction`、`constraint`、`transition`、`feedback`、`heterogeneity`、`timescale`、`transport_balance`。`taxonomy/subfield_taxonomy_v1.json` 再为每个子领域提供具体机制菜单。每个 child 都保存 `evolution_contract`：操作、作用范围（unary/pairwise/multiway/state_coupling/time_forcing/memory）、结构角色、领域机制、前后片段、parent reduction、可观测 signature，以及为什么简单系数重拟合或轨迹拟合不能替代该机制。旧记录仍可读取，但新演化记录必须满足该契约。

`mechanism_ontology.py` 负责加载和校验跨学科 ontology；taxonomy 只负责领域语义。这样“加一项/改变假设”是统一演化主线，而不会把某一个领域概念（例如饱和）误套到所有学科。

## 可观测变化门（Observable Variation Gate）

生成数据后，`quality/observable_gate.py` 会在题目进入 Harbor 或 solver 前检查 ODE 目标是否已经在采样窗口内数值收敛到终值。它直接检查完整生成的 5,000 点候选数据；在 difficulty gate 模式则检查完整的 train/hidden 数据。静态函数不会被这个 gate 因为“饱和”而拒绝。该门只使用实际生成的 CSV，不修改方程或采样范围，并把 `observable_gate.json` 保存到每个 lineage attempt。难度门控的 sampling replan 后会再次检查。

判断采用一个直观的末段平台规则。令完整、有序 ODE 曲线的最后 `20%` 为 \(W_2\)，它前面的 `20%` 为 \(W_1\)，整段范围为 \(R=\max y-\min y\)：

\[
r_1=\frac{\operatorname{range}(W_2)}{R},\qquad
r_2=\frac{|\operatorname{median}(W_2)-\operatorname{median}(W_1)|}{R}.
\]

当 `r1 < 0.02` 且 `r2 < 0.02` 时，目标在可见采样窗内已近似水平，整条谱系会被拒绝并从 gen0 重新演化。整段为常数也会拒绝。它不使用 `(max-min)/max(|y|)`，不是函数复杂度分数；静态函数不因饱和而被这个 gate 删除。可用 `--observable-terminal-window-fraction` 与 `--observable-terminal-flatness-ratio` 调整阈值。

## 后续 Harbor 评测

候选题生成与 Harbor 评测刻意解耦。生成阶段保留完整公式、DataGenSpec、5,000 点 CSV、谱系和随机种子；研究者之后可根据研究问题手动决定 Harbor 的训练/测试划分，例如同域插值、单变量右侧外推、ODE 时间后段外推或条件组合外推。

当需要自动 Harbor 难度门控时，可显式使用：

```text
--mode difficulty_gate
```

它会将 5,000 点分为 4,500 个可见训练点和 500 个 hidden test 点，并计算：

```text
clipped_test_R2 = max(-1, min(raw_test_R2, 1))
```

决策逻辑：

```text
默认 `replan_once` policy：

```text
clipped test R2 <= 0.90  -> accept
clipped test R2 >  0.90  -> same equation, replan sampling range once
仍然 > 0.90              -> discard lineage and restart from gen0
```

`--difficulty-policy one_shot` 则不重规划：第一次 hidden R² 超过 `0.90` 就直接拒绝该 candidate。全 taxonomy 批处理默认使用此策略，随后继续下一个新 gen0，而不在同一题上反复尝试。
```

该 legacy 自动门控使用同一 spec 的独立随机抽样，因而是 IID 插值评测，不应被解释为外推评测。采样重规划只能修改已有独立变量的范围，不能修改方程、参数、噪声、初值或状态结构。

## 学科与 Taxonomy

`taxonomy/subfield_taxonomy_v1.json` 是固定的学科-子领域分类表。

- Physics 和 biology 使用 taxonomy 中固定的前 7 个 subfield。正式实验通常为每个 subfield 分配 10 个 scenario。
- AI 包含固定子领域 `scaling_laws`。
- AI 的 gen0 方程来自 `seeds/ai_scaling_laws_equations.jsonl`，不会重复调用 Stage-2/Stage-3 LLM，而是直接进入统一的 evolve pipeline。

AI 固定 seed 和普通 Stage-3 方程最终都输出为相同的 `equations.jsonl` 记录格式，因此可以用同一套演化和评分逻辑处理。

## Harbor 模板

`Harbor_example/` 是一个只包含任务骨架的本地模板。运行 pipeline 时使用：

```text
--harbor-template Harbor_example
```

当你决定把某个候选转换为 Harbor task 时，`harbor/` 会复制模板、接收你准备好的训练/测试 CSV，并写入：

- `environment/train_data.csv`：4500 个模型可见的训练点；
- `tests/test_data.csv`：500 个只由 verifier 读取的 hidden test 点；
- 根据当前 spec 更新后的变量名、目标名和严格的逐点 instruction；
- verifier 随机顺序逐点调用 `law([row])`，每一行在新 fork 的子进程内执行，并在评分期间暂存 hidden CSV；
- verifier 使用 hidden test 计算 raw test R2。

模板本身不需要携带训练数据、测试数据或参考 solution。模型在 Harbor 运行时负责生成自己的 `law.py` 和解释文件；builder 也不再额外写入 `srbench_manifest.json`。

## 核心模块

```text
auto_workflow.py              Stage 1-3：学科 -> 子领域 -> 场景 -> gen0 方程
equation_evolve.py            方程机制演化
novelty_check.py              新颖性判定（可独立运行）
evolution_pipeline.py         候选题总控；可选 legacy Harbor 难度门控
data_spec_agent_sdk.py        方程 -> DataGenSpec
data_generator/               按 spec 确定性生成数据
model_provider.py             Anthropic/OpenRouter 的认证、请求和重试适配层
harbor/                       `python -m harbor build/run`：构建并运行 Harbor task
quality/                      数据质量诊断与 parent-refit 诊断
tools/                        可选辅助工具，例如合并 equations.jsonl
taxonomy/                     固定学科与子领域
seeds/                        AI 固定 Scaling Laws gen0
```

`tools/merge_equations.py` 是可选工具，用于把多个学科的 Stage-3 `equations.jsonl` 合并成一个统一索引，不属于必须的评分步骤。

## 最小运行说明

安装项目依赖并准备 API key、Harbor CLI 和可用模型后：

```bash
# 生成普通学科的固定 taxonomy 方程
python auto_workflow.py \
  --subject physics \
  --scenarios 70 \
  --n-subfields 7 \
  --subfield-source fixed

# AI 直接导入固定 Scaling Laws gen0
python auto_workflow.py \
  --subject AI \
  --subfield-source fixed
```

随后从相应 `equations.jsonl` 选择一个 `scenario_id`，生成候选题：

```bash
python evolution_pipeline.py \
  --input <equations.jsonl> \
  --id <scenario_id> \
  --discipline <physics|biology|AI> \
  --steps 5 \
  --mode candidate \
  --n-total 5000
```

这会生成一份未评测的候选题，不会创建 4,500/500 split、Harbor task 或 solver 分数。模型通过 `--model`、`--spec-model` 和 `--novelty-model` 指定，不在代码中写死。

### Core taxonomy 批量实验

`scripts/run_full_taxonomy_pipeline.py` 是可恢复的首轮批调度器。它固定运行 Biology、Chemistry、Physics、Materials、Economy 的 taxonomy 顺序前 7 个子领域、每个子领域 10 个 scenario，另加 AI 的唯一 `scaling_laws` 子领域 10 个新生成 scenario：合计 **360 个 gen0**。AI 的 reviewed seed 目前只有 7 条；批处理显式使用 `--equation-mode generate` 在同一冻结子领域下生成 10 条新 scenario，而不是重复 seed。

先只打印计划：

```bash
python scripts/run_full_taxonomy_pipeline.py \
  --run-name full_taxonomy_v1 \
  --dry-run
```

批量生成候选题（每个 gen0 进入完整 evolve、novelty、DataSpec、5000 点生成和 Observable Gate）：

```bash
python scripts/run_full_taxonomy_pipeline.py \
  --run-name full_taxonomy_v1 \
  --mode candidate \
  --provider anthropic \
  --model <model>
```

需要真实 Harbor 难度门时，把 `--mode` 改为 `difficulty_gate`，再提供 `--solver-command`、`--harbor-template Harbor_example`。该 core batch 默认每个 gen0 只跑一条 lineage、只做一次 4500/500 single-row-isolated Harbor R² 评测；若 R² 超过 `0.90`，它直接拒绝该 gen0 并进入下一个，不做 sampling replan 或同题重演化。预期的科学 rejection 会继续下一题；Harbor、凭据、模型、代码或数据格式等 execution failure 默认立即停止并报告。仅在明确需要尽可能跑完所有题时，才添加 `--continue-on-error`。中断后用同一个 `--run-name --resume` 继续。每个 subject 的 gen0 checkpoint、每题 evolve 输出和 append-only `batch_ledger.jsonl` 都位于 `outputs/Core_Taxonomy/<run-name>/`。

## 输出

所有运行产物写入 `outputs/`，包括：

- Stage-2 场景和 Stage-3 方程；
- 演化谱系与 novelty 记录；
- 候选题的 DataGenSpec、`final_spec.json`、单份 5,000 点 CSV 和审计记录；
- 若后来选择运行 Harbor，则额外保存 Harbor task、solver raw R2 和 clipped test R2。

`outputs/` 是实验产物，默认不应提交到 GitHub。

## 环境与安全

- Python 环境需要支持 `numpy`、`scipy`、`sympy`，LLM 阶段还需要对应 provider SDK。
- API key 只能通过本地环境变量提供，不要写入仓库。
- Harbor 模板使用仓库相对路径，其他机器 clone 后可以直接重新生成数据。
- 本 README 只描述核心 pipeline；具体实验规模、模型选择和批量调度由实验 prompt 或外部脚本指定。
