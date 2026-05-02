"""
Subsidy allocation strategies for BMP adoption.
Each strategy determines: which farms get subsidized, what BMP type, how much.

Policy constraints:
- Both FCFS and Hotspot can offer Type A, Type B, or both
- Difference is only in ordering (random vs P-risk) and subsidy amount
- This ensures fair comparison between strategies
"""

import numpy as np


class BaseStrategy:
    """Base class for subsidy allocation strategies."""

    def order_farms(self, farms):
        raise NotImplementedError

    def allocate(self, farm, remaining_budget):
        raise NotImplementedError

    def _make_offer(self, farm, bmp_type, subsidy_per_acre):
        """Helper to create a properly formatted offer."""
        if bmp_type == 'none':
            return {'type': 'none', 'subsidy_per_acre': 0, 'total_cost': 0}

        total = subsidy_per_acre * farm.area_acres
        return {
            'type': bmp_type,
            'subsidy_per_acre': subsidy_per_acre,
            'total_cost': total
        }

    def _determine_bmp_type(self, farm):
        """Determine what BMP to offer based on what farm already has."""
        if not farm.has_type_a and not farm.has_type_b:
            return 'both'      # Offer both at once (real policy allows this)
        elif farm.has_type_a and not farm.has_type_b:
            return 'type_b'
        elif not farm.has_type_a and farm.has_type_b:
            return 'type_a'
        else:
            return 'none'      # Already has both


class FirstComeFirstServed(BaseStrategy):
    """
    Current policy: random order, fixed subsidy rate.
    All farms get same offer regardless of P-risk.
    Can offer both A+B in one year (matches real UTRCA policy).
    """

    def __init__(self, subsidy_a=30, subsidy_b=30, seed=None):
        self.subsidy_a = subsidy_a
        self.subsidy_b = subsidy_b
        self.rng = np.random.RandomState(seed)

    def order_farms(self, farms):
        shuffled = list(farms)
        self.rng.shuffle(shuffled)
        return shuffled

    def allocate(self, farm, remaining_budget):
        bmp_type = self._determine_bmp_type(farm)
        if bmp_type == 'none':
            return self._make_offer(farm, 'none', 0)

        # Fixed subsidy for all farms
        if bmp_type == 'both':
            subsidy = self.subsidy_a + self.subsidy_b  # $30 + $30 = $60/acre
        elif bmp_type == 'type_a':
            subsidy = self.subsidy_a
        else:
            subsidy = self.subsidy_b

        offer = self._make_offer(farm, bmp_type, subsidy)

        if offer['total_cost'] > remaining_budget:
            # Try offering just one type if both is too expensive
            if bmp_type == 'both':
                offer = self._make_offer(farm, 'type_a', self.subsidy_a)
                if offer['total_cost'] > remaining_budget:
                    return self._make_offer(farm, 'none', 0)
            else:
                return self._make_offer(farm, 'none', 0)

        return offer


class HotspotPriority(BaseStrategy):
    """
    Proposed: prioritize high-risk farms, variable subsidy by risk level.
    Low-risk farms get no subsidy (budget focused on where it matters).
    Can also offer both A+B (same as FCFS for fair comparison).
    """

    def __init__(self, high_subsidy=50, med_subsidy=30, seed=None):
        self.high_subsidy = high_subsidy
        self.med_subsidy = med_subsidy
        self.rng = np.random.RandomState(seed)

    def order_farms(self, farms):
        return sorted(farms, key=lambda f: f.p_risk, reverse=True)

    def allocate(self, farm, remaining_budget):
        bmp_type = self._determine_bmp_type(farm)
        if bmp_type == 'none':
            return self._make_offer(farm, 'none', 0)

        if farm.risk_level == 'High':
            if bmp_type == 'both':
                subsidy = self.high_subsidy * 2
            else:
                subsidy = self.high_subsidy
        elif farm.risk_level == 'Medium':
            if bmp_type == 'both':
                subsidy = self.med_subsidy * 2
            else:
                subsidy = self.med_subsidy
        else:
            return self._make_offer(farm, 'none', 0)

        offer = self._make_offer(farm, bmp_type, subsidy)

        if offer['total_cost'] > remaining_budget:
            if bmp_type == 'both':
                single_sub = self.high_subsidy if farm.risk_level == 'High' else self.med_subsidy
                offer = self._make_offer(farm, 'type_a', single_sub)
                if offer['total_cost'] > remaining_budget:
                    return self._make_offer(farm, 'none', 0)
            else:
                return self._make_offer(farm, 'none', 0)

        return offer


class EfficiencyPricing(BaseStrategy):
    """
    Price by bioavailable P reduction efficiency.
    DRP is 100% bioavailable → heavy subsidy for Type B
    PP is 25% bioavailable → light subsidy for Type A
    Random order (FCFS) — isolates pricing effect from spatial effect.
    """

    def __init__(self, subsidy_a=15, subsidy_b=60, seed=None):
        self.subsidy_a = subsidy_a
        self.subsidy_b = subsidy_b
        self.rng = np.random.RandomState(seed)

    def order_farms(self, farms):
        shuffled = list(farms)
        self.rng.shuffle(shuffled)
        return shuffled

    def allocate(self, farm, remaining_budget):
        # Prioritize Type B (high bioavailable impact)
        if not farm.has_type_b:
            offer = self._make_offer(farm, 'type_b', self.subsidy_b)
        elif not farm.has_type_a:
            offer = self._make_offer(farm, 'type_a', self.subsidy_a)
        else:
            return {'type': 'none', 'subsidy_per_acre': 0, 'total_cost': 0}

        if offer['total_cost'] > remaining_budget:
            return {'type': 'none', 'subsidy_per_acre': 0, 'total_cost': 0}
        return offer


class SmartHotspot(BaseStrategy):
    """
    Spatial targeting with FCFS-identical subsidy rates.

    Key insight: Naive Hotspot fails because $100/acre for high-risk farms
    hits the $75K/farm cap in <5 years, wasting budget capacity.

    SmartHotspot keeps the same per-acre rates as FCFS ($30 A, $30 B),
    but changes TWO things:
      1. ORDER: high P-risk farms get offered first (not random)
      2. FILTER: low-risk farms get nothing (budget saved for high/medium)

    This isolates the pure effect of spatial prioritization from
    subsidy pricing -- the only difference vs FCFS is WHO gets the money,
    not HOW MUCH.
    """

    def __init__(self, subsidy_a=30, subsidy_b=30, seed=None):
        self.subsidy_a = subsidy_a
        self.subsidy_b = subsidy_b
        self.rng = np.random.RandomState(seed)

    def order_farms(self, farms):
        return sorted(farms, key=lambda f: f.p_risk, reverse=True)

    def allocate(self, farm, remaining_budget):
        if farm.risk_level == 'Low':
            return self._make_offer(farm, 'none', 0)

        bmp_type = self._determine_bmp_type(farm)
        if bmp_type == 'none':
            return self._make_offer(farm, 'none', 0)

        if bmp_type == 'both':
            subsidy = self.subsidy_a + self.subsidy_b
        elif bmp_type == 'type_a':
            subsidy = self.subsidy_a
        else:
            subsidy = self.subsidy_b

        offer = self._make_offer(farm, bmp_type, subsidy)

        if offer['total_cost'] > remaining_budget:
            if bmp_type == 'both':
                offer = self._make_offer(farm, 'type_a', self.subsidy_a)
                if offer['total_cost'] > remaining_budget:
                    return self._make_offer(farm, 'none', 0)
            else:
                return self._make_offer(farm, 'none', 0)

        return offer
