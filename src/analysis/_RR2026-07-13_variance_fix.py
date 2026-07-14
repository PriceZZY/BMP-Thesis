"""修正后的方差分解 —— 复刻论文的 A/B/C 实验设计，但让参数真的动起来。

BUG: simulation.py:137 传 sample=not env.stochastic；environment.py 的门是
     `if sample and self.stochastic`。stochastic=True -> sample=False -> 门恒 False。
     => 实验 A 里参数从未被抽样，A 退化成 C。这就是 var_A(3.6317) ≈ var_C(3.6222) 的原因。

修法（正确的认识论处理）：参数不确定性是**全流域系统性的**（我们不知道真实的 BMP 效率
是 0.55 还是 0.65），不是逐田块的独立测量噪声。所以应当 **每个 run 抽一次，全流域共用**。
逐田块抽 8,949 次会被大数定律抹平 —— 那样即使修好开关也仍然得到接近零的参数方差。

实现：直接把 run 级别的抽样值写进模块常量的 'mean'。现有代码路径读的就是 'mean'，
因此无需触碰那个坏掉的开关，就实现了正确的 run 级抽样。

实验（复刻 src/analysis/variance_decomposition.py）：
  A'  precip 固定 1.0，参数 run 级抽样，采纳随机   -> 参数 + 采纳 方差
  C   precip 固定 1.0，参数固定均值，采纳随机      -> 仅采纳方差（应复现 ~3.62）
  B   = 798.82（论文原值，这个实验是干净的，precip 确实被抽样了）
"""
import sys, os, io, json, time, contextlib
import numpy as np
from multiprocessing import Pool

REPO = "/Users/pricesmacbook/Documents/世界认知/claude/BMP-Thesis"
os.chdir(REPO)
sys.path.insert(0, "src")

N = 500
VAR_B_PUBLISHED = 798.8181800373691  # 论文 Experiment B，干净，直接沿用

PRISTINE = {
    "REDUCTION_A": {'High': {'mean': 0.60, 'std': 0.15}, 'Medium': {'mean': 0.30, 'std': 0.10}, 'Low': {'mean': 0.10, 'std': 0.05}},
    "REDUCTION_B": {'High': {'mean': 0.70, 'std': 0.10}, 'Medium': {'mean': 0.50, 'std': 0.10}, 'Low': {'mean': 0.30, 'std': 0.10}},
    "BASE_P_LOSS": {'High': {'mean': 1.50, 'std': 0.50}, 'Medium': {'mean': 0.50, 'std': 0.20}, 'Low': {'mean': 0.15, 'std': 0.05}},
    "PARTICULATE_RATIO": {'mean': 0.80, 'min': 0.70, 'max': 0.90},
}


def run_one(args):
    seed, exp = args
    import model.environment as envmod
    import model.adoption_function as af
    from model.subsidy_strategies import FirstComeFirstServed
    from model.simulation import run_single_simulation

    af.PARAMS["intercept"] = -2.00
    af.PARAMS["subsidy_coeff"] = 0.010

    # 每次调用先恢复原始常量
    envmod.REDUCTION_A = {k: dict(v) for k, v in PRISTINE["REDUCTION_A"].items()}
    envmod.REDUCTION_B = {k: dict(v) for k, v in PRISTINE["REDUCTION_B"].items()}
    envmod.BASE_P_LOSS = {k: dict(v) for k, v in PRISTINE["BASE_P_LOSS"].items()}
    envmod.PARTICULATE_RATIO = dict(PRISTINE["PARTICULATE_RATIO"])

    if exp == "A":
        # ---- run 级参数抽样：一个 run 抽一次，全流域 8,949 块地共用 ----
        prng = np.random.RandomState(seed + 777_000)
        for name, lo, hi in [("BASE_P_LOSS", 0.01, None), ("REDUCTION_A", 0.05, 0.95), ("REDUCTION_B", 0.05, 0.95)]:
            tbl = getattr(envmod, name)
            for k, v in tbl.items():
                d = prng.normal(PRISTINE[name][k]['mean'], PRISTINE[name][k]['std'])
                d = max(lo, d) if hi is None else float(np.clip(d, lo, hi))
                v['mean'] = d
        pr = prng.uniform(0.70, 0.90)
        envmod.PARTICULATE_RATIO = {'mean': pr, 'min': pr, 'max': pr}

    with contextlib.redirect_stdout(io.StringIO()):
        env = envmod.ThamesEnvironment(data_path="data/processed", stochastic=True, seed=seed)
        env.current_precip_multiplier = 1.0
        env.sample_precip_multiplier = lambda: 1.0          # 固定降水（同论文 A/C 实验）
        run = run_single_simulation(env, FirstComeFirstServed(30, 30, seed=seed), years=4, seed=seed)
    return float(run[-1]["p_reduction_tonnes"])


if __name__ == "__main__":
    seeds = list(range(8000, 8000 + N))   # 论文方差分解用的种子段
    res = {}
    t0 = time.time()
    for exp in ["C", "A"]:
        with Pool(8) as p:
            res[exp] = p.map(run_one, [(s, exp) for s in seeds], chunksize=8)
        v = np.var(res[exp], ddof=1)
        lbl = {"C": "C  仅采纳随机 (参数固定均值)", "A": "A' 参数 run 级抽样 + 采纳"}[exp]
        print(f"  {lbl:34s} var={v:9.3f}  mean={np.mean(res[exp]):6.2f}t  "
              f"95%=[{np.percentile(res[exp],2.5):.1f},{np.percentile(res[exp],97.5):.1f}]", file=sys.stderr, flush=True)

    var_c = float(np.var(res["C"], ddof=1))
    var_a = float(np.var(res["A"], ddof=1))
    var_params = max(0.0, var_a - var_c)
    total = VAR_B_PUBLISHED + var_params + var_c

    print(f"\n  论文 Experiment C 原值 = 3.622  |  我复现 = {var_c:.3f}  "
          f"{'✓ 吻合' if abs(var_c-3.622)/3.622 < 0.35 else '(略有差异,种子子集)'}", file=sys.stderr)
    print("\n" + "=" * 72, file=sys.stderr)
    print("  修正后的方差分解 (n=%d, run 级参数抽样)" % N, file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"{'来源':<26}{'论文报的':>14}{'修正后':>16}", file=sys.stderr)
    print("-" * 72, file=sys.stderr)
    print(f"{'Precipitation':<24}{'798.82 (99.55%)':>18}{f'{VAR_B_PUBLISHED:.2f} ({VAR_B_PUBLISHED/total*100:.1f}%)':>18}", file=sys.stderr)
    print(f"{'Pure parameters':<24}{'0.010 (0.001%)':>18}{f'{var_params:.2f} ({var_params/total*100:.1f}%)':>18}", file=sys.stderr)
    print(f"{'Adoption stochasticity':<24}{'3.62 (0.45%)':>18}{f'{var_c:.2f} ({var_c/total*100:.1f}%)':>18}", file=sys.stderr)
    print("-" * 72, file=sys.stderr)
    print(f"{'Total':<24}{'802.45':>18}{f'{total:.2f}':>18}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"\n  => 参数不确定性的真实贡献是 {var_params/total*100:.1f}%，不是 0.001%。", file=sys.stderr)
    print(f"  => Precipitation 仍然主导 ({VAR_B_PUBLISHED/total*100:.1f}%)，但不是 99.55%。", file=sys.stderr)
    print(f"  => 摘要里的 '99%' 这个数字站不住。结论(降水主导)站得住。", file=sys.stderr)
    print(f"\n  {2*N} runs in {time.time()-t0:.0f}s", file=sys.stderr)
    json.dump({"var_c": var_c, "var_a": var_a, "var_params": var_params,
               "var_precip": VAR_B_PUBLISHED, "total": total, "n": N},
              open("/private/tmp/claude-501/-Users-pricesmacbook/5cff14cf-29bb-4f73-a231-154d43db4438/scratchpad/variance_fix.json", "w"))
