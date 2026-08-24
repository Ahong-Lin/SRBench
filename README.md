# SRBench — 符号回归基准生成流水线（v6）

SRBench 是一套用大语言模型（LLM）自动构建 **符号回归（Symbolic Regression, SR）基准数据集** 的流水线。它从一个学科（如 physics / biology）出发，逐级生成子领域 → 场景 → 控制方程，再把方程"演化"得更复杂、更"新颖"，最后把方程变成可求解的**数值数据（CSV）**，供符号回归算法拟合与评测。

核心目标：产出的方程既 **科学合理**，又 **不能被直接背诵**（不是教科书公式），必须通过对数据的推断才能重新发现——这正是符号回归任务的价值所在。

---

## 目录

- [整体流程](#整体流程)
- [目录结构](#目录结构)
- [各模块功能](#各模块功能)
- [环境与依赖](#环境与依赖)
- [Provider 与模型配置](#provider-与模型配置)
- [快速开始（完整流水线）](#快速开始完整流水线)
- [门控演化：防止 parent 可替代 child](#门控演化防止-parent-可替代-child)
- [各阶段独立用法](#各阶段独立用法)
- [输出产物](#输出产物)
- [关键设计特性](#关键设计特性)
- [已知注意事项](#已知注意事项)

---

## 整体流程

基础流水线由一串可独立运行的命令行脚本组成，上游脚本把结果写入文件，
下游脚本用 `--input` / `--spec` 指向该文件继续处理。对于最终以模型实际解题
难度筛题的实验，使用 `evolution_pipeline.py` 作为 Stage 4–7 的总控入口：先完整
生成 `gen0 → gen5`，再以外部符号回归模型的 test R² 筛选。进程内耦合还包括
`auto_workflow.py` 的前三阶段，以及 `equation_evolve.py` 对 `novelty_check.py` 的调用。

```
 学科 subject
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  auto_workflow.py     （阶段 1–3，进程内串联）                  │
│                                                               │
│  [1/3] subject   → subfields   子领域（固定分类 / 生成 / 扩展） │
│  [2/3] subfield  → scenarios   场景（M2 风格：自然语言 + 规格）  │
│  [3/3] scenario  → equation    控制方程（sympy 表达式）         │
└─────────────────────────────────────────────────────────────┘
      │  equations.jsonl
      ▼
┌─────────────────────────────────────────────────────────────┐
│  equation_evolve.py   （阶段 4：方程演化）                      │
│    每步二选一：change_assumption（改假设重推） / add_term（加项）│
│    可选新颖性门控 ↕ 调用 novelty_check.py（阶段 5）             │
└─────────────────────────────────────────────────────────────┘
      │  evolution_*.jsonl
      ▼
┌─────────────────────────────────────────────────────────────┐
│  data_spec_agent_sdk.py  （阶段 6a：生成"数据生成规格"）        │
│    LLM + sympy 工具：判方程类型、纠正变量角色、选积分器、        │
│    定采样范围/参数、校验各项"可见性"（激励检查）→ DataGenSpec  │
└─────────────────────────────────────────────────────────────┘
      │  *_spec.jsonl
      ▼
┌─────────────────────────────────────────────────────────────┐
│  data_generator/generate_from_spec.py  （阶段 6b：出数据）      │
│    纯 numpy/scipy，按 integrator 求解 → CSV (+ PNG 图)          │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
   symbolic-regression 基准数据（CSV）
```

阶段 5（新颖性判定）有两种用法：作为独立 CLI 批量标注，或作为阶段 4 的**停止条件**内嵌运行。

### 最终难度门控：防止模型过于容易解题

`evolution_pipeline.py` 的选择单位是一整条谱系，而非每一代 child。它先从同一
`gen0` 连续演化到 `gen5`，再做 novelty check、生成数据并让指定的 Opus / GPT
符号回归评测器实际解题。只有该评测器的正式 `clipped test R²` 超过阈值时，才
允许一次受约束的采样区间重规划：

```text
gen0 → gen1 → gen2 → gen3 → gen4 → gen5
  → novelty_check（必须 Yes）
  → Spec Agent 生成 gen5 DataGenSpec（excitation_check 仍须通过）
  → 生成 5,000 点总数据：4,500 点训练数据 + 500 点独立 hidden test 数据
  → 外部 SR solver 计算 raw test R² → clip 到 [-1, 1]
       clipped test R² > 0.90：同一 gen5 一次“仅改 range”的采样重规划
                    → 重新生成数据并让同一 solver 重做
                    → 仍然 > 0.90：丢弃整条谱系，回到 gen0 重做 5 次演化
       clipped test R² ≤ 0.90：接受 gen5 为最终题
```

重规划锁定方程、变量集合、参数、噪声、初值、ODE 状态结构、采样密度与 scale；
只能修改既有独立变量的数值范围。重做谱系时会把“模型过易解题”的反馈传给
evolver，要求每个 parent→child 是实质性的机制差异，而非只调系数。每次谱系
尝试、novelty 判定、采样重规划和 solver 分数都会写入输出目录供审计。

---

## 目录结构

```
SRBench/
├── auto_workflow.py              # 阶段 1–3：学科→子领域→场景→方程（自带 LLM 调用）
├── equation_evolve.py            # 阶段 4：把一个方程演化成更复杂的方程谱系
├── merge_equations.py            # 合并多个学科的 Stage-3 方程 JSONL
├── novelty_check.py              # 阶段 5：判断方程是否"新颖"（可背诵 vs 需从数据发现）
├── data_spec_agent_sdk.py        # 阶段 6a：Agent 生成 DataGenSpec（数据生成规格，不算数据）
├── model_provider.py             # 共享的 LLM 传输层（anthropic / openrouter 适配）
├── use_openrouter.sh             # 配置 OpenRouter 环境变量的辅助脚本
├── taxonomy/
│   └── subfield_taxonomy_v1.json # 冻结的学科-子领域分类表（含 physics / biology / AI 等）
└── data_generator/
    ├── generate_from_spec.py     # 阶段 6b：按 spec 确定性地求解并输出 CSV
    ├── integrate_ode.py          # 参考实现：单个一阶 ODE 积分器（CLI）
    ├── integrate_system.py       # 参考实现：一阶 ODE 方程组积分器（CLI）
    ├── integrate_basset.py       # 参考实现：Basset 积分-微分方程（乘积积分 + 隐式欧拉）
    └── integrate_basset_abm.py   # 参考实现：分数阶 Basset（Adams-Bashforth-Moulton PECE）

outputs/                          # 所有产物（已 .gitignore，可由流水线重新生成）
```

> `data_generator/` 里的四个 `integrate_*.py` 是**独立的参考/演示 CLI**：它们把物理模型写死，可单独运行验证数值方法。`generate_from_spec.py`（阶段 6b）并不 import 它们，而是把同样的数值方案按 spec 重新实现了一遍。

---

## 各模块功能

### `auto_workflow.py` — 阶段 1–3（基准生成主体）
一个自包含脚本，通过 LLM 调用完成三步，并把结果**增量写盘**（中途失败也保留已完成部分），支持从 JSONL 检查点**断点续跑**。

- **阶段 1｜subject → subfields**，由 `--subfield-source` 决定来源：
  - `fixed`（默认）：从冻结分类表 `taxonomy/subfield_taxonomy_v1.json` 取**前 N 个**子领域（N 默认为该学科的 `default_n`），可复现。
  - `generate`：让模型现场划分一套新的子领域（数量可由 `sqrt(scenarios)` 附近随机 roll）。
  - `extend`：让模型提出 N 个**不重叠的新候选**子领域，仅写出供人工审核，**不生成场景/方程**。
- **阶段 2｜subfield → scenarios**（"M2"风格）：为每个子领域生成若干自然语言场景，含 `spec`（目标变量、输入变量及范围、期望/禁止行为、机制标签、函数族）。场景 ID 形如 `m2_{subfield}_{seed}_{idx:03d}`。
- **阶段 3｜scenario → equation**：为每个场景推导一个 **sympy 语法** 的控制方程；输出 `expression`、`symbols` 及每个符号的角色标注 `symbol_properties`（`O`=输出/目标、`V`=输入变量、`P`=参数）。

AI 的 `scaling_laws` 是 taxonomy 中的固定子领域，但采用固定 gen0 方程源：
`taxonomy/subfield_taxonomy_v1.json` 的 `fixed_equation_source` 指向
`seeds/ai_scaling_laws_equations.jsonl`。运行 `auto_workflow.py --subject AI
--subfield-source fixed` 时不会重复调用 Stage 2/3 LLM，而是将这 7 条经过审核的
Scaling Laws 直接写成同样的 `Scenarios/` 与 `Equations/` checkpoint，随后可以用
`evolution_pipeline.py` 与物理、生物完全相同地逐条进化。这样 AI 不是一套旁路格式，
最后可用 `merge_equations.py` 合并为一个统一的 equation index。

### `equation_evolve.py` — 阶段 4（方程演化）
取一个基准方程，逐步让它变复杂。每一步按加权硬币二选一：
- `change_assumption`：挑一个变量/参数，放宽或改变其物理假设，**重新推导**方程；
- `add_term`：加入一个新的函数项（阻尼、驱动、耦合、非线性、饱和、源汇……）。
每步输出喂给下一步，形成"世代谱系"。内置严格的符号一致性校验（角色唯一、无未声明/未使用符号、新符号必须给采样范围建议等）。

### `novelty_check.py` — 阶段 5（新颖性判定）
让 LLM 判定候选方程是否"科学新颖"，返回 `{"reasoning", "answer": "Yes"|"No"}`：
- `Yes` = 新颖，只能从实验数据推断出来；
- `No` = 经典/可背诵公式。
既可独立对整份方程文件批量打标（`--output` 写回增强文件），也被阶段 4 作为**停止门控**内嵌调用：从第 `--steps` 代起，每演化一步就判定一次，判为 `Yes` 即停（或达到 `--max-steps`）。

### `data_spec_agent_sdk.py` — 阶段 6a（数据生成规格 Agent）
把一条演化方程记录转成机器可读的 **`DataGenSpec`**（**只做规划，不算数据**）。上游表达式的"数学"可信，但"角色标注 / 方程类型"常有误，因此给 LLM 一组确定性的 sympy 工具去核对与纠正：
- 工具集：`analyze_expression`（结构分析）、`check_substitution`（数值代入检查）、`excitation_check`（**激励检查**：每一项、尤其本代新增项，必须在采样网格上把因变量抬动 ≥ `k·noise`，默认 `k=5`）、`auto_balance`（自动调系数让弱项可见）、`emit_data_gen_spec`（终止并产出规格）。
- 输出 `DataGenSpec` 关键字段：`equation_type`（explicit / implicit / ode1 / ode_higher / ode_system / delay_differential / integro_diff / unsupported）、`integrator`、独立变量与范围、固定参数、状态方程、初值、`noise`、`role_corrections`、`rationale` 等。
- 两条后端路径：`anthropic` 走官方 `claude_agent_sdk`（会启动 `claude` CLI 子进程）；`openrouter` 走纯 Python 的函数调用循环（无需 CLI）。

### `data_generator/generate_from_spec.py` — 阶段 6b（确定性出数据）
读取 `DataGenSpec`，**纯 numpy/scipy、无 LLM、可复现**。按 `integrator` 分派到六种数值后端，写出带表头的 CSV，并尽力生成一张诊断 PNG，附带一个廉价的数值健康检查：

| integrator | 用途 |
|---|---|
| `evaluate_explicit` | 显式 `y = f(x…)` 直接求值 |
| `root_solve_implicit` | 隐式 `g(y, x…)=0`，逐点 `fsolve` |
| `integrate_ode` | 一阶 ODE，`solve_ivp` RK45（rtol 1e-8 / atol 1e-10）|
| `integrate_system` | 一阶 ODE 方程组（高阶 ODE 降阶后也走这里）|
| `integrate_dde` | 标量定常时滞 DDE，步进法 + RK4 |
| `integrate_basset` | Basset 积分-微分方程（弱奇异记忆核，乘积积分）|

支持随机盒采样（多变量 explicit/implicit 且给了 `--n-total` 时）或规则网格；`noise` 为因变量上的**绝对**高斯标准差。

### `model_provider.py` — 共享 LLM 传输层
封装 Anthropic Messages API 与 OpenRouter OpenAI 兼容 `/chat/completions` 的差异，暴露统一的 `ModelCaller.complete()` / `openrouter_chat()` 与 `build_model_caller()` 工厂。被阶段 4/5/6a(openrouter) 使用。
> 注意：`auto_workflow.py` **没有** import 本模块，而是内置了一份等价的 `ModelCaller`。

### `taxonomy/subfield_taxonomy_v1.json` — 冻结分类表
taxonomy 包含 `biology`、`chemistry`、`physics`、`economy`、`materials` 和 `AI`。
前五个学科各列出 14 个子领域，`default_n=7`；`AI` 目前固定为一个
`scaling_laws` 子领域和 7 条文献锚定的 gen0 方程。普通学科的 `fixed` 模式从分类表
取子领域后调用 Stage 2/3；AI 的固定方程模式直接导入种子记录。文件被视为**只读冻结**：
扩展只能追加到末尾、不得改名/重排，`fixed` 模式下会记录其 SHA-256 以保证可复现。

---

## 环境与依赖

- **Python ≥ 3.10**（`claude_agent_sdk` 要求；文档提到一个 `srbench-agent` conda 环境）。
- **pip 依赖**：
  - `anthropic`、`httpx`、`pydantic` — 所有 LLM 阶段
  - `numpy`、`scipy`、`sympy` — 阶段 6a 的符号校验 + 阶段 6b 全部数值积分
  - `pandas` — **可选**，仅用于阶段 1–3 / 阶段 4 的 `.xlsx` 汇总表；缺失时自动跳过
  - `claude_agent_sdk` — **仅** 阶段 6a 的 `anthropic` 路径需要
- **外部服务/二进制**：
  - 一个 Claude 兼容端点（Anthropic 风格代理，或 OpenRouter），并配好密钥
  - **`claude` CLI**（`npm i -g @anthropic-ai/claude-code`）——**仅**阶段 6a 的 `anthropic` 模式需要，自动探测 `~/.npm-global/bin/claude`，也可用 `--cli-path` 指定

```bash
pip install anthropic httpx pydantic numpy scipy sympy pandas
# 仅阶段 6a 的 anthropic 路径需要：
npm i -g @anthropic-ai/claude-code
```

---

## Provider 与模型配置

每个调用模型的脚本都用 `--provider {anthropic,openrouter}` 选择协议（默认 `anthropic`）。

**anthropic（默认）**
```bash
export ANTHROPIC_API_KEY="sk-..."          # 或 ANTHROPIC_AUTH_TOKEN=...
export ANTHROPIC_BASE_URL="https://code.ppchat.vip/"   # 默认即此代理，可用 --base-url 覆盖
```
- 需要 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`；`--auth-source {auto,api_key,auth_token}` 决定用哪个（`auto` 优先 API key）。

**openrouter**
```bash
source env.sh            # 你自己的、被 .gitignore 的文件，内含 OPENROUTER_API_KEY
source use_openrouter.sh # 导出 OPENROUTER_BASE_URL 等
```
- 需要 `OPENROUTER_API_KEY`；base URL 默认 `https://openrouter.ai/api/v1`。

**模型选择**
- `--model` 默认 `claude-opus-4-7`，驱动阶段 1–3、演化、新颖性、规格 Agent。
- `auto_workflow.py` 额外有 `--equation-model`（阶段 3 单独用），`equation_evolve.py` 有 `--novelty-model`。
- 阶段 6b 不用任何模型。

> ⚠️ **OpenRouter 模型坑**：`use_openrouter.sh` 里设的 `OPENROUTER_MODEL`（如 `anthropic/claude-opus-4.8`）**不会被 Python 读取**——模型永远来自 `--model`（默认 `claude-opus-4-7`）。用 OpenRouter 时**必须**显式传 `--model <openrouter-slug>`，否则默认 slug 在 OpenRouter 端会失败。

---

## 快速开始（完整流水线）

以 Anthropic 默认 provider 为例：

```bash
export ANTHROPIC_API_KEY="sk-..."          # 或 ANTHROPIC_AUTH_TOKEN=...
export ANTHROPIC_BASE_URL="https://code.ppchat.vip/"

# 阶段 1–3：固定分类表切片 → 场景 → 方程
python auto_workflow.py --subject biology --scenarios 10 \
    --subfield-source fixed --run-name bio_seed0
# 产出：outputs/Equations/bio_seed0/equations.jsonl

# AI：从 taxonomy 指定的固定 seed 导入 7 条 Scaling Laws gen0（不调用 Stage 2/3 LLM）
python auto_workflow.py --subject AI --subfield-source fixed \
    --run-name ai_scaling_fixed
# 产出：outputs/Equations/ai_scaling_fixed/equations.jsonl

# 将不同学科的 Stage-3 方程合并成统一入口
python merge_equations.py \
    --input outputs/Equations/physics_7x10/equations.jsonl \
           outputs/Equations/biology_7x10/equations.jsonl \
           outputs/Equations/ai_scaling_fixed/equations.jsonl \
    --output outputs/Equations/combined_physics_biology_ai.jsonl

# 阶段 4（+ 内嵌阶段 5 新颖性门控）：演化其中一个方程
python equation_evolve.py \
    --input outputs/Equations/bio_seed0/equations.jsonl \
    --id m2_population_ecology_0_000 \
    --steps 5 --novelty-check
# 产出：outputs/Evolved_Equations/evolution_<base_id>_<ts>.jsonl

# 阶段 6a：为最终演化方程规划数据生成（Agent + sympy）
python data_spec_agent_sdk.py \
    --input outputs/Evolved_Equations/evolution_<base_id>_<ts>.jsonl --last
# 产出：outputs/Specs/evolution_<base_id>_<ts>_last_spec.jsonl

# 阶段 6b：确定性求解 → CSV
python data_generator/generate_from_spec.py \
    --spec outputs/Specs/evolution_<base_id>_<ts>_last_spec.jsonl
# 产出：outputs/data/<record_id>_gen<n>_<ts>.csv (+ .png)
```

**OpenRouter 变体**（每个调模型的阶段都要加 `--provider openrouter --model <slug>`）：
```bash
source env.sh && source use_openrouter.sh
python auto_workflow.py --subject biology --scenarios 10 --subfield-source fixed \
    --provider openrouter --model anthropic/claude-opus-4.8 --run-name bio_or
```

## 最终难度门控与 Harbor 出题

`evolution_pipeline.py` 的一个候选是完整谱系：先从 `gen0` 至少演化到 `gen5`，
从第 5 代起每代运行 `novelty_check`；若为 No 则继续演化，直到 Yes 或
`--max-steps`。通过后生成 5,000 点总数据（4,500 点
训练数据 + 500 点独立 hidden test 数据），并让调用方指定的模型在 Harbor 中解题。
正式筛选分数为
`clip(raw test R², -1, 1)`：若 `> 0.90`，同一公式只允许一次**仅改输入 range**
的重采样；仍然 `> 0.90` 时丢弃整个谱系、回到同一个 gen0 重新演化。打回反馈
要求每个 parent→child 有实质机制差异。

先指定一个已经在 Harbor 中跑通的 task 目录作为模板；模板是本地运行依赖，不必
上传 GitHub。其 Docker、task.toml 和 verifier 框架会保留，pipeline 自动替换
训练/隐藏测试 CSV、变量名和说明。对 ODE，自动排除 `<target>_noisy`，避免标签泄露。
Harbor 模型名不写死，完全由 `--solver-command` 中的 adapter 参数决定。

```bash
# 使用项目的完整依赖环境；不要使用缺 scipy/sympy 的系统 python。
PYTHON=python

# Anthropic 示例：先按你的环境设置密钥/代理。
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_BASE_URL="https://code.ppchat.vip/"

# Harbor CLI 的绝对路径（按本机环境调整）。
HARBOR=harbor
TEMPLATE=Harbor_example

# 每次尝试都完整演化 5 代；最多重做 4 条完整谱系。
# {task} 是 pipeline 自动导出的 Harbor 题目目录。Harbor verifier 的 reward.txt
# 会被 adapter 转为 raw_test_r2，供 pipeline 决定接受、重采样或重做谱系。
$PYTHON evolution_pipeline.py \
  --input outputs/Equations/biology_first7_k70_openrouter_seed0/equations.jsonl \
  --id m2_population_ecology_0_000 \
  --discipline biology \
  --steps 5 \
  --max-lineage-attempts 4 \
  --easy-r2 0.90 \
  --n-total 5000 --test-points 500 \
  --harbor-template "$TEMPLATE" \
  --solver-command "$PYTHON harbor_solver_adapter.py --task {task} --harbor-bin $HARBOR --agent claude-code --model claude-opus-4-8 --env daytona --job-name srbench_gate" \
  --seed 42
```

接受后输出目录含 `final_spec.json`、最终 Harbor task、4,500 点训练 CSV、500 点
hidden test CSV、每次尝试的 novelty 记录、采样重规划和 Harbor raw/clipped test R²。
Harbor agent 只能读取训练 CSV；500 点 hidden test 只由 verifier 读取。

若用 GPT-5.6 Sol，只需把 `--model claude-opus-4-8` 替换为实际 Harbor 可用的
GPT-5.6 Sol 模型名。OpenRouter 只需把上面 evolution/spec 阶段认证替换为：

```bash
source env.sh && source use_openrouter.sh
$PYTHON evolution_pipeline.py ... --provider openrouter --model anthropic/claude-opus-4.8
```

---

## 各阶段独立用法

```bash
# 只打印计划、不调用 API（试跑）
python auto_workflow.py --subject physics --scenarios 20 --dry-run

# 断点续跑（参数与 --run-name 必须与上次完全一致）
python auto_workflow.py --subject biology --scenarios 10 --subfield-source fixed \
    --run-name bio_seed0 --resume

# 让模型提议分类表扩展候选（供人工审核，不生成场景）
python auto_workflow.py --subject biology --scenarios 1 \
    --subfield-source extend --new-subfields 5

# 列出可演化的方程（不花 token）
python equation_evolve.py --input .../equations.jsonl --list

# 独立跑新颖性判定并写回增强文件
python novelty_check.py --input .../evolution_xxx.jsonl --output eq.novelty.jsonl

# 阶段 6a 内置演示（一个故意标错角色的方程，无需 --input）
python data_spec_agent_sdk.py --demo

# 阶段 6b：只跑某一条 spec、自定输出目录、重设采样点数
python data_generator/generate_from_spec.py --spec specs.jsonl --index 0 \
    --output-dir outputs/foo --n-total 500

# 数据生成参考 CLI（写死物理模型，用于验证数值方法）
python data_generator/integrate_ode.py --plot
python data_generator/integrate_system.py --plot
python data_generator/integrate_basset.py --params "K_B=0.5, n_pl=0.8" --t1 8 --n 2000 --plot
python data_generator/integrate_basset_abm.py --selftest    # 仅解析解自检，不出数据
```

---

## 输出产物

所有产物都落在仓库根的 `outputs/` 下（**已 gitignore**）：

```
outputs/
├── Scenarios/<run_name>/
│   ├── subfields.json            # 本次用到的子领域
│   └── scenarios.jsonl           # 生成的场景（含 spec）
├── Equations/<run_name>/
│   ├── equations.jsonl           # 成功推导的方程
│   ├── equation_failures.jsonl   # 失败记录（可 --resume 重试）
│   ├── pipeline.xlsx             # 场景+方程 join 的人工审阅表（需 pandas）
│   ├── run_meta.json             # 配置 + 状态 + 计数（断点续跑用）
│   └── progress.json             # 实时进度
├── Evolved_Equations/
│   └── evolution_<base_id>_<ts>.jsonl(+.xlsx)   # 演化谱系（gen0=原方程）
├── Specs/
│   └── <input-stem>_spec.jsonl   # 阶段 6a 的 DataGenSpec
└── data/
    ├── <record_id>_gen<n>_<ts>.csv(+.png)       # 阶段 6b 的数值数据
    └── generation_failures.jsonl                # 逐条失败记录

taxonomy/candidates/<subject>_extensions_<ts>.json   # extend 模式的候选（待人工审核）
```

CSV 列：各独立变量 → 因变量 →（当 `noise>0`）`<dep>_noisy`；ODE 方程组会输出全部状态列。

---

## 关键设计特性

- **增量写盘 + 断点续跑**：阶段 1–3 全程 JSONL 检查点，`--resume` 会用 `run_meta.json` 做**配置漂移校验**（学科、seed、模型、provider、`batch_size`、`fixed` 模式下的分类表 SHA-256 等任一不符即中止），杜绝"续跑却悄悄改了实验条件"。
- **可复现**：`fixed` 模式取分类表前 N 项、`--seed` 固定随机 roll 与配额洗牌、阶段 6b 用 `default_rng(seed)`；分类表哈希入库。
- **新颖性门控**：把"是否需要从数据发现"变成可自动判定的停止条件，保证基准方程不是可背诵的教科书公式。
- **激励检查（excitation check）**：阶段 6a 强制每一项、尤其新增项，在采样区间内能把因变量抬动到噪声之上（默认 5σ），避免生成"看不出来"的无效项；必要时 `auto_balance` 自动调系数。
- **规划与执行分离**：阶段 6a（LLM 决定"算什么、怎么积分"）与阶段 6b（纯数值确定性执行）解耦——数据完全可复现、可独立复核。
- **双 Provider**：Anthropic 与 OpenRouter 二选一，同一套脚本通用。
- **容错**：每个模型调用都有带退避的重试；单条方程/单条 spec 失败只记录到 `*_failures.jsonl`，不中断整批。

---

## 已知注意事项

以下是阅读/运行代码时值得留意的点（源自对现有代码的核对）：

- **默认 Anthropic base URL 是代理** `https://code.ppchat.vip/`，并非 `api.anthropic.com`；如需直连请用 `--base-url` 或 `ANTHROPIC_BASE_URL` 覆盖。
- **默认模型是 `claude-opus-4-7`**（脚本内硬编码默认值）。
- **`OPENROUTER_MODEL` 不被 Python 读取**（见上文 OpenRouter 坑）。
- **分类表无 `example_phenomena` 字段**，但 `auto_workflow.py` 的 `--taxonomy-context` 默认 `name_description_examples` 会去读它——因此 `fixed` 模式下 "examples" 部分实际为空；这与分类表自带的 `prompt_context`（主实验只用子领域名）说明也略有出入。
- **`auto_workflow.py` 自带一份 `ModelCaller`**，未复用 `model_provider.py`（两者行为等价但独立维护）。
- **阶段 6a 的 `anthropic` 路径依赖 `claude` CLI 子进程**；若只想纯 Python，请用 `--provider openrouter`。
- **`data_generator/` 的 `integrate_*.py` 注释/日志为中文**，且默认输出目录写在 `data_generator/outputs/ode_data/`（与其 docstring 里旧路径描述不一致，以代码为准）。
- **阶段 6b 并不 import** `integrate_basset.py` 等参考 CLI，而是把同样的数值方案在 `generate_from_spec.py` 内**重新实现**（spec 驱动、符号化推导力项）。
- **无并发**：各阶段均为顺序循环；`--batch-size` 只是"每次 API 调用请求多少个场景"，不是并行度。
- 阶段 6a 文档提到的 "Stage 6c"（消费 `sanity_expectations` 做校验）在当前仓库中**尚无对应脚本**。
