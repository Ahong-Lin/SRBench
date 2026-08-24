# SRBench v6

SRBench 是一个用大语言模型生成符号回归基准题目的流水线。它覆盖物理、生物和 AI Scaling Laws，并把方程演化、数据生成、Harbor 出题和实际解题难度筛选统一起来。

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
  -> Harbor task
  -> external symbolic-regression solver
  -> clipped test R2
```

最终候选的完整流程为：

```text
gen0 -> gen1 -> ... -> gen5
  -> novelty_check
  -> if No: continue evolving until Yes or max-steps
  -> DataSpec Agent
  -> 5000 total points
       4500 visible training points
        500 hidden test points
  -> Harbor solver
  -> raw test R2
  -> clip(raw R2, -1, 1)
```

`evolution_pipeline.py` 是最终难度筛选的总控入口。它以完整谱系为选择单位，而不是逐代单独接受题目。

## 难度门控

正式指标是独立 hidden test 上的：

```text
clipped_test_R2 = max(-1, min(raw_test_R2, 1))
```

决策逻辑：

```text
clipped test R2 <= 0.90  -> accept
clipped test R2 >  0.90  -> same equation, replan sampling range once
仍然 > 0.90              -> discard lineage and restart from gen0
```

采样重规划只能修改已有独立变量的范围，不能修改方程、参数、噪声、初值或状态结构。重做谱系时要求 parent 和 child 具有实质性的机制差异，而不是只改变系数或做等价改写。

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

`harbor_task_builder.py` 会为每个候选自动生成一个新的 Harbor task，并写入：

- `environment/train_data.csv`：4500 个模型可见的训练点；
- `tests/test_data.csv`：500 个只由 verifier 读取的 hidden test 点；
- 根据当前 spec 更新后的变量名、目标名和 instruction；
- verifier 使用 hidden test 计算 raw test R2。

模板本身不需要携带训练数据、测试数据或参考 solution。模型在 Harbor 运行时负责生成自己的 `law.py` 和解释文件。

## 核心模块

```text
auto_workflow.py              Stage 1-3：学科 -> 子领域 -> 场景 -> gen0 方程
equation_evolve.py            方程机制演化
novelty_check.py              新颖性判定
evolution_pipeline.py         完整谱系、DataSpec、Harbor 和难度门控总控
data_spec_agent_sdk.py        方程 -> DataGenSpec
data_generator/               按 spec 确定性生成数据
harbor_task_builder.py        生成 Harbor 格式任务
harbor_solver_adapter.py      调用 Harbor 并读取 verifier R2
taxonomy/                     固定学科与子领域
seeds/                        AI 固定 Scaling Laws gen0
```

`merge_equations.py` 是可选工具，用于把多个学科的 Stage-3 `equations.jsonl` 合并成一个统一索引，不属于必须的评分步骤。

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

随后从相应 `equations.jsonl` 选择一个 `scenario_id`，调用：

```bash
python evolution_pipeline.py \
  --input <equations.jsonl> \
  --id <scenario_id> \
  --discipline <physics|biology|AI> \
  --steps 5 \
  --harbor-template Harbor_example \
  --solver-command '<Harbor solver command>'
```

模型通过 `--model`、`--spec-model`、`--novelty-model` 以及 Harbor solver 参数指定，不在代码中写死。

## 输出

所有运行产物写入 `outputs/`，包括：

- Stage-2 场景和 Stage-3 方程；
- 演化谱系与 novelty 记录；
- DataGenSpec、训练数据和 hidden test 数据；
- Harbor task、solver raw R2 和 clipped test R2；
- 最终接受题目的 `final_spec.json` 和审计记录。

`outputs/` 是实验产物，默认不应提交到 GitHub。

## 环境与安全

- Python 环境需要支持 `numpy`、`scipy`、`sympy`，LLM 阶段还需要对应 provider SDK。
- API key 只能通过本地环境变量提供，不要写入仓库。
- Harbor 模板使用仓库相对路径，其他机器 clone 后可以直接重新生成数据。
- 本 README 只描述核心 pipeline；具体实验规模、模型选择和批量调度由实验 prompt 或外部脚本指定。
