"""
Empirical adoption probability function.
Based on logit model from farmer adoption literature.

Key references:
- Palm-Forster, Swinton, & Shupp (2017) JSWC 72(5):493-505
- Liu, Bruins, & Heberling (2018) Sustainability 10(2):432
- Prokopy et al. (2019) JSWC 74(5):520-534

Adoption probability is a logistic function of:
  - Net economic benefit (subsidy - cost)
  - Farm size (larger farms adopt more)
  - Peer effect (neighbor adoption rate)
"""

import numpy as np


# Adoption function parameters
# These are initial estimates; will be calibrated to match UTRCA Year 1 data
PARAMS = {
    'intercept': -2.00,         # Calibrated v5 (with participation filter)
    'subsidy_coeff': 0.010,     # Calibrated v5
    'area_coeff': 0.002,        # Per acre: larger farms slightly more likely
    'peer_coeff': 1.5,          # Neighbor adoption rate multiplier
    'risk_aversion': 0.3,       # Random noise std (captures non-economic factors)
    'max_adoption_prob': 0.85,  # Ceiling: some farmers never adopt
}
# Calibration note: intercept and subsidy_coeff calibrated via grid search
# to approximate UTRCA Year 1 results (595 projects, 35000 acres, 5.7t P).
# Calibration aligns Year 1 simulation outputs with UTRCA Year 1 totals (595 projects,
# 35,000 acres, 5.7 t P) at field-polygon granularity (8,949 AAFC fields, mean 26.1 ha;
# see paper §3.2 / §4.1).

# BMP costs ($/acre, net of subsidy = what farmer pays out of pocket)
BMP_COSTS = {
    'type_a': 25,   # Typical cover crop/no-till cost per acre
    'type_b': 35,   # Midpoint of OMAFA 2025 Pub 60 Type B implementation cost range ($20-50/acre)
    'both': 55,     # Combined (slight discount from sum of 25+35=60)
}

# Long-term benefit ($/acre/year, undiscounted; see paper §4.1 / Appendix A)
# Cover crops improve soil health → future yield gains
LONG_TERM_BENEFIT = {
    'type_a': 5,    # Modest long-term soil benefit
    'type_b': 3,    # Less long-term benefit from fertilizer management
    'both': 10,     # Synergy bonus
}


def adoption_probability(farm, offer, rng=None, params=None):
    """
    Calculate probability that a farm adopts the offered BMP.

    Args:
        farm: Farm agent
        offer: dict with 'type', 'subsidy_per_acre'
        rng: numpy RandomState for stochastic component
        params: override default parameters (for calibration)

    Returns:
        float: probability [0, max_adoption_prob]
    """
    if params is None:
        params = PARAMS

    bmp_type = offer['type']
    subsidy_per_acre = offer.get('subsidy_per_acre', 30)

    # Net benefit per acre
    cost = BMP_COSTS.get(bmp_type, 25)
    benefit = LONG_TERM_BENEFIT.get(bmp_type, 5)
    net_benefit = subsidy_per_acre - cost + benefit

    # Logit components
    logit = (
        params['intercept']
        + params['subsidy_coeff'] * net_benefit
        + params['area_coeff'] * farm.area_acres
        + params['peer_coeff'] * farm.neighbor_adoption_rate()
    )

    # Base probability (logistic sigmoid)
    base_prob = 1.0 / (1.0 + np.exp(-logit))

    # Add stochastic noise (captures non-economic factors)
    if rng is not None:
        noise = rng.normal(0, params['risk_aversion'])
        base_prob = base_prob + noise

    # Clamp to [0, max]
    prob = np.clip(base_prob, 0.0, params['max_adoption_prob'])

    return prob
