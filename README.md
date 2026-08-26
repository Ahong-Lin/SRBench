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

每一代在 `change_assumption` 与 `add_term` 之间选择。前者可在科学上合理时把原先固定的外部条件提升为一个可观测输入（静态模型），或把省略的内部量提升为 ODE state；后者不允许增加输入或 state，只能加入一个缺失的生成机制。

`add_term` 统一从六类机制中选择：非线性响应、相互作用、容量约束、异质性调制、反馈/竞争、regime crossover。随后按学科注入具体菜单：Physics 的本构/耦合机制、Biology 的资源/调控机制，或 AI Scaling Laws 的有效数据、容量、计算和优化机制。每个 add-term child 都保存 `add_term_audit`：机制类别、因果主张、回到 parent 的极限，以及可观测的数据特征。

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
clipped test R2 <= 0.90  -> accept
clipped test R2 >  0.90  -> same equation, replan sampling range once
仍然 > 0.90              -> discard lineage and restart from gen0
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
- 根据当前 spec 更新后的变量名、目标名和 instruction；
- verifier 使用 hidden test 计算 raw test R2。

模板本身不需要携带训练数据、测试数据或参考 solution。模型在 Harbor 运行时负责生成自己的 `law.py` 和解释文件。

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
