"""Re-run the JGLR Monte Carlo, recording the bioavailable / PP / DRP metrics
that the original monte_carlo.py computed but discarded.

Faithfulness check: seed 1000 FCFS must reproduce p_reduction_t = 51.25869938923559
from results/monte_carlo_results.json.
"""
import sys, os, json, time, copy
from multiprocessing import Pool

sys.setrecursionlimit(1_000_000)

REPO = "/Users/pricesmacbook/Documents/世界认知/claude/BMP-Thesis"
os.chdir(REPO)
sys.path.insert(0, "src")

STRATEGIES = ["FCFS", "NaiveHotspot", "SmartHotspot", "EfficiencyPricing", "ModerateEfficiency"]

_TEMPLATE = None


def make_strategy(name, seed):
    from model.subsidy_strategies import (
        FirstComeFirstServed, HotspotPriority, SmartHotspot, EfficiencyPricing)
    if name == "FCFS":
        return FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    if name == "NaiveHotspot":
        return HotspotPriority(high_subsidy=50, med_subsidy=30, seed=seed)
    if name == "SmartHotspot":
        return SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)
    if name == "EfficiencyPricing":
        return EfficiencyPricing(subsidy_a=15, subsidy_b=60, seed=seed)
    if name == "ModerateEfficiency":
        return EfficiencyPricing(subsidy_a=25, subsidy_b=40, seed=seed)
    raise ValueError(name)


def init_worker():
    import model.adoption_function as af
    af.PARAMS["intercept"] = -2.00
    af.PARAMS["subsidy_coeff"] = 0.010


def run_one(args):
    """Construct a fresh environment per run — exactly as src/analysis/monte_carlo.py does.
    A deepcopy-and-reseed shortcut was tried and REJECTED by the reproducibility check:
    environment construction itself draws from the RNG, so a reused template desyncs."""
    seed, strat = args
    import io, contextlib
    import model.adoption_function as af
    from model.environment import ThamesEnvironment
    from model.simulation import run_single_simulation

    af.PARAMS["intercept"] = -2.00
    af.PARAMS["subsidy_coeff"] = 0.010

    with contextlib.redirect_stdout(io.StringIO()):
        env = ThamesEnvironment(data_path="data/processed", stochastic=True, seed=seed)
        run = run_single_simulation(env, make_strategy(strat, seed), years=4, seed=seed)
    y4 = run[-1]
    return {
        "seed": seed,
        "strategy": strat,
        "p_reduction_t": float(y4["p_reduction_tonnes"]),
        "pp_reduction_t": float(y4["pp_reduction_tonnes"]),
        "drp_reduction_t": float(y4["drp_reduction_tonnes"]),
        "bioavailable_reduction_t": float(y4["bioavailable_reduction_tonnes"]),
        "additional_reduction_t": float(y4["additional_reduction_tonnes"]),
        "total_cost": float(sum(r["total_cost"] for r in run)),
        "adopted_type_a": int(y4["adopted_type_a"]),
        "adopted_type_b": int(y4["adopted_type_b"]),
    }


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seeds = list(range(1000, 1000 + n_seeds))
    jobs = [(s, st) for s in seeds for st in STRATEGIES]

    t0 = time.time()
    with Pool(processes=8, initializer=init_worker) as pool:
        out = pool.map(run_one, jobs, chunksize=8)
    print(f"{len(out)} runs in {time.time()-t0:.0f}s", file=sys.stderr)

    # FAITHFULNESS CHECK against the published results file
    ref = 51.25869938923559
    got = next(r["p_reduction_t"] for r in out if r["seed"] == 1000 and r["strategy"] == "FCFS")
    ok = abs(got - ref) < 1e-9
    print(f"REPRODUCIBILITY CHECK seed=1000 FCFS: got {got!r} vs published {ref!r} -> "
          f"{'EXACT MATCH' if ok else '*** MISMATCH ***'}", file=sys.stderr)
    if not ok:
        sys.exit("Refusing to report numbers from a harness that does not reproduce the paper.")

    path = "/private/tmp/claude-501/-Users-pricesmacbook/5cff14cf-29bb-4f73-a231-154d43db4438/scratchpad/mc_bioavail.json"
    with open(path, "w") as f:
        json.dump({"n_seeds": n_seeds, "runs": out}, f)
    print(f"wrote {path}", file=sys.stderr)
