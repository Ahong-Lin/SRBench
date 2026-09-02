# Core Taxonomy One-Shot Difficulty Experiment — 中止报告

**日期:** 2026-08-31
**Commit:** `7303216b2e320a4749a54fa134d02748ff2a61c8` (origin/main, "Stop core taxonomy batch on execution failures")
**入口:** `scripts/run_full_taxonomy_pipeline.py --mode difficulty_gate`
**结论:** 实验在当前 frozen taxonomy 下**无法产出任何题目**,已中止。两轮共 52 个 gen0,**0 accepted**,Harbor hidden-R² 评测**一次都未成功执行**。

---

## 1. 执行摘要

| | v1 | v2 |
|---|---|---|
| run-name | `core_taxonomy_v1_gate` | `core_taxonomy_v2_opus` |
| evolution 模型 | gpt-5.6-sol (openrouter 网关) | **claude-opus-4-8** |
| 处理的 gen0 | 18 | 34 |
| **accepted** | **0** | **0** |
| rejected | 18 | 34 |
| Harbor 成功评测 | 0 | 0 |
| solver 花费 | $0 | $0 |
| 运行时长 | 2h37m | 1h10m |

两个不同厂商、不同架构的模型,在**同一个子领域(`cell_biology_and_signaling`)上都是 0/10,且拒绝原因完全一致**。这排除了"模型能力不足"的解释。

**产物路径:**
- `outputs/Core_Taxonomy/core_taxonomy_v1_gate/{batch_config.json,batch_ledger.jsonl}`
- `outputs/Core_Taxonomy/core_taxonomy_v2_opus/{batch_config.json,batch_ledger.jsonl}`
- 逐题日志:`<batch>/logs/evolve/biology/<equation_id>.log`
- 审计:`<batch>/evolved/biology/<id>/final_*/lineage_attempts.jsonl`

dry-run 三项断言均通过:`total_scenarios: 360`、`max_lineage_attempts: 1`、`difficulty_policy: one_shot`。生成阶段本身健康——biology 70/70 scenario + 70/70 equation,0 失败,taxonomy SHA `e5e95c39…` 未被改动。

---

## 2. 核心阻塞:26 / 36 个在范围内的子领域 `evolution_profile` 为空

这是最重要的发现,且**与模型无关**。

`mechanism_ontology.py:137` 无条件校验:

```python
if contract["structural_role"] not in profile.get("allowed_structural_roles", []):
    raise ValueError(f"structural role '{contract['structural_role']}' is not allowed by profile")
```

当 `allowed_structural_roles` 为**空列表**时,任何提案都必然抛异常,没有"不约束"的退路。

值得注意的是**紧接下面的 mechanism 校验(141–147 行)全部有 `if mechanisms:` 保护**,空 profile 时会正确跳过;只有 role 这一条没有。这个不一致强烈提示空 profile 是未完成的数据,而非有意的设计。

审计结果(按 `first_n_in_listed_order` 取前 7 个子领域):

| 学科 | 有可用 profile | 空 profile | 注定失败的 scenario |
|---|---|---|---|
| biology | 5 / 7 | neuroscience, genetics | 20 |
| **chemistry** | **0 / 7** | 全部 7 个 | **70** |
| physics | 2 / 7 (classical_mechanics, nuclear) | 5 | 50 |
| **materials** | **0 / 7** | 全部 7 个 | **70** |
| economy | 2 / 7 (micro, macro) | 5 | 50 |
| AI | 1 / 1 ✅ (roles=7 mechs=4,全库最完整) | 0 | 0 |
| **合计** | **10 / 36** | **26 / 36** | **260 / 360** |

**360 题里有 260 题(72%)从原理上不可能被接受。chemistry 和 materials 两个学科整体归零。**

实测验证:`neuroscience_and_neural_dynamics`(空 profile)10/10 全拒,拒绝原因全为 mechanism/role 不在 profile。

---

## 3. 第二个阻塞:即使 profile 非空,白名单也过窄

上限 100 题,但那 100 题的实测通过率同样是 0。以 v2 (opus) 的 34 个 gen0 为例:

| 拒绝闸口 | 次数 |
|---|---|
| `domain mechanism id X is not in the subfield profile` | 20 |
| `structural role X is not allowed by profile` | 6 |
| `ODE symbols declared but unused by every state RHS` | 2 |
| `missing suggested range for new symbols` | 2 |
| `ODE time_symbol must have V role` | 1 |
| `ODE systems must contain 1-4 states` | 1 |
| `add_term must not add/remove V inputs` | 1 |
| `RuntimeError: solver command exited`(execution failure,见第 5 节) | 1 |
| **合计** | **34** |

即 34 个 gen0 中,**33 个死于结构/契约校验,1 个死于我方 solver 参数错误;没有一个是因为"题目太容易"或"科学质量不足"而被淘汰**。`easy_r2 = 0.9` 这个 difficulty gate 从未被触及。

**这不是"科学质量不达标",而是词表不匹配。**opus 在 34 个 gen0 中提出了 **63 个互不相同的 mechanism id**,全部被拒。典型案例:

| 模型提出 | 白名单实际允许 | 语义 |
|---|---|---|
| `product_inhibition` | `product_feedback` | 相同 |
| `enzyme_inactivation` / `enzyme_deactivation` | `enzyme_inhibition` | 相近 |
| `cooperative_binding` / `cooperativity` | (无) | 酶动力学标准机制 |
| `allosteric_modulation` | (无) | 酶动力学标准机制 |
| `competitive_inhibition` | `enzyme_inhibition` | 应属子类 |
| `arrhenius_kinetics` / `arrhenius_rate` | `temperature_rate_modulation` | 相同 |

`enzyme_kinetics_and_biochemistry` 只允许 4 个 mechanism id,而模型提出的是教科书级正确机制,只是命名不同。

`structural_role` 的情况类似但更微妙:被拒 20 次的是 **`response_law`**,而它是 `mechanism_ontology.py:163` 中 `fallback_contract()` 为 `change_assumption` 生成的默认 role。该 role **在 6 个子领域是合法的**(`enzyme_kinetics_and_biochemistry`、`physiology_and_homeostasis`、`classical_mechanics`、`nuclear_and_particle_physics`、`microeconomics`、`scaling_laws`),但在 `cell_biology_and_signaling`(被拒 14 次)和 `population_ecology`(被拒 6 次)的白名单里没有。也就是说 role 词表在各子领域间不一致,模型很难预判某个语义相同的改动在当前子领域该用哪个 role 名。

### 3.1 关键旁证:后置的科学闸门几乎从未被触及

统计 `lineage_attempts.jsonl` 的 audit status,可以看出流水线在哪一层终止:

| audit status | v1 (gpt-5.6-sol) | v2 (opus) |
|---|---|---|
| `pipeline_error`(结构/契约校验阶段即终止) | 17 | 34 |
| `reject_low_observable_variation`(ODE observable gate) | **1** | **0** |
| 走到 Harbor hidden-R² 评测 | 0 | 0 |

**52 个 gen0 中只有 1 个活到了 ODE observable gate,0 个活到 Harbor。**换言之,本实验设计中真正承担科学筛选职责的两道闸门——observable gate 和 `easy_r2=0.9` 的难度门——**基本没有机会发挥作用**,几乎全部 gen0 在更前面的词表/契约校验就被拦掉了。这也是"0 accepted"无法通过换模型解决的根本原因。

(那唯一 1 例 observable gate 拒绝是 v1 的 `m2_cell_biology_and_signaling_0_005`:它跑完 6 代 lineage、两次通过 novelty、生成了真实 train/test CSV,最终因目标 `dK_dt` 末段收敛到 0 被拒 —— `robust_range=0.0066` vs `range=0.479`,median `-2.5e-08`。这说明 observable gate 本身工作正常且有效。)


---

## 4. 建议(需仓库负责人决策)

按性价比排序:

1. **补齐 26 个空 `evolution_profile`**。这是解锁 72% 题量的唯一途径,无法绕过。
2. **给 role 校验加空 profile 保护**,与 141–147 行的 mechanism 校验保持一致:
   ```python
   roles = profile.get("allowed_structural_roles", [])
   if roles and contract["structural_role"] not in roles:
       raise ValueError(...)
   ```
   这样空 profile 表示"不约束"而非"全部拒绝"。
3. **统一各子领域的 `structural_role` 词表**。`response_law` 在 6 个子领域合法、在 `cell_biology_and_signaling` / `population_ecology` 不合法(共被拒 20 次),而它正是 `fallback_contract()` 对 `change_assumption` 的默认取值。建议要么补齐,要么让 fallback 按子领域取合法值。
4. **扩充 mechanism 白名单或引入别名/同义映射**。当前是精确字符串匹配;仅补上 `cooperative_binding`、`allosteric_modulation`、`competitive_inhibition`、`product_inhibition` 等常见同义词就能显著提高通过率。
5. **让 execution failure 无法被伪装成科学 rejection**(见第 5 节)。

---

## 5. 附:一个影响统计口径的健壮性问题

`scripts/run_full_taxonomy_pipeline.py:103` 的 `_evolution_status()` 只把 `"No acceptable final task after"` 识别为 rejection,其余非零退出视为 `execution_failure` 并停批。这个设计是对的。

但 `evolution_pipeline.py` 会**在内部捕获基础设施异常**,打印 `REJECT pipeline error: <Exception>`,随后仍以正常的 rejection 文案退出。结果是 **API 错误、solver 崩溃被记为 `rejected`,batch 的安全停止机制看不见**。

本次实测到两例(均为我方配置问题,非仓库缺陷,但暴露了该机制):

- **v1,1 例 `ModelRequestError`** — gpt-5.6-sol 在 `effort=max` 下,reasoning token 与输出 token 共用预算;`equation_evolve.py:1106` 的 `max_tokens=4000` 被推理耗尽(`reasoning_tokens=4000`, `finish_reason=length`, `content=""`)。**该模型不适合走这个调用点**;换 opus 后此错误归零。
- **v2,1 例 `RuntimeError: solver command exited 1`** — 我误把 `--env` 当作环境变量注入(它实际是 harbor 的 environment *类型*,`harbor/__init__.py:146`),导致 `ValueError: Failed to import module 'ANTHROPIC_BASE_URL=http'`。**这一例说明确实有 gen0 走到了 Harbor 调用**,但因我的参数错误失败,并被错记为科学 rejection。

**建议:**在 `evolution_pipeline.py` 中区分"科学 gate 拒绝"与"基础设施异常",后者以独立退出码或独立日志标记透出,使批处理层能正确停批。否则 accept/reject 统计会被静默污染——这正是本次两个 batch 的 ledger 都不可直接用于统计的原因。

---

## 6. 未做的事

- 未修改任何源码、taxonomy、Harbor verifier、instruction、训练数据或 hidden 数据
- 未通过改题目/reference/CSV/verifier 来人为影响分数
- 未输出或保存任何 API key / token
- 未使用 `--continue-on-error`
- 实验产物仅写入 `outputs/`

**Verifier 隔离性已核验通过**(`Harbor_example/tests/test_outputs.py`):隐藏点随机顺序(`random.SystemRandom().shuffle`)、每次仅 `law([row])`(唯一调用点,第 59 行,且强制返回单条)、每行 `os.fork()` 独立子进程并降权至 `nobody`、评分期间 hidden CSV 被 `os.replace` 改名为 `secrets.token_hex(12)` 且 `0o600`、不存在整表批量传入 `law()` 的路径。这部分实现是可靠的。

---

## 7. 中断点(如需 resume)

**注意:两个 batch 的 ledger 均已被第 5 节所述问题污染(v1 混入 1 例 API 失败,v2 混入 1 例 solver 失败,均被记为 `rejected`),建议修复后使用新的 run-name 重跑,而非 `--resume`。**

| | v1 | v2 |
|---|---|---|
| 最后终态记录 | `m2_neuroscience_and_neural_dynamics_0_007` | `m2_population_ecology_0_003` |
| 中断时在跑 | `_0_008` | `m2_population_ecology_0_004` |
| ledger 行数 | 19 | 35 |
| 已处理子领域 | cell_biology 10/10, neuroscience 8/10 | cell_biology 10/10, neuroscience 10/10, enzyme_kinetics 10/10, population_ecology 4/10 |

两次停止均在 ledger 记录写入后进行,而 ledger 只在 solver 返回后才写,因此**没有中途砍掉正在计费的 Harbor 评测**。

**总花费:solver 侧 $0**(Harbor 从未成功完成评测)。生成侧 gpt-5.6-sol 无法定价(hyra `pricing.py` 将其列入 `_UNPRICED`,网关上报 $0);opus 侧仅消耗生成阶段 token,未产生 solver 费用。
