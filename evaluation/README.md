# 用 Codex + gpt-5.6-sol 评测 Harbor 题目

## 0917 / 0921 GPT-5.4 replay 迁移与重新评测

这两批已将数据和题包纳入 Git，服务器克隆后可直接使用，无需重新生成或包装。
GPT-5.4 是演化出题模型；下面两份配置沿用历史求解设置：
`gpt-5.6-sol`、Codex CLI `0.131.0`、high、每题 3 次、并发 2、Daytona。
需要换求解模型时修改配置中的 `agents`。

| 批次 | 原始场景来源 | 生成题 / 可评测题 | 配置 |
|---|---|---:|---|
| 0917 | `outputs/bio_phys_30_gpt56sol` | 60 / 59 | [0917 YAML](harbor_replay_0917_gpt54.yaml) |
| 0921 | `outputs/bio_phys_30_gpt56sol_20260921` | 60 / 59 | [0921 YAML](harbor_replay_0921_gpt54.yaml) |

上传内容包括两批 replay 的完整 `01_generated`（含谱系和生成调用归档）、
`02_packaged/20260930`、运行配置，以及实际复用的 gen0 方程和来源记录。
两个原始场景批次的 `round_001` 和 `round_002` 的 `gen0` 也一并保存，
共 145 条 scenario 和 140 条初始方程记录。原始场景由 GPT-5.6-sol 生成，
随后 GPT-5.4 复用初始方程进行演化。历史复用可能回退到上一轮，
应以 replay 内的 gen0 副本和 `generation_complete.json` 为准。
归档中的旧绝对路径仅作来源记录，评测入口使用相对路径。

没有纳入旧求解结果、绘图缓存或重复的演化工作目录。完整清单和 SHA256 见
`evaluation/replay_bundle_manifest.json`。服务器从仓库根目录验证：

```bash
python evaluation/verify_replay_bundle.py
```

两批合计 **118 个题包**，均保留原训练集、隐藏测试集、评分代码和参考解。
0917 的 `physics_014` 与 0921 的 `physics_019` 是尚未声明显式分支的隐式方程，
仅保留生成记录；原因见各批 `packaging_report.json`。

在已安装 Harbor 0.16.1、配置好下文 `.env.harbor` 的服务器上分别运行：

```bash
harbor run --config evaluation/harbor_replay_0917_gpt54.yaml \
  --env-file .env.harbor --job-name replay0917_rerun_01 --yes
harbor run --config evaluation/harbor_replay_0921_gpt54.yaml \
  --env-file .env.harbor --job-name replay0921_rerun_01 --yes
```

结果分别写入对应 replay 的 `04_evaluations`；重复实验请使用新的 job-name。
这些命令会调用模型并创建 Daytona 资源，本次迁移没有执行在线评测。
原 Dockerfile 的 Python 包版本未锁定；本次保留题包原样，文件校验一致不代表
未来安装的依赖版本必然一致。以下章节保留的是旧批次评测说明。

从 llm-srbench-v7 根目录执行。此机器已有 conda 环境 `harbor`，Harbor 版本为 0.16.1；生成程序使用的 `srbench-agent` 是另一个环境。

配置：[harbor_codex_gpt56sol_daytona.yaml](harbor_codex_gpt56sol_daytona.yaml)。模型固定为 `gpt-5.6-sol`，Codex CLI 固定为 `0.131.0`，reasoning effort 为 high，网页搜索关闭，默认两路并发、每题一次、每题 agent 最长 3600 秒。Daytona 承载解题沙盒，任务结束后删除沙盒，下载 law.py 和 explain.md。

## 环境变量

首次准备：

```bash
conda activate harbor
cp -n evaluation/harbor.env.example .env.harbor
```

填写 `.env.harbor`：

```dotenv
OPENAI_API_KEY=用于Codex且有gpt-5.6-sol权限的密钥
OPENAI_BASE_URL=https://api.openai.com/v1
DAYTONA_API_KEY=你的Daytona密钥
```

如果使用代理，把 OPENAI_BASE_URL 改为与密钥匹配、支持 Responses API 的地址，保留 `/v1` 基础路径；不要填 `/v1/chat/completions`。生成公式时使用的 Chat Completions 接口能调用成功，并不能确认 Codex 所需的 Responses API 也可用。不要将生成接口的不同服务密钥与此地址混用。

本次未请求模型，也未创建云端沙盒，因此尚未验证你所用服务对该模型的 Responses 接口权限。官方文档页面本次访问被拒绝；启动配置按本机 Harbor 0.16.1 的 Codex 实现核对，模型名按用户指定保留。

## 先评测历史 5 题

```bash
harbor run \
  --config evaluation/harbor_codex_gpt56sol_daytona.yaml \
  --env-file .env.harbor \
  --path outputs/bio_phys_30_gpt56sol/02_packaged/history_v7/harbor_dataset \
  --job-name gpt56sol_history_5 \
  --yes
```

这里使用独立的 5 题目录，避免依赖软链接目录的名称过滤。Harbor 0.16.1 在过滤 LocalTaskId 时使用解析后的目录名，这些目录名均为 `task`，因此不要用 `--include-task-name 'history_*'` 选择这些软链接题目。

## 评测全部 53 题

```bash
harbor run \
  --config evaluation/harbor_codex_gpt56sol_daytona.yaml \
  --env-file .env.harbor \
  --job-name gpt56sol_all_53 \
  --yes
```

这会重新评测全部 53 题，包含历史 5 题。若已评测历史题、只想跑本轮新增 48 题：

```bash
harbor run \
  --config evaluation/harbor_codex_gpt56sol_daytona.yaml \
  --env-file .env.harbor \
  --path outputs/bio_phys_30_gpt56sol/02_packaged/all_current_20260920/harbor_dataset \
  --job-name gpt56sol_current_48 \
  --yes
```

可加 `--n-concurrent 1` 改为单并发。重复做新实验时使用新的 job-name；两个任务并发表示两个题目各自运行一个 Codex agent，不改变题目数据。执行这些命令会实际调用模型并创建 Daytona 资源。

## 结果与验证

结果写到 `outputs/bio_phys_30_gpt56sol/04_evaluations/<job-name>/`。每个 trial 的 `verifier/metrics.json` 记录原始 R² 等指标，`verifier/reward.txt` 为 Harbor 奖励；law.py、explain.md 通过配置中的 artifacts 下载。异常任务需要结合 trial 的 result.json 和 verifier 日志判断，不能把运行错误等同于难题。

当前已离线验证：53 个题目可被 Harbor 发现和读取，历史 5 题的原始干净标签与找回的公式逐点相符；新题包均为 4500 个训练点和 500 个隐藏测试点，参考解自检 R²=1。尚无本轮 Codex 模型解题成绩。

历史题对应关系：

| 新题号 | 原任务 | 目标 |
|---|---|---|
| history_001 | enzyme_kinetics_and_biochemistry_0_006 | A |
| history_002 | epidemiology_and_disease_dynamics_0_002 | R0 |
| history_003 | genetics_and_population_genetics_0_001 | dH_dt |
| history_004 | population_ecology_0_006 | N_eq |
| history_005 | population_ecology_0_008 | g |

历史数据来源及公式来源保存在 `02_packaged/history_v7/_sources/`；独立题包自带 ground_truth 和 reference solution，后续运行不依赖原来的 History_Hyra 目录。
