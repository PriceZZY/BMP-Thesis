# 复现路径实测状态（2026-08-30）

> 本文件记录一次**真实执行**的复现尝试：装依赖、跑脚本、逐字段核对结果文件。
> 所有结论都来自实跑输出，不是静态阅读推断。

## 一、审稿人「15 分钟路径」原本是坏的 —— 两个互相独立的失败点

| 层 | 现象 | 位置 |
|---|---|---|
| **环境层** | 不按 `requirements.txt` 装（拿最新 matplotlib）→ `TypeError: Axes.boxplot() got an unexpected keyword argument 'labels'`。matplotlib 3.11 移除了 `labels=` | `generate_figures.py:53`（另 68、84 同病） |
| **数据层** | 按钉的 `matplotlib==3.10.8` 装 → Fig 3、Fig 4 正常出图，然后 `KeyError: 'y1_p'` | `generate_figures.py:149` |

两个坑是**串联**的：环境层那个先发作，所以只有按 requirements 装的人才会看到数据层那个。
审稿人不按 requirements 装是常态 —— 这意味着大多数人连第二个坑都走不到。

## 二、逐字段核对：缺的只有一个键，而且它在一句死代码上

`results/monte_carlo_results.json` 的 `raw.<策略>[]` 每条记录，实际的键是：

```
seed · strategy · p_reduction_t · total_cost · adoption_rate · cost_per_kg
```

`generate_figures.py` 读三个 raw 字段：

| 字段 | 结果文件里 | 说明 |
|---|---|---|
| `p_reduction_t` | ✅ 有 | 14 处引用 |
| `cost_per_kg` | ✅ 有 | 第 64–66 行，Fig 3 成本面板 |
| `y1_p` | ⛔ **没有** | 只在第 149 行出现一次 |

**第 149 行是一句死代码。** 原文：

```python
fcfs_y1_p = [r['y1_p'] for r in fcfs]
# Approximate base load from total reduction / fraction
# Instead, show the distribution width          ← 作者自己写的：改用了别的做法
p_reductions = [r['p_reduction_t'] for r in fcfs]
```

`fcfs_y1_p` 定义之后**再没有被读过**，Fig 5 后续全部改用 `p_reduction_t`。
作者换了做法，把旧的那行留在了那里。

> ⚠️ **本文件 08-30 上午的第一版有一处错**：当时写「代码要 `y1_p` 和 `cost_pe_kg`，两个都不存在」。
> `cost_pe_kg` 是 `cost_per_kg` 的笔误，该字段**存在**。缺的只有 `y1_p` 一个。
> 这个错本来当场可测 —— Fig 3 的成本面板就读 `cost_per_kg`，而实跑里 Fig 3 是正常出图的，
> 「字段缺失」和「图能画出来」直接矛盾。是我没把已有的观测拿来自查。

## 三、已修（三处纯管道改动，不涉及任何论文数字）

1. **删掉 `generate_figures.py:149` 的死代码**（改为注释说明）。
2. **三处 `labels=` → `tick_labels=`**（53、68、84 行）。`tick_labels` 自 matplotlib 3.9 起可用，
   钉的 3.10.8 和最新的 3.11 都支持 ⇒ **修法与版本无关**，不需要读者严格按 requirements 装。
   （`fix_figures.py` 本来就用的 `tick_labels=`，无需改动。）
3. **`fig2_prisk_map.py`：`_REPO` 的定义从第 22 行提到第 10 行** —— 原本第 10–12 行在定义之前就用它，必然 `NameError`。

### 验证方式
在 `/tmp` 的克隆里跑（不在主仓，避免覆盖仓内已有的图），`results/` 与 `data/` 用**拷贝**不用软链，
确保写入不外溢：

| 环境 | 结果 |
|---|---|
| `matplotlib==3.10.8`（requirements 钉的） | ✅ `All figures generated!` |
| `matplotlib 3.11.1`（最新） | ✅ `All figures generated!` |

Fig 2 与 Fig 6 仍然是脚本自己声明的 `deferred`（需要 GIS 图层），不属本次修复范围。

## 四、**没有做**的事，以及为什么

- **没有补造 `y1_p` 字段。** 补一个字段进去，就把「无法复现」变成了「看起来能复现」——
  那在学术上比现状更严重。这一行是死代码，删掉才是它本来的样子。
- **没有重跑 Monte Carlo。** 重跑会换掉论文的证据基础。这是作者的决定，不是执行者的。
- **没有改任何一个论文里报告的数字。** 上面三处改动全部是管道层，图的内容与数据完全不变。

## 五、仍然未解、且只有作者能决定的两条

这两条**不是**上面那种删一行就好的问题，它们是「结果文件与生成它的代码不同源」：

1. **`monte_carlo_results.json` 与 HEAD 代码不同源。**
   `_draw_run_params`（`environment.py:112-134`）现在每个 run 抽一次参数；而存档结果里
   seed-1000 的 `51.25869938923559` 只能由「参数钉死在均值」的旧代码产生。
   README:69 / RUN_GUIDE:95 / 手稿 §4.5、§8 四处都承诺了逐位复现。
   ⇒ 要么重跑并重报全部区间，要么在文档里显式声明结果对应的是哪个提交。

2. **`sensitivity_oat_results.json` 不由仓内任何版本的代码产生。**
   OAT 调 `run_single_simulation`，该函数**无条件**施加参与过滤；但存档结果的 FCFS 是 92.07 t，
   同参数、过滤开启的主 MC 是 42.79 t。Fig 8 的图注却写着 "participation filter OFF"。
   ⇒ 图上的情景标签与生成它的代码直接矛盾。

这两条的共同点：**修不修、怎么修，取决于要不要动已投稿的数字**，超出执行范围。
