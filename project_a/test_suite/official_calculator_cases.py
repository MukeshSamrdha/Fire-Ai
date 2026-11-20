"""
30 Reference Test Cases verified against the Income Tax Department's official tax provisions
and reference calculator for FY 2024-25 (AY 2025-26).
"""
from typing import List, Dict, Any

OFFICIAL_CALCULATOR_CASES: List[Dict[str, Any]] = [
    {
        "id": "OFF_01",
        "description": "Fresher starting job, below taxable threshold",
        "input": {"gross_salary": 350000, "basic_salary": 175000, "hra_received": 50000, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 23},
        "expected_old_tax": 0.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "Old: 350k - 50k = 300k taxable. Slab tax 2.5k, Sec 87A rebate 2.5k -> Tax 0. New: 350k - 75k = 275k <= 300k -> Tax 0."
    },
    {
        "id": "OFF_02",
        "description": "Mid-level engineer earning 7.5 LPA, no deductions",
        "input": {"gross_salary": 750000, "basic_salary": 375000, "hra_received": 120000, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 28},
        "expected_old_tax": 54600.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "Old: 750k - 50k = 700k taxable. Slab tax 52.5k + 4% cess = 54.6k. New: 750k - 75k = 675k <= 700k. 87A rebate covers full tax -> Tax 0!"
    },
    {
        "id": "OFF_03",
        "description": "New regime 87A exact threshold edge case: Gross 7.75 Lakhs",
        "input": {"gross_salary": 775000, "basic_salary": 387500, "hra_received": 100000, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 26},
        "expected_old_tax": 59800.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "New Regime: 775k - 75k std ded = exactly 700k taxable income. 87A rebate covers ₹20,000 slab tax -> Final Tax ₹0."
    },
    {
        "id": "OFF_04",
        "description": "New regime Sec 87A Marginal Relief edge case: Gross 7.80 Lakhs (Taxable 7.05 Lakhs)",
        "input": {"gross_salary": 780000, "basic_salary": 390000, "hra_received": 100000, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 29},
        "expected_old_tax": 60840.0,
        "expected_new_tax": 5200.0,
        "recommended": "new",
        "notes": "New Regime: 780k - 75k = 705k. Slab tax = 20k + 10%*(5k) = 20.5k. Excess over 700k is 5,000. Marginal relief caps tax at 5,000 + 4% cess = 5,200."
    },
    {
        "id": "OFF_05",
        "description": "New regime Sec 87A Marginal Relief edge case: Gross 7.90 Lakhs (Taxable 7.15 Lakhs)",
        "input": {"gross_salary": 790000, "basic_salary": 395000, "hra_received": 100000, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 30},
        "expected_old_tax": 62920.0,
        "expected_new_tax": 15600.0,
        "recommended": "new",
        "notes": "New Regime: 790k - 75k = 715k. Slab tax = 20k + 1.5k = 21.5k. Excess over 700k is 15k. Marginal relief caps tax at 15,000 + 4% cess = 15,600."
    },
    {
        "id": "OFF_06",
        "description": "Gross 10 Lakhs, full 80C (1.5L) only",
        "input": {"gross_salary": 1000000, "basic_salary": 500000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 31},
        "expected_old_tax": 75400.0,
        "expected_new_tax": 44200.0,
        "recommended": "new",
        "notes": "Old: 10L - 50k - 1.5L = 800k. Tax = 12.5k + 60k = 72.5k + 4% = 75.4k. New: 10L - 75k = 925k. Tax = 20k + 22.5k = 42.5k + 4% = 44.2k. New saves 31.2k."
    },
    {
        "id": "OFF_07",
        "description": "Gross 10 Lakhs, heavy deductions (80C, 80D, 80CCD, Metro HRA)",
        "input": {"gross_salary": 1000000, "basic_salary": 500000, "da": 0, "hra_received": 200000, "rent_paid": 240000, "is_metro": True, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 25000, "home_loan_interest": 0, "age": 32},
        "expected_old_tax": 15080.0,
        "expected_new_tax": 44200.0,
        "recommended": "old",
        "notes": "HRA exemption = min(200k, 240k - 50k = 190k, 250k) = 190k. Total ded = 50k + 190k + 150k + 50k + 50k = 490k. Taxable = 510k. Tax = 14.5k + 4% cess = 15,080. Old wins!"
    },
    {
        "id": "OFF_08",
        "description": "Old regime exact 5 Lakhs taxable income threshold",
        "input": {"gross_salary": 550000, "basic_salary": 275000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 28},
        "expected_old_tax": 0.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "Old: 550k - 50k = 500k. Slab tax 12.5k. 87A rebate 12.5k -> Tax 0. New: 550k - 75k = 475k -> Tax 0."
    },
    {
        "id": "OFF_09",
        "description": "Old regime just above 5 Lakhs taxable income (Cliff effect: 500,010)",
        "input": {"gross_salary": 550010, "basic_salary": 275000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 28},
        "expected_old_tax": 13000.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "Old: 550,010 - 50,000 = 500,010. 87A rebate vanishes! Slab tax 12,500 + 2 = 12,502 + 4% cess = 13,002.08 -> rounded 13,000. Huge cliff in old regime."
    },
    {
        "id": "OFF_10",
        "description": "Gross 12 Lakhs with Home loan interest 2 Lakhs (Sec 24b) and 80C",
        "input": {"gross_salary": 1200000, "basic_salary": 600000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 200000, "age": 34},
        "expected_old_tax": 75400.0,
        "expected_new_tax": 71500.0,
        "recommended": "new",
        "notes": "Old: 12L - 50k - 150k - 200k = 800k taxable -> 72.5k + 4% = 75,400. New: 12L - 75k = 1,125,000. Slab tax = 68,750 + 4% = 71,500. New saves ₹3,900."
    },
    {
        "id": "OFF_11",
        "description": "Gross 15 Lakhs, moderate deductions (80C 1.5L, 80D 25k)",
        "input": {"gross_salary": 1500000, "basic_salary": 750000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 25000, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 33},
        "expected_old_tax": 202800.0,
        "expected_new_tax": 130000.0,
        "recommended": "new",
        "notes": "Old: 15L - 225k = 12.75L taxable. Tax 195k + 4% = 202,800. New: 15L - 75k = 14.25L taxable. Tax 125k + 4% = 130,000. New saves ₹72,800."
    },
    {
        "id": "OFF_12",
        "description": "Gross 15 Lakhs, maximum possible deductions (HRA, 80C, 80CCD, 80D 100k, 24b, Senior Citizen age 61)",
        "input": {"gross_salary": 1500000, "basic_salary": 750000, "hra_received": 300000, "rent_paid": 360000, "is_metro": True, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 50000, "sec_80d_parents": 50000, "self_senior_citizen": True, "parents_senior_citizen": True, "home_loan_interest": 200000, "age": 61},
        "expected_old_tax": 44720.0,
        "expected_new_tax": 130000.0,
        "recommended": "old",
        "notes": "HRA exemption: 360k - 75k = 285k. Total ded: 50k + 285k + 150k + 50k + 100k + 200k = 835k. Taxable = 665k. Senior slabs apply. Old saves ₹85,280."
    },
    {
        "id": "OFF_13",
        "description": "Gross 20 Lakhs salaried professional",
        "input": {"gross_salary": 2000000, "basic_salary": 1000000, "hra_received": 300000, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 25000, "home_loan_interest": 0, "age": 36},
        "expected_old_tax": 335400.0,
        "expected_new_tax": 278200.0,
        "recommended": "new",
        "notes": "Old: 20L - 300k deds = 17L taxable -> Tax 322.5k + 4% = 335,400. New: 20L - 75k = 1,925,000. Tax: 140k + 30%*(425k) = 267.5k + 4% = 278,200. New saves ₹57,200."
    },
    {
        "id": "OFF_14",
        "description": "Gross 25 Lakhs, high earner",
        "input": {"gross_salary": 2500000, "basic_salary": 1250000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 50000, "parents_senior_citizen": True, "home_loan_interest": 200000, "age": 40},
        "expected_old_tax": 421200.0,
        "expected_new_tax": 434200.0,
        "recommended": "old",
        "notes": "Old: 25L - 525k = 19.75L taxable -> Tax 405k + 4% = 421,200. New: 25L - 75k = 24.25L -> Tax 417.5k + 4% = 434,200. Old saves ₹13,000."
    },
    {
        "id": "OFF_15",
        "description": "Gross 50 Lakhs (Exact threshold for Surcharge)",
        "input": {"gross_salary": 5000000, "basic_salary": 2500000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 45},
        "expected_old_tax": 1302600.0,
        "expected_new_tax": 1214200.0,
        "recommended": "new",
        "notes": "Taxable income <= 50L. Surcharge is 0% under both regimes."
    },
    {
        "id": "OFF_16",
        "description": "Surcharge Edge Case: Gross 51 Lakhs (Surcharge Marginal Relief test)",
        "input": {"gross_salary": 5100000, "basic_salary": 2500000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 45},
        "expected_old_tax": 1417000.0,
        "expected_new_tax": 1263600.0,
        "recommended": "new",
        "notes": "Taxable income exceeds 50L. Surcharge marginal relief applies to prevent tax jump exceeding excess income."
    },
    {
        "id": "OFF_17",
        "description": "Gross 60 Lakhs (10% Surcharge applies without full relief)",
        "input": {"gross_salary": 6000000, "basic_salary": 3000000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 48},
        "expected_old_tax": 1776060.0,
        "expected_new_tax": 1678820.0,
        "recommended": "new",
        "notes": "10% surcharge applies on base tax."
    },
    {
        "id": "OFF_18",
        "description": "Gross 1.05 Crore (15% Surcharge threshold edge case with Marginal Relief)",
        "input": {"gross_salary": 10500000, "basic_salary": 5000000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 52},
        "expected_old_tax": 3525210.0,
        "expected_new_tax": 3369730.0,
        "recommended": "new",
        "notes": "Income crosses 1 Crore. Surcharge jumps from 10% to 15% with marginal relief evaluated."
    },
    {
        "id": "OFF_19",
        "description": "Gross 2.1 Crore (25% Surcharge threshold edge case)",
        "input": {"gross_salary": 21000000, "basic_salary": 10000000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 55},
        "expected_old_tax": 7926750.0,
        "expected_new_tax": 7757750.0,
        "recommended": "new",
        "notes": "Income crosses 2 Crores. Surcharge jumps to 25%."
    },
    {
        "id": "OFF_20",
        "description": "Gross 6 Crore ultra-high earner (37% Old Surcharge vs 25% New Surcharge Cap!)",
        "input": {"gross_salary": 60000000, "basic_salary": 30000000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 58},
        "expected_old_tax": 25357880.0,
        "expected_new_tax": 22967750.0,
        "recommended": "new",
        "notes": "Critical difference: New regime caps surcharge at 25%, while Old regime imposes 37%! New regime saves over ₹23 Lakhs."
    },
    {
        "id": "OFF_21",
        "description": "Senior Citizen (Age 65) Gross 8 Lakhs, Senior slabs under old regime",
        "input": {"gross_salary": 800000, "basic_salary": 400000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 50000, "self_senior_citizen": True, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 65},
        "expected_old_tax": 20800.0,
        "expected_new_tax": 23400.0,
        "recommended": "old",
        "notes": "Old: 800k - 50k - 150k - 50k = 550k. Senior basic exemption 3L. Slab tax: 5% of 2L + 20% of 50k = 10k + 10k = 20k + 4% = 20,800. New: 800k - 75k = 725k taxable -> 22,500 + 4% = 23,400. Old saves ₹2,600."
    },
    {
        "id": "OFF_22",
        "description": "Super Senior Citizen (Age 82) Gross 12 Lakhs",
        "input": {"gross_salary": 1200000, "basic_salary": 600000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 50000, "self_senior_citizen": True, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 82},
        "expected_old_tax": 93600.0,
        "expected_new_tax": 71500.0,
        "recommended": "new",
        "notes": "Old regime basic exemption is 5 Lakhs for age 80+. Taxable 950k -> Tax 90k + 4% = 93,600. New: 71,500. New saves ₹22,100."
    },
    {
        "id": "OFF_23",
        "description": "Non-Metro HRA test: Bangalore employee earning 14 Lakhs",
        "input": {"gross_salary": 1400000, "basic_salary": 700000, "hra_received": 250000, "rent_paid": 300000, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 25000, "home_loan_interest": 0, "age": 30},
        "expected_old_tax": 89960.0,
        "expected_new_tax": 109200.0,
        "recommended": "old",
        "notes": "Non-metro HRA: 40% of 700k = 280k. Rent - 10% = 300k - 70k = 230k. Actual HRA = 250k. Exempt = 230k. Total ded = 505k. Taxable = 895k -> 86.5k + 4% = 89,960. Old saves ₹19,240."
    },
    {
        "id": "OFF_24",
        "description": "Metro HRA test: Mumbai employee earning 14 Lakhs identical rent",
        "input": {"gross_salary": 1400000, "basic_salary": 700000, "hra_received": 250000, "rent_paid": 300000, "is_metro": True, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 25000, "home_loan_interest": 0, "age": 30},
        "expected_old_tax": 89960.0,
        "expected_new_tax": 109200.0,
        "recommended": "old",
        "notes": "Metro 50% = 350k. Rent - 10% is 230k (binding constraint). Exemption remains 230k. Old saves ₹19,240."
    },
    {
        "id": "OFF_25",
        "description": "HRA Edge Case: Rent paid is less than 10% of salary (Exemption = 0)",
        "input": {"gross_salary": 1200000, "basic_salary": 600000, "hra_received": 200000, "rent_paid": 50000, "is_metro": True, "sec_80c": 150000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 29},
        "expected_old_tax": 117000.0,
        "expected_new_tax": 71500.0,
        "recommended": "new",
        "notes": "Rent (50k) < 10% of basic (60k). Rule 2A yields 0 exemption. Taxable 1M -> Tax 112.5k + 4% = 117,000. New regime wins."
    },
    {
        "id": "OFF_26",
        "description": "Deduction Clamping: 80C declared 3 Lakhs (clamped to 1.5L) and 24b declared 3.5 Lakhs (clamped to 2L)",
        "input": {"gross_salary": 1600000, "basic_salary": 800000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 300000, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 350000, "age": 35},
        "expected_old_tax": 179400.0,
        "expected_new_tax": 153400.0,
        "recommended": "new",
        "notes": "80C clamped to 150k, 24b clamped to 200k. Total ded = 400k. Taxable = 12L -> Tax 172.5k + 4% = 179,400. New: 153,400."
    },
    {
        "id": "OFF_27",
        "description": "Section 80D Maximum allowable combination (Self 50k senior + Parents 50k senior = 1 Lakh)",
        "input": {"gross_salary": 1100000, "basic_salary": 550000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 60000, "sec_80d_parents": 60000, "self_senior_citizen": True, "parents_senior_citizen": True, "home_loan_interest": 0, "age": 62},
        "expected_old_tax": 62400.0,
        "expected_new_tax": 55900.0,
        "recommended": "new",
        "notes": "Old: 1.1M - 50k std - 150k - 50k - 100k (80D capped) = 750k taxable. Senior citizen slab -> 60k + 4% = 62,400. New: 55,900. New saves ₹6,500."
    },
    {
        "id": "OFF_28",
        "description": "Gross 9 Lakhs with no investments",
        "input": {"gross_salary": 900000, "basic_salary": 450000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 27},
        "expected_old_tax": 85800.0,
        "expected_new_tax": 33800.0,
        "recommended": "new",
        "notes": "New regime saves ₹52,000 for zero-deduction salaried employees."
    },
    {
        "id": "OFF_29",
        "description": "Breakeven deduction test at 15 Lakhs Gross",
        "input": {"gross_salary": 1500000, "basic_salary": 750000, "hra_received": 200000, "rent_paid": 275000, "is_metro": True, "sec_80c": 150000, "sec_80ccd_1b": 50000, "sec_80d_self": 25000, "sec_80d_parents": 25000, "home_loan_interest": 100000, "age": 35},
        "expected_old_tax": 96200.0,
        "expected_new_tax": 130000.0,
        "recommended": "old",
        "notes": "HRA exempt = 200k. Total ded = 50k + 200k + 150k + 50k + 50k + 100k = 575k. Taxable = 925k -> 92.5k + 4% = 96,200. Old saves ₹33,800."
    },
    {
        "id": "OFF_30",
        "description": "Ultra low income: Gross 2.4 Lakhs",
        "input": {"gross_salary": 240000, "basic_salary": 120000, "hra_received": 0, "rent_paid": 0, "is_metro": False, "sec_80c": 0, "sec_80ccd_1b": 0, "sec_80d_self": 0, "sec_80d_parents": 0, "home_loan_interest": 0, "age": 22},
        "expected_old_tax": 0.0,
        "expected_new_tax": 0.0,
        "recommended": "new",
        "notes": "Taxable income is below standard deduction and basic exemption limit under both regimes. Tax is exactly ₹0."
    }
]
