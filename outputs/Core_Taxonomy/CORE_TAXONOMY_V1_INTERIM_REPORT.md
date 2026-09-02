# core_taxonomy_v1 中期报告 — biology 学科(57/70)

**日期:** 2026-09-02/03
**Commit:** `2c641c0f53d074f2e84e0aed51d7c8c6c916458e` ("Add guided mechanism planning and random embedding patterns")
**入口:** `scripts/run_full_taxonomy_pipeline.py --mode difficulty_gate`
**状态:** 人工中止于 biology 学科第 57 条(共 70)。**0 accepted**,但流水线全程健康,**0 execution failure**。

---

## 1. 执行摘要

| 项目 | 数值 |
|---|---|
| 计划 gen0(全量) | 360 |
| 计划 gen0(biology) | 70 |
| 实际生成 gen0 | **70 / 70**(0 失败) |
| 实际处理 evolution | **57** |
| **accepted** | **0** |
| rejected | 57 |
| **execution_failure** | **0** |
| Harbor hidden-R² 评测 | **16 次** |
| 因 R² > 0.90 直接淘汰 | **16** |
| solver 总花费 | **$32.72**(中位 $2.23/题) |
| 运行时长 | 约 8 小时 |

**产物路径**
- `outputs/Core_Taxonomy/core_taxonomy_v1/batch_config.json`
- `outputs/Core_Taxonomy/core_taxonomy_v1/batch_ledger.jsonl`(58 行 = 1 generation + 57 evolution)
- `outputs/Core_Taxonomy/core_taxonomy_v1/logs/`(逐题 evolve 日志)
- `outputs/Core_Taxonomy/core_taxonomy_v1/gen0/`(Scenarios + Equations)
- `outputs/Core_Taxonomy/core_taxonomy_v1/evolved/`(lineage、DataSpec、5000 点 CSV、observable gate、Harbor task)

**参数合规性**(dry-run 与 batch_config.json 双重确认)

`total_scenarios=360`、`max_lineage_attempts=1`、`difficulty_policy=one_shot`、`operation_policy=guided`、`embedding_policy=random`、`n_total=5000`、`test_points=500`(即 4500 训练 / 500 hidden)、`easy_r2=0.90`。未使用 `--continue-on-error`。

**两处本地替换**(其余参数原样)
1. `--env daytona` → `docker`:本机无任何 Daytona 凭据(无 `DAYTONA_*`、无 `~/.daytona`),该云端沙箱会立即失败并按规则 12 停批。
2. `claude-opus-4-7` → `claude-opus-4-8`:本机代理上唯一可用的 opus 档位。

`--solver-command` 追加了 `--extra=--ae ...` 以向容器注入 `ANTHROPIC_BASE_URL`(容器需用网桥地址 `172.17.0.1`,loopback 不通)。注:`harbor run --env` 是 environment *类型*而非环境变量设置器(`harbor/__init__.py:146`)。

---

## 2. 本轮的关键进展:上一轮的死结已解开

上一份 `EXPERIMENT_HALT_REPORT.md` 报告了两个阻塞,本轮 commit `2c641c0` 已修复:

| 阻塞 | 上一轮(52 gen0) | 本轮(57 gen0) |
|---|---|---|
| `domain mechanism id 不在 profile` | **78 次** | **0** |
| `structural role 不被 profile 允许` | **27 次** | **0** |
| 走到 Harbor 评测 | **0** | **16** |

`mechanism_ontology.py` 现在对缺失 profile 回退到 `ontology["default_allowed_roles"]`(10 个 role)+ 学科级 `_SUBJECT_FALLBACKS`,并移除了 mechanism id 硬校验,注释写明"an absent or novel ID must not reject a scientifically coherent proposal"。

**效果显著:**上一轮 52 个 gen0 无一走到 Harbor;本轮 57 个中有 **16 个(28%)**跑通了 演化 → novelty → DataSpec → 数据生成 → observable gate → Harbor 全链路。

**遗留:**`_SUBJECT_FALLBACKS` 只覆盖 physics/biology/economy/ai。chemistry 与 materials 仍返回 `mechs=0`(共 140 题),因 mechanism 硬校验已移除,未必必挂,但风险高于其它学科 —— 本轮未跑到,无实测数据。

---

## 3. 终止闸口分布(57 条)

| 闸口 | 数量 | 占比 |
|---|---|---|
| `pipeline_error`(guided 契约校验) | **34** | 60% |
| **`harbor_r2 > 0.90`(直接淘汰)** | **16** | 28% |
| `reject_low_observable_variation`(ODE observable gate) | **7** | 12% |
| execution_failure | **0** | 0% |

按指令要求的口径归类:
- **因 observable gate / novelty / DataSpec / 数据生成失败被拒:41**(34 契约 + 7 observable)
- **因 R² > 0.90 被拒:16**
- **execution_failure:0**

`pipeline_error` 全部为 `EvolvedEquationValidationError`,主要是 `--operation-policy guided` 新增的两层计划一致性约束:
- `evolution_contract.scientific_mechanism must match the first-layer plan`
- `evolution_contract.before_fragment must occur in the parent expression`

这类校验检查的是**逻辑自洽**(两层计划是否一致、声明改动的片段是否真在表达式里),比上一轮的**命名匹配**合理得多,但对模型输出的格式精度要求很高。

---

## 4. 各子领域统计

| 子领域 | 处理 | accepted | 契约校验拒 | observable gate 拒 | R²>0.90 淘汰 |
|---|---|---|---|---|---|
| cell_biology_and_signaling | 10 | 0 | 7 | 1 | 2 |
| neuroscience_and_neural_dynamics | 10 | 0 | 8 | 0 | 2 |
| enzyme_kinetics_and_biochemistry | 10 | 0 | 5 | 1 | 4 |
| population_ecology | 10 | 0 | 6 | 1 | 3 |
| epidemiology_and_disease_dynamics | 10 | 0 | 5 | 2 | 3 |
| genetics_and_population_genetics | **7**(中止) | 0 | 3 | 2 | 2 |
| physiology_and_homeostasis | **0**(未开始) | — | — | — | — |
| **合计** | **57** | **0** | **34** | **7** | **16** |

`neuroscience` 与 `genetics` 原本 `evolution_profile` 为空,靠 `subject_fallback` 救回;两者都产出了走到 Harbor 的题目,说明 fallback 机制有效。

---

## 5. 核心发现:难度门 `easy_r2=0.90` 与题目分布严重不匹配

16 次 Harbor 评测的 hidden R²:

| 统计量 | 数值 |
|---|---|
| 中位数 | **0.999994** |
| 最小值 | **0.999876** |
| 最大值 | **1.000000** |
| ≤ 0.90(接受) | **0** |
| > 0.90(淘汰) | **16** |

**最小值都有 0.999876。**16 个样本没有一个接近 0.90,分布宽度只有 1.2e-4 —— 这不是"擦边淘汰",而是求解器在所有题目上都达到了数值饱和。阈值定在 0.90 还是 0.99,结果完全一样。

**求解成本在实质上升,却完全没有转化为难度。**中位 solver 花费随进度从 $0.67 → $0.96 → $1.25 → $1.47 → $1.85 → **$2.23**,涨了 3.3 倍。题目确实让求解器花了更多推理,但 16/16 无一例外被解出。

**一条求解器自述值得注意。**`population_ecology_0_008`(耗时 21 分钟)的 agent 在输出中主动说明:

> "the near-cancelling ±2.6 coefficients mean this is an accurate empirical decomposition rather than a guaranteed recovery of the exact generating expression"

即它承认拿到的是**高精度经验拟合**而非真正还原生成表达式,但 R² 仍达 0.99995。这揭示了机制:**求解器不需要找到真解,只要拟合足够好就能突破 0.90**。

---

## 6. 建议

1. **难度门形同虚设,需重新设计。**当前 hidden 集与训练集同分布且无噪声,R² 天然饱和。建议改为**外推留出**(如训练 t∈[0,8]、hidden t∈(8,10]),并在生成时校验 `var_hidden/var_train > 1e-2` 以免方差塌缩。
2. **补充"是否真正还原表达式"的判据。**R² 无法区分真解与高精度拟合。可考虑符号等价性检查,或对求解器提交的 `law.py` 做复杂度/可解释性约束。
3. **补齐 chemistry 与 materials 的 `_SUBJECT_FALLBACKS`。**这两个学科(140 题)目前 `mechs=0`,是全量跑之前应确认的风险点。
4. **`guided` 契约校验占了 60% 的拒绝。**约束本身合理,但可考虑放宽 `before_fragment` 的匹配方式(如允许规范化后比较),或增加 retry 预算。
5. **让 execution failure 无法伪装成科学 rejection。**`evolution_pipeline.py` 会内部捕获基础设施异常并打印 `REJECT pipeline error:` 后按正常 rejection 退出,使批处理层的安全停止看不见。本轮虽为 0,但上一轮曾因此漏判两例。

---

## 7. 附:haiku-4.5 演化批次(execution failure,已停)

同参数用 haiku 作**演化模型**的对照批次在生成阶段即失败:

```
auto_workflow.py:1248 generate_m2_for_subfield -> _json_from_response
json.decoder.JSONDecodeError: Unterminated string starting at: line 624 column 24
```

**根因(配置问题,非仓库缺陷):**`auto_workflow.py:1245` 请求 `max_tokens=12000`,而 haiku-4.5 的真实输出上限为 **8192**,代理按 `min(client, ceiling)` 封顶,10 个 scenario 的 JSON 被硬截断。重试 6 次均在同一位置失败,属确定性失败。

**结论:**haiku 不适合作生成/演化模型;但可作求解器(逐题调用,无长 JSON 需求)。

目录:`outputs/Core_Taxonomy/core_taxonomy_v1_haiku/`(ledger 仅 1 条 generation-error,无污染数据,保留作证据)。

**待办:**`outputs/Core_Taxonomy/probe_haiku_solver.py` 已就绪 —— 用 haiku 重跑 opus 已评测过的 16 道 Harbor task,以区分「题目太简单」与「opus 求解器太强」。该探针把任务复制到 scratch 目录后运行,不写回官方 ledger,不违反规则 2(每 gen0 至多一次 Harbor 评测)。本次中止前未执行。

---

## 8. 中断点(如需 `--resume`)

| 项目 | 值 |
|---|---|
| 最后终态记录 | `m2_genetics_and_population_genetics_0_006` |
| 中断时在跑 | `m2_genetics_and_population_genetics_0_007`(无终态,resume 会重试) |
| ledger 行数 | 58 |
| 未处理 | genetics 3 条 + physiology 10 条 + 其余 5 个学科 290 条 |

中止在 ledger 记录写入之后进行,而 ledger 仅在 solver 返回后才写,因此**未砍掉任何正在计费的 Harbor 评测**。

恢复命令(run-name / 模型 / 参数需完全一致,追加 `--resume`):

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8788"
export ANTHROPIC_API_KEY="<8788 代理 sentinel>"
python3 scripts/run_full_taxonomy_pipeline.py \
  --run-name core_taxonomy_v1 --mode difficulty_gate \
  --provider anthropic --model claude-opus-4-8 \
  --steps 5 --max-lineage-attempts 1 --n-total 5000 --test-points 500 \
  --easy-r2 0.90 --difficulty-policy one_shot \
  --operation-policy guided --embedding-policy random \
  --harbor-template Harbor_example \
  --solver-command "python3 -m harbor run --task {task} --model claude-opus-4-8 --agent claude-code --env docker --extra=--ae --extra=ANTHROPIC_BASE_URL=http://172.17.0.1:8788 --extra=--ae --extra=ANTHROPIC_API_KEY=<sentinel>" \
  --resume
```

---

## 9. 未做的事

- 未修改任何源码、taxonomy、Harbor verifier、instruction、训练数据或 hidden 数据
- 未通过改题目 / reference / CSV / verifier 影响分数
- 未输出或保存任何 API key / token
- 未使用 `--continue-on-error`
- 实验产物仅写入 `outputs/`

**Verifier 隔离性已核验**(`Harbor_example/tests/test_outputs.py`):隐藏点随机顺序(`random.SystemRandom().shuffle`)、每次仅 `law([row])`(唯一调用点第 59 行,强制返回单条)、每行 `os.fork()` 独立子进程并降权至 `nobody`、评分期间 hidden CSV 被 `os.replace` 改名为 `secrets.token_hex(12)` 且 `0o600`、不存在整表批量传入 `law()` 的路径。
