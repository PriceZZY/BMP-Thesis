"""
Farm agent class for BMP adoption ABM.
Each agent represents a soil polygon (or farm parcel when data available).
"""

import numpy as np


class Farm:
    """A farm agent that decides whether to adopt BMPs."""

    def __init__(self, farm_id, area_ha, p_risk, risk_level,
                 drainage_score, slope_pct, clay_score, dist_to_water,
                 neighbors=None):
        # Identity
        self.farm_id = farm_id

        # Physical attributes (from GIS data)
        self.area_ha = area_ha
        self.area_acres = area_ha * 2.471  # 1 ha = 2.471 acres
        self.p_risk = p_risk                # 0-100 continuous score
        self.risk_level = risk_level        # 'Low', 'Medium', 'High'
        self.drainage_score = drainage_score  # 1-6
        self.slope_pct = slope_pct
        self.clay_score = clay_score        # 1-3
        self.dist_to_water = dist_to_water  # meters

        # BMP state
        self.has_type_a = False  # surface protection (cover crop, no-till)
        self.has_type_b = False  # fertilizer management (deep placement, 4R)

        # Tracking
        self.year_adopted_a = None
        self.year_adopted_b = None
        self.total_subsidy_received = 0

        # Transport chain attributes (set by environment)
        self.is_tile_drained = False       # P2: tile drainage flag
        self.baseline_adoption_prob = 0.2  # P1: additionality baseline
        self.is_additional = False         # P1: was this adoption additional?

        # Spatial neighbors (set after initialization)
        self.neighbors = neighbors or []

    @property
    def bmp_status(self):
        """Current BMP adoption status."""
        if self.has_type_a and self.has_type_b:
            return 'both'
        elif self.has_type_a:
            return 'type_a'
        elif self.has_type_b:
            return 'type_b'
        else:
            return 'none'

    @property
    def adopted(self):
        """Whether any BMP is adopted."""
        return self.has_type_a or self.has_type_b

    def adopt(self, bmp_type, year):
        """Adopt a BMP type."""
        if bmp_type in ('type_a', 'both'):
            if not self.has_type_a:
                self.has_type_a = True
                self.year_adopted_a = year
        if bmp_type in ('type_b', 'both'):
            if not self.has_type_b:
                self.has_type_b = True
                self.year_adopted_b = year

    def can_receive_subsidy(self, bmp_type):
        """Check if this farm can receive subsidy for a given BMP type."""
        if bmp_type == 'type_a':
            return not self.has_type_a
        elif bmp_type == 'type_b':
            return not self.has_type_b
        elif bmp_type == 'both':
            return not self.has_type_a or not self.has_type_b
        return False

    def neighbor_adoption_rate(self):
        """Fraction of neighbors who have adopted any BMP."""
        if not self.neighbors:
            return 0.0
        adopted = sum(1 for n in self.neighbors if n.adopted)
        return adopted / len(self.neighbors)

    def reset(self, keep_initial=False):
        """Reset farm state for new simulation run."""
        if not keep_initial:
            self.has_type_a = False
            self.has_type_b = False
            self.year_adopted_a = None
            self.year_adopted_b = None
        self.total_subsidy_received = 0

    def __repr__(self):
        return (f"Farm({self.farm_id}, {self.area_ha:.1f}ha, "
                f"risk={self.risk_level}, bmp={self.bmp_status})")
