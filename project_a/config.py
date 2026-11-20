"""
Configuration for Indian Income Tax Rules.
Statutory sources:
- Income-tax Act, 1961
- Finance Act 2024 & Finance (No. 2) Act 2024 (for FY 2024-25 / AY 2025-26)
- Finance Act 2025 (for FY 2025-26 / AY 2026-27)
"""
from dataclasses import dataclass
from typing import List, Tuple

# Section limits
SEC_80C_MAX = 150000.0
SEC_80CCD_1B_MAX = 50000.0
SEC_80D_NORMAL_MAX = 25000.0
SEC_80D_SENIOR_MAX = 50000.0
SEC_24B_MAX = 200000.0  # Self-occupied property interest loss
CESS_RATE = 0.04

# FY 2024-25 Parameters
STD_DEDUCTION_OLD_2024_25 = 50000.0
STD_DEDUCTION_NEW_2024_25 = 75000.0  # Increased by Finance (No. 2) Act 2024

OLD_REGIME_REBATE_87A_LIMIT = 500000.0
OLD_REGIME_REBATE_87A_MAX = 12500.0

NEW_REGIME_REBATE_87A_LIMIT_2024_25 = 700000.0
NEW_REGIME_REBATE_87A_MAX_2024_25 = 25000.0

# Old Regime Slabs (General Individual < 60)
OLD_REGIME_SLABS_GENERAL: List[Tuple[float, float, float]] = [
    (0.0, 250000.0, 0.0),
    (250000.0, 500000.0, 0.05),
    (500000.0, 1000000.0, 0.20),
    (1000000.0, float('inf'), 0.30)
]

# Old Regime Slabs (Senior Citizen 60 - 79)
OLD_REGIME_SLABS_SENIOR: List[Tuple[float, float, float]] = [
    (0.0, 300000.0, 0.0),
    (300000.0, 500000.0, 0.05),
    (500000.0, 1000000.0, 0.20),
    (1000000.0, float('inf'), 0.30)
]

# Old Regime Slabs (Super Senior Citizen 80+)
OLD_REGIME_SLABS_SUPER_SENIOR: List[Tuple[float, float, float]] = [
    (0.0, 500000.0, 0.0),
    (500000.0, 1000000.0, 0.20),
    (1000000.0, float('inf'), 0.30)
]

# New Regime Slabs FY 2024-25 (Finance (No. 2) Act 2024)
NEW_REGIME_SLABS_2024_25: List[Tuple[float, float, float]] = [
    (0.0, 300000.0, 0.0),
    (300000.0, 700000.0, 0.05),
    (700000.0, 1000000.0, 0.10),
    (1000000.0, 1200000.0, 0.15),
    (1200000.0, 1500000.0, 0.20),
    (1500000.0, float('inf'), 0.30)
]

# FY 2025-26 Parameters (Finance Act 2025)
STD_DEDUCTION_OLD_2025_26 = 50000.0
STD_DEDUCTION_NEW_2025_26 = 75000.0

NEW_REGIME_REBATE_87A_LIMIT_2025_26 = 1200000.0  # Budget 2025 zero tax up to 12L
NEW_REGIME_REBATE_87A_MAX_2025_26 = 60000.0

# New Regime Slabs FY 2025-26 (Budget 2025)
NEW_REGIME_SLABS_2025_26: List[Tuple[float, float, float]] = [
    (0.0, 400000.0, 0.0),
    (400000.0, 800000.0, 0.05),
    (800000.0, 1200000.0, 0.10),
    (1200000.0, 1600000.0, 0.15),
    (1600000.0, 2000000.0, 0.20),
    (2000000.0, 2400000.0, 0.25),
    (2400000.0, float('inf'), 0.30)
]

# Surcharge thresholds & rates (Old & New Regimes)
# Note: For New Regime, max surcharge is capped at 25% (37% rate eliminated)
SURCHARGE_TIERS_OLD = [
    (5000000.0, 10000000.0, 0.10),
    (10000000.0, 20000000.0, 0.15),
    (20000000.0, 50000000.0, 0.25),
    (50000000.0, float('inf'), 0.37)
]

SURCHARGE_TIERS_NEW = [
    (5000000.0, 10000000.0, 0.10),
    (10000000.0, 20000000.0, 0.15),
    (20000000.0, float('inf'), 0.25)
]
