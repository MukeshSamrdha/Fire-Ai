"""
Test Case Generator for Indian Income Tax Engine (Project A).
Generates at least 200 edge cases covering every statutory threshold:
- Below taxable limits (2.5L, 3L)
- Rebate 87A cliffs (Old: 5L vs 5.0001L; New: 7L, 7.05L, 7.15L, 7.27L marginal relief)
- Slab boundaries (10L, 12L, 15L)
- Surcharge thresholds (50L, 1Cr, 2Cr, 5Cr) with marginal relief
- HRA metro vs non-metro and rent < 10% salary
- Age brackets: general (<60), senior (60-79), super senior (80+)
- Deduction clamping: 80C, 80CCD(1B), 80D, 24(b)
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from project_a.test_suite.official_calculator_cases import OFFICIAL_CALCULATOR_CASES
from project_a.implementations.hand_coded import HandCodedTaxEngine
from project_a.models import SalaryInput

def generate_all_test_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    
    # 1. Include the 30 Official Calculator Verified Cases
    cases.extend(OFFICIAL_CALCULATOR_CASES)

    engine_2024 = HandCodedTaxEngine(financial_year="2024-25")
    case_counter = len(cases) + 1

    # 2. Threshold Edge Cases around Standard Deduction & Basic Exemption
    salaries_low = [
        100000, 200000, 250000, 250010, 260000, 300000, 300010, 350000,
        375000, 400000, 450000, 490000, 499990, 500000, 500010, 510000,
        525000, 550000, 575000, 600000, 650000, 690000, 699990, 700000,
        700010, 705000, 710000, 715000, 720000, 725000, 727770, 728000,
        730000, 750000, 775000, 775010, 780000, 790000, 800000
    ]

    for sal in salaries_low:
        inp = SalaryInput(gross_salary=float(sal), basic_salary=float(sal*0.5), age=30)
        res = engine_2024.compare_regimes(inp)
        cases.append({
            "id": f"GEN_LOW_{case_counter:03d}",
            "description": f"Threshold test at gross salary ₹{sal:,.0f} (Age 30, no deductions)",
            "input": inp.model_dump(),
            "expected_old_tax": res.old_regime.total_tax,
            "expected_new_tax": res.new_regime.total_tax,
            "recommended": res.recommended_regime,
            "notes": f"Old taxable: ₹{res.old_regime.taxable_income:,.0f}, New taxable: ₹{res.new_regime.taxable_income:,.0f}"
        })
        case_counter += 1

    # 3. Slab Transition Points: 8L to 15L with varying deductions
    salaries_mid = [
        850000, 900000, 950000, 1000000, 1050000, 1100000, 1150000, 1200000,
        1250000, 1300000, 1350000, 1400000, 1450000, 1500000, 1550000, 1600000,
        1700000, 1800000, 1900000, 2000000
    ]

    deduction_combos = [
        # (80c, 80ccd, 80d_self, 80d_par, hl_int, rent_pct, is_metro)
        (0, 0, 0, 0, 0, 0, False),                               # Nil deductions
        (150000, 0, 0, 0, 0, 0, False),                          # 80C only
        (150000, 50000, 25000, 0, 0, 0, False),                  # 80C + NPS + 80D
        (150000, 50000, 25000, 50000, 200000, 0.25, True),      # Max deductions + Metro HRA
        (150000, 0, 0, 0, 200000, 0, False),                     # 80C + Home loan
        (100000, 25000, 15000, 20000, 100000, 0.20, False)      # Moderate partial deductions
    ]

    for sal in salaries_mid:
        for combo in deduction_combos:
            c, ccd, ds, dp, hl, rent_pct, metro = combo
            basic = sal * 0.50
            hra_rec = sal * 0.20 if rent_pct > 0 else 0.0
            rent = sal * rent_pct
            inp = SalaryInput(
                gross_salary=float(sal),
                basic_salary=float(basic),
                hra_received=float(hra_rec),
                rent_paid=float(rent),
                is_metro=metro,
                sec_80c=float(c),
                sec_80ccd_1b=float(ccd),
                sec_80d_self=float(ds),
                sec_80d_parents=float(dp),
                parents_senior_citizen=(dp > 25000),
                home_loan_interest=float(hl),
                age=35
            )
            res = engine_2024.compare_regimes(inp)
            cases.append({
                "id": f"GEN_MID_{case_counter:03d}",
                "description": f"Mid-tier salary ₹{sal:,.0f} with deds (80C={c}, NPS={ccd}, Metro={metro})",
                "input": inp.model_dump(),
                "expected_old_tax": res.old_regime.total_tax,
                "expected_new_tax": res.new_regime.total_tax,
                "recommended": res.recommended_regime,
                "notes": f"Old tax: ₹{res.old_regime.total_tax:,.0f}, New tax: ₹{res.new_regime.total_tax:,.0f}"
            })
            case_counter += 1

    # 4. Surcharge Edge Cases & High Earners (50L, 1Cr, 2Cr, 5Cr, 10Cr)
    surch_salaries = [
        4800000, 4900000, 4999900, 5000000, 5000100, 5050000, 5100000, 5200000,
        5500000, 6000000, 7500000, 9500000, 9999900, 10000000, 10000100, 10100000,
        10500000, 12000000, 15000000, 19999900, 20000000, 20000100, 20500000,
        25000000, 49999900, 50000000, 50000100, 51000000, 60000000, 100000000
    ]

    for sal in surch_salaries:
        inp = SalaryInput(gross_salary=float(sal), basic_salary=float(sal*0.5), sec_80c=150000.0, age=45)
        res = engine_2024.compare_regimes(inp)
        cases.append({
            "id": f"GEN_SURCH_{case_counter:03d}",
            "description": f"Surcharge test case at ₹{sal:,.0f} (Marginal relief check)",
            "input": inp.model_dump(),
            "expected_old_tax": res.old_regime.total_tax,
            "expected_new_tax": res.new_regime.total_tax,
            "recommended": res.recommended_regime,
            "notes": f"Old surcharge: ₹{res.old_regime.surcharge:,.0f}, New surcharge: ₹{res.new_regime.surcharge:,.0f}"
        })
        case_counter += 1

    # 5. Senior and Super Senior Citizens
    senior_salaries = [400000, 500000, 600000, 800000, 1000000, 1200000, 1500000, 2000000]
    for sal in senior_salaries:
        # Age 65: Senior
        inp_65 = SalaryInput(gross_salary=float(sal), basic_salary=float(sal*0.5), age=65, sec_80d_self=50000.0, self_senior_citizen=True)
        res_65 = engine_2024.compare_regimes(inp_65)
        cases.append({
            "id": f"GEN_SENIOR_{case_counter:03d}",
            "description": f"Senior citizen (Age 65) salary ₹{sal:,.0f}",
            "input": inp_65.model_dump(),
            "expected_old_tax": res_65.old_regime.total_tax,
            "expected_new_tax": res_65.new_regime.total_tax,
            "recommended": res_65.recommended_regime,
            "notes": "Senior basic exemption ₹3,00,000 under old regime."
        })
        case_counter += 1

        # Age 83: Super Senior
        inp_83 = SalaryInput(gross_salary=float(sal), basic_salary=float(sal*0.5), age=83, sec_80d_self=50000.0, self_senior_citizen=True)
        res_83 = engine_2024.compare_regimes(inp_83)
        cases.append({
            "id": f"GEN_SUPERSENIOR_{case_counter:03d}",
            "description": f"Super Senior citizen (Age 83) salary ₹{sal:,.0f}",
            "input": inp_83.model_dump(),
            "expected_old_tax": res_83.old_regime.total_tax,
            "expected_new_tax": res_83.new_regime.total_tax,
            "recommended": res_83.recommended_regime,
            "notes": "Super Senior basic exemption ₹5,00,000 under old regime."
        })
        case_counter += 1

    return cases

if __name__ == "__main__":
    all_cases = generate_all_test_cases()
    output_path = Path(__file__).parent / "test_cases_200.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_cases, f, indent=2)
    print(f"Generated {len(all_cases)} test cases successfully saved to {output_path}.")
