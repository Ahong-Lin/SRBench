# 用 Codex + gpt-5.6-sol 评测 Harbor 题目

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
