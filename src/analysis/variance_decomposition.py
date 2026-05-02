"""
Variance Decomposition: what drives the spread in P reduction outcomes?
Three experiments, each 1000 MC runs, FCFS only:
  A: Fix precip=1.0, vary everything else → parameter + adoption variance
  B: Fix all params to mean, vary precip only → precipitation variance
  C: Fix precip and params, vary adoption rng only → adoption noise
"""
import sys
sys.path.insert(0, "D:/Claude/BMP-Thesis/src")

import numpy as np
import json
import time
from multiprocessing import Pool
from pathlib import Path

RESULTS = Path("D:/Claude/BMP-Thesis/results")
N_RUNS = 1000


def run_experiment(args):
    seed, experiment = args

    import model.adoption_function as adopt_mod
    import model.environment as env_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed
    from model.simulation import run_single_simulation, PARTICIPATION_RATES

    adopt_mod.PARAMS['intercept'] = -2.00

    if experiment == 'A':
        # Fix precipitation, vary parameters + adoption
        env = ThamesEnvironment(stochastic=True, seed=seed)
        env.current_precip_multiplier = 1.0  # Fixed

        # Override sample_precip to always return 1.0
        env.sample_precip_multiplier = lambda: 1.0

        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
        run = run_single_simulation(env, strategy, years=4, seed=seed)

    elif experiment == 'B':
        # Fix parameters to mean, vary precipitation only
        env = ThamesEnvironment(stochastic=False, seed=seed)  # deterministic params

        # But enable stochastic precipitation
        precip_rng = np.random.RandomState(seed)
        env.sample_precip_multiplier = lambda: precip_rng.lognormal(-0.18, 0.6)

        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)

        # Need participation filter
        part_rng = np.random.RandomState(seed + 50000)
        env.reset()
        for farm in env.farms:
            farm._type_b_spent = 0
            farm.is_additional = False
            rate = PARTICIPATION_RATES.get(farm.risk_level, 0.40)
            farm._will_participate = part_rng.random() < rate
        env.rng = np.random.RandomState(seed)

        from model.simulation import simulate_program
        run = simulate_program(env, strategy, years=4, seed=seed)

    elif experiment == 'C':
        # Fix precipitation and parameters, vary adoption rng only
        env = ThamesEnvironment(stochastic=False, seed=42)  # Same params every time
        env.sample_precip_multiplier = lambda: 1.0  # Fixed precip

        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)

        # Participation varies with seed (adoption noise)
        part_rng = np.random.RandomState(seed + 50000)
        env.reset()
        for farm in env.farms:
            farm._type_b_spent = 0
            farm.is_additional = False
            rate = PARTICIPATION_RATES.get(farm.risk_level, 0.40)
            farm._will_participate = part_rng.random() < rate
        env.rng = np.random.RandomState(seed)

        from model.simulation import simulate_program
        run = simulate_program(env, strategy, years=4, seed=seed)

    y4 = run[-1]
    return {
        'seed': seed, 'experiment': experiment,
        'y4_p': float(y4['p_reduction_tonnes']),
    }


if __name__ == '__main__':
    print(f"Variance Decomposition: 3 experiments x {N_RUNS} runs")

    jobs = []
    for exp in ['A', 'B', 'C']:
        for i in range(N_RUNS):
            jobs.append((i + 8000, exp))

    t0 = time.time()
    with Pool(processes=14) as pool:
        results = pool.map(run_experiment, jobs)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.0f}s ({elapsed/60:.1f} min)")

    # Analyze
    for exp in ['A', 'B', 'C']:
        vals = [r['y4_p'] for r in results if r['experiment'] == exp]
        print(f"\n  Experiment {exp}:")
        print(f"    Mean: {np.mean(vals):.1f}t")
        print(f"    Std:  {np.std(vals):.1f}t")
        print(f"    Var:  {np.var(vals):.1f}")
        print(f"    Range: [{np.min(vals):.1f}, {np.max(vals):.1f}]")

    var_a = np.var([r['y4_p'] for r in results if r['experiment'] == 'A'])
    var_b = np.var([r['y4_p'] for r in results if r['experiment'] == 'B'])
    var_c = np.var([r['y4_p'] for r in results if r['experiment'] == 'C'])

    # Orthogonal variance decomposition: Experiment A = pure_params + adoption;
    # subtract C to isolate pure-parameter contribution. Precip (B), pure_params,
    # and adoption are mutually exclusive, so pct sums to 100% by construction.
    var_precip = var_b
    var_pure_params = var_a - var_c
    var_adoption = var_c
    total_var = var_precip + var_pure_params + var_adoption  # = var_b + var_a

    pct_precip = var_precip / total_var * 100
    pct_pure_params = var_pure_params / total_var * 100
    pct_adoption = var_adoption / total_var * 100

    print(f"\n  Orthogonal Variance Decomposition:")
    print(f"    Precipitation (B):         {var_precip:.2f} ({pct_precip:.2f}%)")
    print(f"    Pure parameters (A-C):     {var_pure_params:.4f} ({pct_pure_params:.3f}%)")
    print(f"    Adoption stochasticity (C):{var_adoption:.2f} ({pct_adoption:.2f}%)")
    print(f"    Total:                     {total_var:.2f} (100.00%)")

    output = {
        'n_runs': N_RUNS,
        # Orthogonal partition (canonical)
        'var_precip': float(var_precip),
        'var_pure_params': float(var_pure_params),
        'var_adoption': float(var_adoption),
        'total_var': float(total_var),
        'pct_precip': float(pct_precip),
        'pct_pure_params': float(pct_pure_params),
        'pct_adoption': float(pct_adoption),
        # Legacy experiment-level variances (retained for traceability)
        'variance_A_params': float(var_a),
        'variance_B_precip': float(var_b),
        'variance_C_adoption': float(var_c),
    }
    with open(RESULTS / "variance_decomposition.json", 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {RESULTS / 'variance_decomposition.json'}")
