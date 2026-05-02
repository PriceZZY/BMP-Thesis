"""
Spatial environment and phosphorus transport chain for the BMP ABM.

Implements the full P transport framework from PAPER_GUIDE Section 2:
  Source → Mobilization → Transport pathway → Delivery → Bioavailability

Key enhancements over basic ABM:
  - Precipitation variability (LogNormal annual multiplier)
  - Particulate:Dissolved split (80:20, matching Ontario field data)
  - Tile drainage penalty (Type A ineffective on tile-drained fields)
  - Additionality tracking (baseline adoption without subsidy)
  - Bioavailable P metric (PP×0.25 + DRP×1.0)
"""

import geopandas as gpd
import numpy as np
from pathlib import Path
from .farm_agent import Farm


# === BMP EFFECTIVENESS ===
# Type A: surface protection (cover crop, no-till) → reduces particulate P
REDUCTION_A = {
    'High':   {'mean': 0.60, 'std': 0.15},
    'Medium': {'mean': 0.30, 'std': 0.10},
    'Low':    {'mean': 0.10, 'std': 0.05},
}

# Type B: fertilizer management (subsurface placement, 4R) → reduces dissolved P
REDUCTION_B = {
    'High':   {'mean': 0.70, 'std': 0.10},
    'Medium': {'mean': 0.50, 'std': 0.10},
    'Low':    {'mean': 0.30, 'std': 0.10},
}

# === BASE P LOSS (kg/acre/year at mean precipitation) ===
BASE_P_LOSS = {
    'High':   {'mean': 1.50, 'std': 0.50},
    'Medium': {'mean': 0.50, 'std': 0.20},
    'Low':    {'mean': 0.15, 'std': 0.05},
}

# === P1: PARTICULATE:DISSOLVED RATIO (updated to 80:20 per Ontario data) ===
PARTICULATE_RATIO = {'mean': 0.80, 'min': 0.70, 'max': 0.90}

# === P1: PRECIPITATION VARIABILITY ===
# Thames P load ranges 80-670t (mean ~300t). LogNormal captures right skew.
# sigma=0.6 gives roughly 3x-4x range around mean (matching observed 80-670t)
# Corrected: mean_log = -sigma^2/2 so E[X] = 1.0 exactly
PRECIP_MULTIPLIER = {'mean_log': -0.18, 'sigma_log': 0.6}

# === P1: ADDITIONALITY — baseline adoption probability WITHOUT subsidy ===
# Low-risk farms adopt simple BMPs anyway; high-risk farms need more incentive
# Source: Claassen, Horowitz, Duquette, & Ueda (2014) Additionality in U.S.
# Agricultural Conservation, USDA ERS Report No. ERR-170; ~46% non-additionality
# for conservation tillage.
BASELINE_ADOPTION = {
    'Low': 0.40,     # Many low-risk farms do cover crops already
    'Medium': 0.20,  # Some adopt without subsidy
    'High': 0.10,    # Few adopt without incentive — this is where subsidy matters most
}

# === P2: TILE DRAINAGE PENALTY ===
# Farms with poor drainage (drainage_score >= 5) likely have tile drains
# Type A (surface BMP) cannot intercept subsurface DRP through tile drains
TILE_DRAIN_THRESHOLD = 5   # drainage_score >= 5 → tile-drained
TILE_DRAIN_TYPE_A_PENALTY = 0.50  # Type A effectiveness halved on tile-drained fields

# === INITIAL STATE ===
INITIAL_ADOPTION_RATE = 0.27  # Census 2021: 27% cover crops

# === POLICY TARGET ===
THAMES_P_REDUCTION_TARGET = 64.0  # tonnes/year (Thames share of 212t Canada target)


class ThamesEnvironment:
    """Manages the spatial environment and farm agents."""

    def __init__(self, data_path=None, stochastic=True, seed=None):
        self.stochastic = stochastic
        self.rng = np.random.RandomState(seed)

        if data_path is None:
            data_path = Path("D:/Claude/BMP-Thesis/data/processed")

        self.data_path = Path(data_path)
        self.farms = []
        self.current_precip_multiplier = 1.0  # Set per year in simulation

        self._load_farms()
        self._build_neighbor_graph()
        self._set_initial_adoption()

    def _load_farms(self):
        """Load farm agents from AAFC field-level GeoPackage."""
        field_path = self.data_path / "field_agents_upper_thames.gpkg"
        soil_path = self.data_path / "soil_p_risk_upper_thames.gpkg"

        if field_path.exists():
            gdf = gpd.read_file(field_path)
            source = "AAFC field polygons"
        elif soil_path.exists():
            gdf = gpd.read_file(soil_path)
            source = "soil polygons (fallback)"
        else:
            raise FileNotFoundError("No agent dataset found in processed/")

        for idx, row in gdf.iterrows():
            area_ha = row.get('area_ha', row.geometry.area / 10000)
            drainage = row.get('drainage_score', 3)

            farm = Farm(
                farm_id=idx,
                area_ha=area_ha,
                p_risk=row.get('p_risk', 50),
                risk_level=row.get('risk_level', 'Medium'),
                drainage_score=drainage,
                slope_pct=row.get('slope_pct', 3),
                clay_score=row.get('clay_score', 2),
                dist_to_water=row.get('dist_to_water', 2000),
            )
            # P2: Mark tile-drained farms
            farm.is_tile_drained = (drainage >= TILE_DRAIN_THRESHOLD)
            # P1: Set baseline adoption probability (additionality)
            farm.baseline_adoption_prob = BASELINE_ADOPTION.get(farm.risk_level, 0.20)

            self.farms.append(farm)

        self._geometries = gdf.geometry

        n_tile = sum(1 for f in self.farms if f.is_tile_drained)
        print(f"Loaded {len(self.farms)} field agents from {source}")
        print(f"  Total area: {sum(f.area_ha for f in self.farms):.0f} ha")
        print(f"  Avg field size: {np.mean([f.area_ha for f in self.farms]):.1f} ha")
        print(f"  Risk: High={sum(1 for f in self.farms if f.risk_level=='High')}, "
              f"Medium={sum(1 for f in self.farms if f.risk_level=='Medium')}, "
              f"Low={sum(1 for f in self.farms if f.risk_level=='Low')}")
        print(f"  Tile-drained: {n_tile} ({n_tile/len(self.farms)*100:.0f}%)")

    def _build_neighbor_graph(self):
        """Build spatial adjacency (500m buffer, capped at 15 neighbors).
        Uses spatial join for O(n log n) instead of O(n^2) pairwise comparison.
        """
        print("Building neighbor graph...")
        MAX_NEIGHBORS = 15

        buffered = self._geometries.buffer(500)
        buff_gdf = gpd.GeoDataFrame(geometry=buffered, crs=self._geometries.crs)
        orig_gdf = gpd.GeoDataFrame(geometry=self._geometries, crs=self._geometries.crs)

        joined = gpd.sjoin(buff_gdf, orig_gdf, how='inner', predicate='intersects')
        joined = joined[joined.index != joined['index_right']]

        neighbor_map = joined.groupby(joined.index)['index_right'].apply(list).to_dict()

        for i, farm in enumerate(self.farms):
            candidates_idx = neighbor_map.get(i, [])
            if len(candidates_idx) > MAX_NEIGHBORS:
                chosen = self.rng.choice(candidates_idx, MAX_NEIGHBORS, replace=False)
                farm.neighbors = [self.farms[j] for j in chosen]
            else:
                farm.neighbors = [self.farms[j] for j in candidates_idx]

        avg = np.mean([len(f.neighbors) for f in self.farms])
        print(f"  Average neighbors: {avg:.1f} (capped at {MAX_NEIGHBORS})")

    def _set_initial_adoption(self):
        """Set 27% of farms as already having Type A (cover crops).
        Biased toward low-risk farms (they adopt more easily)."""
        n_adopted = int(len(self.farms) * INITIAL_ADOPTION_RATE)
        sorted_farms = sorted(self.farms, key=lambda f: f.p_risk)
        for farm in sorted_farms[:n_adopted]:
            farm.has_type_a = True
            farm.year_adopted_a = 0
            farm.is_additional = False  # Pre-existing, not additional

        print(f"  Initial adoption: {n_adopted} farms ({INITIAL_ADOPTION_RATE*100:.0f}%)")

    def sample_precip_multiplier(self):
        """Sample annual precipitation multiplier from LogNormal distribution.
        mean=1.0 (average year), range roughly 0.3-3.0 (dry to wet).
        """
        if self.stochastic:
            return self.rng.lognormal(
                PRECIP_MULTIPLIER['mean_log'],
                PRECIP_MULTIPLIER['sigma_log']
            )
        return 1.0

    def base_p_loss(self, farm, sample=True):
        """Base annual P loss (kg). Scaled by precipitation multiplier."""
        params = BASE_P_LOSS[farm.risk_level]
        if sample and self.stochastic:
            rate = self.rng.normal(params['mean'], params['std'])
            rate = max(0.01, rate)
        else:
            rate = params['mean']
        return farm.area_acres * rate * self.current_precip_multiplier

    def p_reduction_detailed(self, farm, sample=True):
        """Calculate P reduction with full transport chain detail.

        Returns dict with:
          - total_reduction_kg: total P reduced
          - pp_reduction_kg: particulate P reduced
          - drp_reduction_kg: dissolved reactive P reduced
          - bioavailable_reduction_kg: PP*0.25 + DRP*1.0
          - is_additional: whether this adoption was above baseline
        """
        if not farm.adopted:
            return {
                'total_reduction_kg': 0, 'pp_reduction_kg': 0,
                'drp_reduction_kg': 0, 'bioavailable_reduction_kg': 0,
                'is_additional': False,
            }

        base = self.base_p_loss(farm, sample=sample)

        # Split into particulate and dissolved (P1: updated to 80:20)
        if sample and self.stochastic:
            p_ratio = self.rng.uniform(PARTICULATE_RATIO['min'], PARTICULATE_RATIO['max'])
        else:
            p_ratio = PARTICULATE_RATIO['mean']

        pp_base = base * p_ratio
        drp_base = base * (1 - p_ratio)

        pp_reduced = 0
        drp_reduced = 0

        # Type A: reduces particulate P
        if farm.has_type_a:
            red_a = REDUCTION_A[farm.risk_level]
            if sample and self.stochastic:
                r = np.clip(self.rng.normal(red_a['mean'], red_a['std']), 0.05, 0.95)
            else:
                r = red_a['mean']

            # P2: Tile drainage penalty — surface BMP less effective on tile-drained fields
            if farm.is_tile_drained:
                r *= (1 - TILE_DRAIN_TYPE_A_PENALTY)

            pp_reduced = pp_base * r

        # Type B: reduces dissolved reactive P
        if farm.has_type_b:
            red_b = REDUCTION_B[farm.risk_level]
            if sample and self.stochastic:
                r = np.clip(self.rng.normal(red_b['mean'], red_b['std']), 0.05, 0.95)
            else:
                r = red_b['mean']
            drp_reduced = drp_base * r

        total = pp_reduced + drp_reduced

        # P1: Bioavailable P (PP is 25% bioavailable, DRP is 100%)
        bioavailable = pp_reduced * 0.25 + drp_reduced * 1.0

        return {
            'total_reduction_kg': total,
            'pp_reduction_kg': pp_reduced,
            'drp_reduction_kg': drp_reduced,
            'bioavailable_reduction_kg': bioavailable,
            'is_additional': getattr(farm, 'is_additional', True),
        }

    def p_reduction(self, farm, sample=True):
        """Backward-compatible: return total P reduction in kg."""
        return self.p_reduction_detailed(farm, sample)['total_reduction_kg']

    def total_p_reduction(self, sample=True):
        """Total P reduction from all adopted BMPs (kg)."""
        return sum(self.p_reduction(f, sample) for f in self.farms)

    def total_p_load(self, sample=True):
        """Total annual P load (kg)."""
        return sum(self.base_p_loss(f, sample) - self.p_reduction(f, sample)
                   for f in self.farms)

    def detailed_metrics(self, sample=False):
        """Compute full transport-chain metrics for current state."""
        total_base = 0
        total_pp_red = 0
        total_drp_red = 0
        total_bioavail_red = 0
        additional_reduction = 0

        for farm in self.farms:
            total_base += self.base_p_loss(farm, sample)
            d = self.p_reduction_detailed(farm, sample)
            total_pp_red += d['pp_reduction_kg']
            total_drp_red += d['drp_reduction_kg']
            total_bioavail_red += d['bioavailable_reduction_kg']
            if d['is_additional']:
                additional_reduction += d['total_reduction_kg']

        total_reduction = total_pp_red + total_drp_red

        return {
            'base_load_tonnes': total_base / 1000,
            'total_reduction_tonnes': total_reduction / 1000,
            'pp_reduction_tonnes': total_pp_red / 1000,
            'drp_reduction_tonnes': total_drp_red / 1000,
            'bioavailable_reduction_tonnes': total_bioavail_red / 1000,
            'additional_reduction_tonnes': additional_reduction / 1000,
            'current_load_tonnes': (total_base - total_reduction) / 1000,
            'target_tonnes': THAMES_P_REDUCTION_TARGET,
            'target_achievement_pct': (total_reduction / 1000) / THAMES_P_REDUCTION_TARGET * 100,
            'additional_target_pct': (additional_reduction / 1000) / THAMES_P_REDUCTION_TARGET * 100,
            'precip_multiplier': self.current_precip_multiplier,
        }

    def summary(self):
        """Quick state summary."""
        total_farms = len(self.farms)
        adopted_a = sum(1 for f in self.farms if f.has_type_a)
        adopted_b = sum(1 for f in self.farms if f.has_type_b)
        adopted_both = sum(1 for f in self.farms if f.has_type_a and f.has_type_b)
        adopted_any = sum(1 for f in self.farms if f.adopted)

        return {
            'total_farms': total_farms,
            'adopted_any': adopted_any,
            'adopted_a': adopted_a,
            'adopted_b': adopted_b,
            'adopted_both': adopted_both,
            'adoption_rate': adopted_any / total_farms,
            'total_area_ha': sum(f.area_ha for f in self.farms),
        }

    def reset(self):
        """Reset all farms for new simulation run."""
        for farm in self.farms:
            farm.reset()
            farm.is_additional = False
            farm._type_b_spent = 0
        self._set_initial_adoption()
        self.current_precip_multiplier = 1.0
        self.rng = np.random.RandomState()
