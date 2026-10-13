# LLM-SRBench v7

**生成公式 → 包装 Harbor 题目 → 对比模型答案与 ground truth。** 三个阶段分开运行，公式生成使用最后讨论的“自然释放自由度”版本。

## 先运行

```bash
conda activate srbench-agent
cd "/Users/hubertlinhong/Desktop/北京大学/2026春季学期/Benchmark/llm-srbench-v7"
python -m pip install -e .
```

如果使用 Anthropic 的 DataSpec agent，需要 `python -m pip install -e '.[agent]'`；现有 `srbench-agent` 环境已包含这个 SDK。OpenAI 和 OpenRouter 使用 Python 工具循环，无需 Claude CLI 或额外安装 OpenAI SDK。密钥通过 shell 环境传入，参见 `.env.example`；程序不会自动读取 `.env`。

各生成阶段（场景、初始方程、演化、novelty、DataSpec）统一遵循 `--base-url` 优先、所选服务环境变量其次的配置顺序。使用 `--provider openai --model gpt-5.6-sol` 时，只读取 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`；地址既可写到 `/v1`，也可写完整 `/v1/chat/completions`。未设置地址时使用 `https://api.openai.com/v1`。代理地址与密钥必须属于同一个服务。

`--model` 同时用作初始生成、演化、novelty 和 DataSpec 的模型；可用 `--spec-model`、`--novelty-model` 单独覆盖。`--auth-source` 只影响 Anthropic。OpenAI 请求使用 `max_completion_tokens`，模型 ID 原样发送，不会替换模型。

OpenAI/OpenRouter 默认读取超时为 300 秒、暂时性网络/服务错误最多重试 1 次；分别用 `SRBENCH_OPENAI_READ_TIMEOUT`、`SRBENCH_OPENAI_MAX_RETRIES` 调整，OpenRouter 则替换变量名中的 `OPENAI`。读取超时限制的是等待后续响应数据的时间，不是整条谱系的总时长。HTTP 日志记录开始、结束、耗时、状态码或异常类型。服务错误不会再进入公式 JSON/结构纠错循环；认证等非暂时性错误直接停止。

## 生物、物理各试跑一个公式

在 `.env` 中填写以下两个变量（已有配置时直接使用，不要用模板覆盖 `.env`）：

```dotenv
OPENAI_API_KEY="你的密钥"
OPENAI_BASE_URL="与你的密钥匹配的服务地址/v1"
```

加载环境后运行：

```bash
set -a
source .env
set +a

python -m srbench generate \
  --subjects biology physics \
  --target-per-subject 1 --batch-size 1 --n-subfields 1 \
  --max-rounds 1 --max-lineage-attempts 1 \
  --steps 5 --max-steps 15 --n-total 5000 \
  --seed 20260917 \
  --provider openai --model gpt-5.6-sol \
  --run-name smoke_gpt56sol_bio_phys_20260917
```

这轮只尝试每领域一个初始公式和一条演化谱系，首个子领域分别为种群生态学、经典力学；若现有筛选拒绝候选，程序会报告未达标，不能保证一定产出两个公式。成功后，每个公式在 `outputs/smoke_gpt56sol_bio_phys_20260917/01_generated/` 下有公式、谱系、数值配置和 5,000 行 `data.csv`。这是生成结果，尚未按训练/测试划分，也没有测量模型求解难度。

对成功生成的结果包装为每题 4,500 个训练点、500 个外推测试点：

```bash
python -m srbench package \
  --run smoke_gpt56sol_bio_phys_20260917 \
  --n-total 5000 --test-points 500 --seed 20260917
```

中断后使用完全相同的生成命令加 `--resume`；新的一轮用新的 `--run-name`。本地这三个阶段不需要 `DAYTONA_API_KEY`。已生成数据与包装数据使用各自的采样过程，包装不会重新演化公式。

## 正式批量生成

生物、物理各收集 30 个通过现有检查且未被结构去重排除的公式：

```bash
python -m srbench generate \
  --subjects biology physics \
  --target-per-subject 30 --batch-size 30 --n-subfields 7 \
  --steps 5 --max-steps 15 --max-lineage-attempts 4 --max-rounds 10 \
  --n-total 5000 --seed 20260917 \
  --provider openai --model gpt-5.6-sol \
  --run-name bio_phys_30_gpt56sol
```

这条命令在生物、物理各 7 个子领域中采样，目标是每领域收集 30 个合格公式，每式 5,000 点。现有拒绝、去重和有限轮次预算仍然适用，不能保证预算内一定收齐。CLI 的缺省值仍是 Anthropic/Claude；使用 GPT 时请保留 `--provider openai --model gpt-5.6-sol`。

### 并行生成：本地进程或 Daytona

`--batch-size 30` 表示每轮最多 30 个初始候选。`--workers 5` 才表示最多同时演化 5 条谱系；缺省仍为 1。每条谱系内部按 `E0 → E1 → … → novelty → DataSpec → 5,000 点` 顺序推进，不同谱系可以同时运行。

| 参数 | 执行方式 |
|---|---|
| `--executor local --workers 5` | 本地启动最多 5 个独立 Python 进程，并发请求模型 |
| `--executor daytona --workers 5` | 同时运行最多 5 个 Daytona sandbox，每条谱系单独一个 sandbox |
| `--executor daytona --workers 30` | 最多 30 个并发 sandbox；需要模型服务和 Daytona 账户都允许相应并发 |

Daytona 生成执行器需要安装一次可选依赖并加载环境：

```bash
python -m pip install -e '.[daytona]'
set -a
source .env
set +a
```

`.env` 需要 `DAYTONA_API_KEY`、`OPENAI_API_KEY`，代理服务还需要匹配的 `OPENAI_BASE_URL`。可选 `DAYTONA_API_URL`、`DAYTONA_TARGET` 指定 Daytona 服务和区域。当前 Daytona 生成执行器支持 OpenAI/OpenRouter；Anthropic 仍可使用本地执行器。

已有 `bio_phys_30_gpt56sol` 记录可以直接切换为以下配置续跑：

```bash
python -m srbench generate \
  --subjects biology physics \
  --target-per-subject 30 --batch-size 30 --n-subfields 7 \
  --steps 5 --max-steps 15 --max-lineage-attempts 4 --max-rounds 10 \
  --n-total 5000 --seed 20260917 \
  --provider openai --model gpt-5.6-sol \
  --executor daytona --workers 5 \
  --run-name bio_phys_30_gpt56sol --resume
```

如果只需要先完成 physics，而 biology 暂时保留在 22 个已接受公式，可在同一 run 上增加执行范围选项：

```bash
python -m srbench generate \
  --subjects biology physics --only-subjects physics \
  --target-per-subject 30 --batch-size 30 --n-subfields 7 \
  --steps 5 --max-steps 15 \
  --max-lineage-attempts 4 --max-rounds 10 \
  --n-total 5000 --seed 20260917 \
  --provider openai --model gpt-5.6-sol \
  --executor local --workers 2 --job-timeout 2700 \
  --on-request-error defer --max-consecutive-request-errors 3 \
  --run-name bio_phys_30_gpt56sol --resume
```

此模式只调度 physics；`run.json` 会继续标为 `incomplete`，直到 biology 和 physics 都达到目标数量。

确认无持续限流后，可将 `--workers 5` 改为 `10` 或 `30`。仅需本地并行时改为 `--executor local`，无需安装 Daytona。**同一输出目录只允许一个调度器**；如果旧命令仍在运行，先在旧终端停止它，再运行新命令。已经完成的最终候选、场景和初始方程会复用；未完成的候选从最近保存的代数继续，保留已选机制和 ontology。

并行实现的边界与恢复行为：

- 当前并行的是初始方程之后的完整谱系；场景和初始方程生成仍由原阶段执行，两个领域仍依次处理。已有 30 个 E0 时直接进入谱系并行。
- 一个主进程拥有去重表、编号和结果索引。worker 只写自己的目录，编号按结果收集顺序分配。种子由领域、轮次和候选位置确定，与并发数、sandbox ID、完成顺序无关。
- 只为尚缺的公式数量启动任务；拒绝或重复后继续补位，不提前超额生成。候选数值失败记为 `skipped`，直接处理下一个基础 scenario；暂时性模型服务错误或单题总超时默认记为 `deferred`，保留检查点并调度下一题。连续 3 题暂时失败则停止派发，收回在跑任务后报错。认证失败和未分类的程序错误仍停止派发。
- 模型、种子和科学预算写在 `batch_config.json`，必须与原实验一致；并发数、执行位置、超时和 snapshot 写在 `execution.json`，允许续跑时调整。
- 本地与云端共用同一 API 服务额度。sandbox 不会加速单次模型响应；加速来自独立谱系重叠运行，实际受请求/令牌限额、重试和最慢任务影响。
- 云端接收代码、当前 E0 和所选模型服务的环境变量；续跑时还上传这一题最新的检查点，不上传 `.env` 或整批 outputs。云端返回的结果路径会转换成本地路径，后续包装与画图命令相同。
- Daytona 完成或正常失败后先下载谱系、数据和诊断记录，再删除 sandbox。日志仍在 `evolve_###.log`，sandbox ID 与清理状态在旁边的 `evolve_###.daytona.*.json`。
- 下载失败时保留并尝试停止 sandbox，供人工恢复；默认停止 24 小时后自动删除。此时先按记录中的 sandbox ID 取回输出，避免直接续跑而重复模型费用。意外断线没有实现远程任务自动重连；本地主调度进程需要持续运行。
- `--job-timeout 14400` 是每条谱系默认 4 小时的执行上限，包含远端准备时间。可调整；超时会保留已写出的诊断记录。
- 每个 sandbox 首次安装包及所需依赖会产生准备开销；可用 `--daytona-snapshot <名称>` 复用已安装科学依赖的 Python snapshot。选用相同 snapshot 有利于固定数值环境。

先查看命令与预算，不调用模型、不创建输出：

```bash
python -m srbench generate --run-name bio_phys_30_gpt56sol \
  --provider openai --model gpt-5.6-sol --seed 20260917 --dry-run
```

对整批公式包装题目：

```bash
python -m srbench package \
  --run bio_phys_30_gpt56sol \
  --n-total 5000 --test-points 500 --seed 20260917
```

对比模型提交的 `law.py` 与真实公式：

```bash
python -m srbench plot \
  --package outputs/bio_phys_30_gpt56sol/02_packaged/biology_001 \
  --law /path/to/model/law.py
```

`plot` 默认比较训练、测试两部分，分开报告指标；加 `--partition test` 可只比较测试集。ground truth 已包含在题包里，无需再提供第二个答案文件。

## 一眼看懂文件位置

```text
llm-srbench-v7/
├── README.md
├── pyproject.toml
├── src/srbench/
│   ├── cli.py                       # generate / package / plot
│   ├── generation/                  # 场景、演化、DataSpec、数值数据
│   │   └── response_diagnostics.py  # 机制覆盖与父模型吸收性报告
│   ├── packaging/                   # 划分、参考解、Harbor 模板
│   ├── plotting/                    # law.py 与真实公式的对比
│   ├── common/                      # 输入契约、指标、逐点运行器
│   └── resources/{taxonomy,seeds}/
├── skills/srbench-harbor-pack/       # 出题包装 skill
├── examples/
│   ├── static_1d/                   # 一维弹簧响应
│   ├── static_multivariate/         # 三维种群增长响应
│   └── ode_system/                  # 种群与资源的双状态系统
├── tests/
└── outputs/
```

每个正式生成批次的产物：

```text
outputs/<run>/
├── run.json
├── 01_generated/
│   ├── index.jsonl
│   └── biology_001/
│       ├── equation.json
│       ├── spec.json
│       ├── data.csv
│       └── lineage.jsonl
├── 02_packaged/<task_id>/
│   ├── manifest.json
│   ├── ground_truth.json
│   ├── split_manifest.json
│   └── task/
│       ├── instruction.md
│       ├── task.toml
│       ├── environment/{Dockerfile,train_data.csv}
│       ├── tests/                    # 测试数据、评分器与逐点运行器
│       └── solution/{solve.sh,reference_law.py,explain.md}
├── 03_plots/solution_YYYYMMDD/          # 仅观察真值
├── 03_plots/LLM_vs_truth_YYYYMMDD/      # 模型与真值对比
│   ├── comparison.png
│   ├── comparison.pdf
│   ├── predictions.csv
│   └── metrics.json
└── _checkpoints/                     # 场景、失败记录、内部中间结果与续跑信息
```

包装后的所有产物路径都是相对路径，`ground_truth.json` 保存完整 spec；搬移题包或删除原来的生成中间文件后仍可绘图。

## v7 的生成思路

```text
学科与场景 → 基线方程 gen0
  → 观察当前方程遗漏的过程或不再成立的假设
  → mechanism plan：机制、operation、freedom_change
  → 按原权重选择兼容的 ontology embedding pattern
  → 实现子方程，记录新自由度、退化关系与原假设
  → 从第 5 代检查 novelty，最多到第 15 代
  → DataGenSpec → 5,000 点 → 原有可观测性检查 → 收集候选
```

`taxonomy` 提供领域背景和机制建议；`operation` 表示新增过程还是修改已有假设；`ontology` 指导机制如何嵌入方程，例如相加、系数依赖、乘性调制、状态耦合。v7 保留原有 ontology 及权重，没有添加细碎的领域机制白名单。

两种 operation 都可以按科学需要释放自由度：

| freedom_change | 含义 | 例子 |
|---|---|---|
| `none` | 保持现有自由度 | 弹簧回复力从线性改为饱和响应 |
| `add_input` | 新增观测条件 | 原方程加入温度 T，固定刚度 k 仍保留 |
| `add_state` | 新增动态状态及其演化方程 | 种群模型加入会被消耗的资源 R |
| `parameter_to_input` | 原来的固定参数本身成为输入 | 弹簧刚度 k 从固定值变为逐实验观测的 k |
| `parameter_to_state` | 原来的固定参数本身成为状态 | 固定增长率 r 改为有自身响应时间的 r(t) |

因此，“新增 T，使 k 受 T 调制”和“将 k 本身变为输入”是不同的自由度变化。新状态必须有 RHS、初值，并实际影响原系统；不强求双向反馈。

新生成的场景不再默认写入 `fixed_univariate`，也不预先抽取 `dimension_track`。旧记录中显式声明的维度限制仍可读取。每步最多释放一个自由度，默认静态输入最多 4 个、ODE 状态最多 4 个，可用 `--max-static-input-dim`、`--max-ode-state-dim` 调整演化上限。

没有新增科学机制 validator、强制升维配额或按 R² 筛难题的门槛。保留已有的角色一致性、闭合系统、范围、novelty 和 ODE 终段变化检查。**高维比例和难题率需要真实批量生成、指定模型求解后统计，不能由权重直接推算。**

ODE 的“状态维数”和回归输入数分开记录。例如 `(t,N,R) → dN_dt` 是两个状态、三个回归输入；它只评估指定 RHS 的恢复，不自动评估整套 ODE 的恢复。

## 采样和评分

- 一维：在归一化采样坐标上，左侧 90% 训练、右侧 10% 测试；log 变量先取 log10。边界属于训练集。
- 多维静态：令 `c = 1 - 0.1**(1/d)`，所有归一化坐标均大于 c 的右上角作为隐藏区，体积恰为 10%；其余区域训练。用 scrambled Sobol 尽量均匀覆盖。
- ODE：按时间留出末段，两份数据都从原来的起始时刻和初值连续积分，不在测试边界重置初值，也不独立随机采样状态。

多维没有天然的整体“从小到大”。这里明确采用联合右上角定义；单个变量的训练、测试范围可以重叠，考察的是未见过的联合区域。默认总计 5,000 点，即 4,500 / 500；改变点数不会自动改变空间的 90% / 10% 定义。

包装阶段从原 spec 重新生成划分后的数据，不声称将候选 `data.csv` 原样拆开。单题也可通过 `--train-csv`、`--test-csv` 同时传入已有数据，此时保留原划分并记录为 `provided`。

参考解 `reference_law.py` 就是真实公式的可执行版本。训练和隐藏测试均使用无噪声的精确输入—输出 pair，包装逐点核对标签与数学真值。旧 spec 的非零 `noise` 设置会被忽略，旧 CSV 的 `_noisy` 列不会作为标签；显式提供的 CSV 标签不符合公式时会报错。参考解对实际训练集和隐藏测试集的 R² 应约为 1。

DataSpec 只提供 `analyze_expression`、`check_substitution`、`emit_data_gen_spec` 三个工具；已取消 `excitation_check`、`auto_balance` 和 `--k-sigma`。数值数据筛选沿用 ODE 末段趋稳规则：最后 20% 目标范围占全程范围的比例、末两个 20% 窗口的中位数差占全程范围的比例，两项都小于 0.02 时直接淘汰该候选。该判定不触发信噪比调参；静态 Sobol 点没有时间顺序，不使用末段趋稳判定。

评分器与绘图共用单行运行器：`law([row])` 每次在新 fork 中调用，消除跨行可变状态。模型输出 NaN、无穷或执行失败时记录失败，不丢弃失败行后重新评分。指标包含未经截断的 R²、RMSE、MAE、目标方差、NMSE、NMAE；沿用现有评分器对近零方差的判定。

一维画真实曲线与残差；多维画 parity 与残差散点；ODE 沿实际轨迹画导数对比。本地执行是进程隔离，不是安全沙盒；需要沙盒时使用 Harbor 的容器或 Daytona 环境。

## 续跑、去重和 Daytona

生成中断后，使用相同命令加 `--resume`；科学配置需要一致，`--workers`、`--executor`、`--daytona-snapshot`、`--job-timeout`、`--on-request-error` 和 `--max-consecutive-request-errors` 可以调整。`--only-subjects physics` 只恢复指定学科，属于执行范围，不改变 `batch_config.json` 中的完整实验学科集合。重复公式和正常科学拒绝会用新候选补足。默认有限轮次预算，达不到 30 个会报不足，不会悄悄当作成功。

遇到长时间接口超时后，可用以下配置恢复原来的生物、物理各 30 题实验。先加载 `.env`，再覆盖旧的重试配置：

```bash
set -a
source .env
set +a
export SRBENCH_OPENAI_READ_TIMEOUT=300
export SRBENCH_OPENAI_MAX_RETRIES=1

python -m srbench generate \
  --subjects biology physics \
  --target-per-subject 30 --batch-size 30 --n-subfields 7 \
  --steps 5 --max-steps 15 \
  --max-lineage-attempts 4 --max-rounds 10 \
  --n-total 5000 --seed 20260917 \
  --provider openai --model gpt-5.6-sol \
  --executor local --workers 2 --job-timeout 2700 \
  --on-request-error defer --max-consecutive-request-errors 3 \
  --run-name bio_phys_30_gpt56sol --resume
```

这会最多并行 2 条谱系，每题本次执行上限 45 分钟。一次模型调用在持续无响应时通常约 10 分钟内耗尽两次 HTTP 尝试；暂时失败后转入后续题目，原题在下次 `--resume` 时仍可续跑。`--on-request-error stop` 可改为首个暂时错误即停。连续失败计数按任务收集顺序计算，成功、重复、正常科学拒绝或数值失败跳过都会清零；达到阈值后仍收回在跑任务。若其他候选已填满目标数，暂缓的题目可留在检查点中，不自动记为科学拒绝。网络策略只影响运行与恢复，不改变 novelty、数值筛选或演化预算。

数值生成出现 NaN/无穷值、点数不足、算术溢出，或求解器明确报告积分/求根失败时，记录为 `candidate_error`；调度器将整个 scenario 标为 `skipped`，直接启动下一个基础 scenario，不在同一 E0 上继续尝试剩余谱系。失败公式、DataSpec、已写出的数据和日志均保留，失败项不计入每领域 30 个合格公式，后续候选继续补足。续跑会跳过这类场景，也能识别旧版本记录的 `candidate data has wrong row count or nonfinite values`。数值失败不会裁剪输出、删除坏点或修改公式；未知程序错误及认证错误仍停止，网络错误仍按 `--on-request-error` 处理。

演化记录在 `_checkpoints/<subject>/round_*/evolved/job_*/candidate_*/lineage_attempt_*/`：

- `lineage.jsonl`：每通过一代立即保存；后续失败仍保留前面的方程。
- `progress.json`、`gen_*_selection.json`：当前阶段、已完成代数，各代机制方案、抽取的 ontology 和选择后的随机状态。
- `model_calls/gen_*_plan.jsonl`、`model_calls/gen_*_equation.jsonl`：逐次记录提示词、模型原文、耗时和校验错误，包括失败重试。
- `failure.json`：失败原因及诊断文件位置；无效 CSV 还记录实际点数和非有限值行数。`accepted_lineage.jsonl` 只在整个候选通过后写出。场景是否跳过记录在学科目录下的 `attempts.jsonl`，状态为 `skipped`。

`--resume` 复用已完成的场景、初始方程和最终候选。未完成谱系读取 `lineage.jsonl`：例如已完成第 6 代、已选好第 7 代机制时，直接继续第 7 代公式调用。若公式已保存但 novelty 中断，先补该代 novelty；成功的 DataSpec 保存在 `planned_spec.json`，后续数值生成中断时可复用。已经科学拒绝的尝试不会重跑。新检查点恢复随机状态，旧检查点根据已有选择记录重放随机抽样；模型响应本身不保证确定性。尚未收到的模型响应及旧版本未保存的记录无法恢复。

`expression` 和 ODE 的 `rhs` 必须是数值表达式。`Eq/Ne/Lt/Le/Gt/Ge/And/Or/Not` 可用于 `Piecewise` 的分支条件；整个 `Eq(输出, RHS)` 不是数值 RHS。`before_fragment` 和 `after_fragment` 必须分别复制自父、子表达式，可直接复制完整表达式；不接受仅在代数上等价但原文不匹配的片段。

包装可加 `--resume`，只复用配置和文件哈希均一致的题包。已有不同题包不会被覆盖。

批量包装还会建立 `02_packaged/harbor_dataset/`，其中的相对软链接指向各题的 `task/`，使 Harbor 可以发现整批题目。每题在 `task.toml` 中有独立名称，避免都叫 `task`。

种子按学科、轮次、任务和尝试分配，生物与物理的种子空间互不重叠。去重键保留符号角色与整个 ODE，忽略空格、冗余括号、系数取值和初值；它不是完整的代数等价判定。远程模型采样不保证确定性，因此相同种子也不保证两次得到相同公式。

Daytona 可以通过 `srbench generate --executor daytona` 承载公式演化，也可以通过 Harbor 承载解题 agent；这是两个独立入口。它不决定公式随机数。把已包装好的 `task/` 送入不同沙盒，会得到相同的题目数据。公式生成和去重由一个调度器维护，不能仅依靠“环境不同”保证多样性。

在已配置好的 Harbor 环境中，可这样运行单题 oracle 验证：

```bash
harbor run --path outputs/demo/02_packaged/static_1d/task \
  --agent oracle --env daytona
```

此命令可能创建付费云资源；此次代码验证没有执行它。

整批 oracle 验证时，将 `--path` 改为 `outputs/bio_phys_30_gpt56sol/02_packaged/harbor_dataset`。

## 不调用模型的示例

每个 example 的 `spec.json` 是手写示例，`law.py` 是故意简化的答案，用来展示偏差，并非真实模型成绩。

```bash
python -m srbench package --spec examples/static_1d/spec.json \
  --output outputs/demo/02_packaged/static_1d --seed 42 --resume
python -m srbench plot --package outputs/demo/02_packaged/static_1d \
  --law examples/static_1d/law.py
```

将 `static_1d` 换为 `static_multivariate` 或 `ode_system` 即可运行其他例子。要验证完美参考解，将 `--law` 指向对应题包的 `task/solution/reference_law.py`，并用 `--output` 指定另一个绘图目录。

运行离线测试：

```bash
python -m unittest discover -s tests -q
python -m compileall -q src
```

测试覆盖两种 operation 的自由度变化、参数角色提升、生成调度与去重、静态/ODE 的 5,000 点数值验证、8 维 Sobol 划分、参考解正确性、旧噪声设置的无噪声兼容、独立评分器、题包搬移与绘图失败处理。Provider 测试还覆盖 OpenAI 地址规范化、密钥隔离、模型与 token 参数传递、DataSpec 工具结果回传、六个生成入口及 OpenRouter 兼容性。离线测试不代表完成真实模型的批量生成或难度测评。

包装 skill 位于 [skills/srbench-harbor-pack/SKILL.md](skills/srbench-harbor-pack/SKILL.md)，可在对话中使用 `$srbench-harbor-pack`。安装时可以将该目录软链接到 `~/.codex/skills/srbench-harbor-pack`，使 skill 的源文件继续由 v7 维护。


### 有效演化与谱系记录（2026-09-21）

生成规划和子方程提示要求说明父模型的响应关系、子模型改变的关系、
以及父模型重新拟合参数能否吸收这种变化。辅助状态轨迹变复杂不自动
意味着被评分的目标映射变复杂。新增 ODE 状态应说明初值是否会关闭
新增机制；已有初值合同仍保持不变。

DataSpec 接收所有已完成代的机制合同及范围建议，在现有 rationale 和
sanity_expectations 中说明采样条件与机制的联系，以及弱效应、失活或
被后续代替代的机制。这里只记录模型的科学预期，不是实测机制可见性
或难度证明，不增加 LLM 调用、拒绝门槛或每代 R² 测试。

每个 checkpoint 的 lineage_attempt_* 保留 gen0 到最新完成代的
lineage.jsonl、逐代 selection、model_calls、progress，以及采样阶段的
mechanism_observation_history.json、planned_spec.json 和诊断。恢复时旧
failure.json 会带时间戳保存。中断在某次模型返回前时，只有阶段/已完成
记录，不会伪造未返回的模型输出。

发布到 01_generated/<id> 时，除 lineage.jsonl 外，新增 lineage_archive/
独立副本，包含该候选运行的各次尝试、调用记录与采样记录；档案清单
为 archive_manifest.json。失败且未发布的候选保留在 _checkpoints。
旧题目不会自动补回已经丢失的历史。ontology 继续采用原有兼容过滤和
加权抽样；中间代拟合对照仍属于离线实验，不在生成阶段自动执行。

生成主流程现已完全停止调用 novelty 模型。`steps` 为实际演化代数；旧 `novelty-model` 参数仅兼容历史命令，输出 `NOT_EVALUATED` 不代表模型判断。


2026-09-21 提示进一步收紧：规划时优先排除参数合并、恒零/抵消项、
不可激活分支、全程不变的升维量、全域微弱修正和仅改变辅助轨迹的候选。
现有 rationale 必须给出具体区分条件（变化量、固定量、父子响应差异、
激活范围），observable_signature 和 DataSpec 继续承接该条件。
ODE 不得把未采样初值或未执行干预作为当前数据的辨识证据。找不到合理
区分时如实记录局限，不伪造效果；这些是提示要求，不是数值验证保证。
调用次数、schema、ontology 权重、生成代数及硬验收条件均不因本次修改增加。

### 机制驱动的响应关系演化（2026-09-24）

旧版的演化定义是：模型诊断一个机制缺口，选择 `add_term` 或
`change_assumption`，再用 ontology 指定机制进入方程的形式。虽然提示中要求
说明父子响应差异，但差异主要保存在自由文本里；`ontology` 的加权抽样也不看
父模型最容易采用的简化关系。DataSpec 只依据机制文字和范围建议选取实验范围，
没有独立的 train/hidden 机制覆盖报告。

新版定义为**机制驱动的响应关系演化**：

```text
诊断父模型 shortcut
→ 选择 add_term / change_assumption
→ 决定 freedom_change
→ 指定 response_change
→ 指定 diagnostic_groups 和 activation_condition
→ 选择与响应变化兼容的 ontology embedding
→ 生成子模型并记录 parent_reduction
→ 用确定性数据计算机制覆盖和父模型吸收性报告
```

`parent_shortcut` 描述父模型的可利用简化，例如
`single_gain`、`separable_product`、`latent_occupancy`、`single_phase`、
`fixed_environment` 和 `independent_branch`。`response_change` 描述真实的
输入到输出关系变化，而不是符号数量变化。当前允许的类型包括
`slope_change`、`curvature_change`、`interaction_emergence`、
`threshold_surface`、`branch_crossover`、`phase_shift`、`zero_shift`、
`ridge_rotation`、`weight_exchange` 和 `asymptotic_change`。

例如，受体模型的“占据后再聚簇”若被识别为可分离 shortcut，下一代应优先考虑
让占据量改变聚簇阈值，而不是简单增加一个很小的 basal 项。`diagnostic_groups`
记录如 `L/K_d`、`C_competitor/K_i`、`R_tot/K_cluster` 这样的诊断坐标；它们由
已声明输入、状态和固定参数计算，**不会成为新的输入列**。`activation_condition`
说明机制在哪个尺度被激活，`train_hidden_contrast` 说明训练区应先看到机制迹象、
隐藏联合区再继续推进它，`continuation_path` 说明怎样退化回父模型。

为了兼容旧谱系，上述字段在读取时是可选的；正式 `generate` 和 standalone
evolution 默认开启严格响应契约，新的模型计划必须填写这些字段，并校验其类型、
涉及的符号和与第一层计划的一致性。ontology 的原有跨学科菜单和
权重仍保留，但会根据 `response_change.type` 给兼容的表达方式加权，例如
`threshold_surface` 偏向 `state_coupling`、`saturating_or_thresholded` 和
`nested_nonlinearity`。这只是结构方向的偏置，不是硬性制造某种形状。

每个候选现在还会产生本地确定性报告：

- `coverage_report`：在训练和隐藏审计点上计算每个 diagnostic group，标记
  `inactive`、`visible` 或 `extended`；
- `target_variance`：报告两部分目标方差和范围，区分结构困难与近常数评分问题；
- `parent_absorption_report`：比较父方程固定参数误差，并在有可调父参数时做有限
  的本地最小二乘重拟合。报告阈值是解释性参考，不构成硬拒绝。

候选生成阶段使用较小的确定性审计设计，正式 Harbor packaging 会在官方的
4,500/500 划分上重新生成覆盖报告。报告不会增加模型调用，也不会按照报告自动
修改公式；它的作用是让“声明的机制是否真的在数据中出现”可检查。当前仍不把
`response_change` 或覆盖率作为硬验收门槛，避免把合理的单调交互、弱机制或稳定态
误判为失败。

### Packaging recovery (2026-09-22)

Regression metrics now assess target degeneracy relative to the target magnitude,
so converting energies between joules and electronvolts does not change R² or its
availability. Exactly constant targets remain undefined. Previously exported
packages retain their bundled metric implementation unless explicitly rebuilt.

Static specs may mark an input axis with `"type": "integer"`. The mixed Sobol
sampler uses uniform integer bins. Its hidden corner contains selected high
integer levels and a continuous corner adjusted to preserve a 10% holdout under
the product of counting measure and normalized continuous volume. Consult
`coordinate_boundaries` in the split manifest; a single shared normalized cutoff
no longer describes mixed integer tasks.

Polynomial implicit equilibria can opt in with
`"implicit_branch": "global_minimum_polynomial_potential"` and integrator
`root_solve_implicit`. `rhs_for_integrator` must be the stationarity residual
`g(target, inputs) = 0`, not `target - g`. The evaluator enumerates real roots,
requires positive curvature, and selects the unique lowest integrated potential.
It rejects noncoercive potentials, ambiguous degenerate minima, and inaccurate
roots. The generated standalone reference carries the same implementation.
Other implicit equations remain unsupported by Harbor packaging.

The four repaired candidates in `bio_phys_30_gpt56sol_20260921` include explicit
repair metadata in their published specs. Original candidate files and the first
51 packages are preserved under `_repairs/20260922_012831/`; generation checkpoints
remain historical records. The restored dataset is `02_packaged/20260922/`, with
55 tasks and `repair_validation.json`. These are manual data/spec corrections,
not new evolution generations. The ODE windows are now 0–400 for biology_006 and
0–0.2 for biology_008; physical parameters and initial states are unchanged.
