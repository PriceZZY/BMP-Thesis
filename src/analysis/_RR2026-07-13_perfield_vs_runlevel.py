"""决定性检验：如果只把那个反向开关修好（保留【逐田块】抽样），
参数对流域总量方差的贡献会是多少？

这决定了 bug 的严重性：
  若 ≈0  -> 论文报的 0.001% 歪打正着是对的，bug 是"难看"不是"错"
  若 显著 -> 论文的数字是错的

方法：precip 固定在 1.0（同论文 Experiment A/C 设计），比较
  C   : 参数钉死在均值           -> 仅采纳噪声
  B'  : 参数【逐田块】独立抽样    -> 采纳噪声 + 逐田块参数噪声
  A'  : 参数【run 级】抽样        -> 采纳噪声 + 认知不确定性
"""
import sys, os, io, json, time, contextlib
import numpy as np
from multiprocessing import Pool

import pathlib
# 仓根按脚本自身位置推出来，与仓内其他脚本同款（fig8_tornado.py:10 等）。
# ⚠️ 原先写死绝对路径 —— 本机外不可运行，且会把作者的用户名与本地目录结构
#    公开到仓库里。`6c3ae58` 那笔提交刚移除过全仓 35 处硬编码路径，这三个
#    R&R 脚本是之后新写的，同一个病又长了回来（审计 B10 #5 点名）。
REPO = str(pathlib.Path(__file__).resolve().parents[2])
os.chdir(REPO); sys.path.insert(0, "src")
N = 400


def run_one(args):
    seed, mode = args
    import model.adoption_function as af
    import model.environment as em
    from model.subsidy_strategies import FirstComeFirstServed
    from model.simulation import run_single_simulation
    af.PARAMS["intercept"] = -2.00; af.PARAMS["subsidy_coeff"] = 0.010

    with contextlib.redirect_stdout(io.StringIO()):
        env = em.ThamesEnvironment(data_path="data/processed", stochastic=True, seed=seed)
        env.current_precip_multiplier = 1.0
        env.sample_precip_multiplier = lambda: 1.0     # 固定降水

        if mode == "C":
            env.use_mean_params()

        elif mode == "PERFIELD":
            # 复刻"只修开关"的世界：每次取参数都重新抽一次（逐田块/逐调用）
            env.use_mean_params()
            rng = np.random.RandomState(seed + 31337)
            def per_field(sample=True, _e=env, _r=rng):
                return {
                    'BASE_P_LOSS': {k: max(0.01, _r.normal(v['mean'], v['std']))
                                    for k, v in em.BASE_P_LOSS.items()},
                    'REDUCTION_A': {k: float(np.clip(_r.normal(v['mean'], v['std']), .05, .95))
                                    for k, v in em.REDUCTION_A.items()},
                    'REDUCTION_B': {k: float(np.clip(_r.normal(v['mean'], v['std']), .05, .95))
                                    for k, v in em.REDUCTION_B.items()},
                    'PARTICULATE_RATIO': float(_r.uniform(em.PARTICULATE_RATIO['min'],
                                                          em.PARTICULATE_RATIO['max'])),
                }
            env._active_params = per_field      # 每个田块一次新抽样

        # mode == "RUNLEVEL": 用构造函数里已经抽好的 run 级 realization（默认行为）

        run = run_single_simulation(env, FirstComeFirstServed(30, 30, seed=seed), years=4, seed=seed)
    return float(run[-1]["p_reduction_tonnes"])


if __name__ == "__main__":
    seeds = list(range(8000, 8000 + N))
    out = {}
    for mode, lab in [("C", "C        参数钉死均值 (仅采纳噪声)"),
                      ("PERFIELD", "B'  逐田块抽样 (=只修开关)"),
                      ("RUNLEVEL", "A'  run级抽样  (=认知不确定性)")]:
        with Pool(8) as p:
            v = p.map(run_one, [(s, mode) for s in seeds], chunksize=8)
        out[mode] = v
        print(f"  {lab:36s} var={np.var(v, ddof=1):9.3f}  mean={np.mean(v):6.2f}t", file=sys.stderr, flush=True)

    vc = np.var(out["C"], ddof=1)
    vpf = np.var(out["PERFIELD"], ddof=1)
    vrl = np.var(out["RUNLEVEL"], ddof=1)
    VB = 798.8181800373691   # 论文 Experiment B (降水), 干净

    print("\n" + "=" * 74, file=sys.stderr)
    print("  参数对方差的净贡献 (= var − var_C)", file=sys.stderr)
    print("=" * 74, file=sys.stderr)
    pf, rl = max(0, vpf - vc), max(0, vrl - vc)
    print(f"  只修开关 (逐田块) : {pf:8.3f}   -> 占总方差 {pf/(VB+pf+vc)*100:5.2f}%", file=sys.stderr)
    print(f"  run 级抽样        : {rl:8.3f}   -> 占总方差 {rl/(VB+rl+vc)*100:5.2f}%", file=sys.stderr)
    print(f"  论文报的          :    0.010   -> 占总方差  0.001%", file=sys.stderr)
    print("=" * 74, file=sys.stderr)
    verdict = ("论文的 0.001% 【歪打正着是对的】—— bug 难看但不实质影响该数字"
               if pf / (VB + pf + vc) < 0.01 else
               "论文的 0.001% 【是错的】—— 即使只修开关也会得到显著的参数方差")
    print(f"\n  => 只修开关的话: {verdict}", file=sys.stderr)
    print(f"  => 但 run 级抽样才是方差分解【该问的问题】(认知不确定性), 它给出 {rl/(VB+rl+vc)*100:.1f}%", file=sys.stderr)
    json.dump({"var_C": vc, "var_perfield": vpf, "var_runlevel": vrl, "var_precip": VB, "n": N},
              open(f"{REPO}/results/_RR2026-07-13_bug_severity_perfield_vs_runlevel.json", "w"))
