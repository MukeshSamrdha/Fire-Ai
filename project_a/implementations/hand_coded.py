"""
Implementation 2a: Hand-coded Deterministic Rules Engine for Indian Income Tax.
Includes exact statutory clause citations for full rupee-level auditability.
Compliant with Section 16(ia), 10(13A), Rule 2A, 80C, 80CCD(1B), 80D, 24(b), 115BAC, 87A, 288A, 288B.
"""
from typing import Tuple, List
import math
from project_a.models import SalaryInput, TaxBreakdown, RegimeComparison
from project_a.config import (
    SEC_80C_MAX, SEC_80CCD_1B_MAX, SEC_80D_NORMAL_MAX, SEC_80D_SENIOR_MAX,
    SEC_24B_MAX, CESS_RATE,
    STD_DEDUCTION_OLD_2024_25, STD_DEDUCTION_NEW_2024_25,
    STD_DEDUCTION_OLD_2025_26, STD_DEDUCTION_NEW_2025_26,
    OLD_REGIME_REBATE_87A_LIMIT, OLD_REGIME_REBATE_87A_MAX,
    NEW_REGIME_REBATE_87A_LIMIT_2024_25, NEW_REGIME_REBATE_87A_MAX_2024_25,
    NEW_REGIME_REBATE_87A_LIMIT_2025_26, NEW_REGIME_REBATE_87A_MAX_2025_26,
    OLD_REGIME_SLABS_GENERAL, OLD_REGIME_SLABS_SENIOR, OLD_REGIME_SLABS_SUPER_SENIOR,
    NEW_REGIME_SLABS_2024_25, NEW_REGIME_SLABS_2025_26,
    SURCHARGE_TIERS_OLD, SURCHARGE_TIERS_NEW
)

def round_it_section(amount: float) -> float:
    """Round to nearest 10 rupees per Section 288A (taxable income) and 288B (tax payable)."""
    return float(round(amount / 10.0) * 10)

class HandCodedTaxEngine:
    """Deterministic hand-coded tax calculator implementing Indian income tax law."""
    
    def __init__(self, financial_year: str = "2024-25"):
        self.fy = financial_year

    def compute_hra_exemption(self, salary_input: SalaryInput) -> Tuple[float, List[str]]:
        """
        Compute HRA exemption under Section 10(13A) read with Rule 2A.
        Least of:
        1. Actual HRA received
        2. Rent paid - 10% of salary (Basic + DA)
        3. 50% of salary for metro, 40% for non-metro
        """
        audit = []
        if salary_input.rent_paid <= 0 or salary_input.hra_received <= 0:
            audit.append("Sec 10(13A) read with Rule 2A: No rent paid or no HRA received; exemption = ₹0")
            return 0.0, audit

        salary_for_hra = salary_input.basic_salary + salary_input.da
        if salary_for_hra <= 0:
            salary_for_hra = max(0.0, salary_input.gross_salary - salary_input.hra_received)

        c1 = salary_input.hra_received
        c2 = max(0.0, salary_input.rent_paid - (0.10 * salary_for_hra))
        pct = 0.50 if salary_input.is_metro else 0.40
        c3 = pct * salary_for_hra

        exemption = min(c1, c2, c3)
        audit.append(
            f"Sec 10(13A) read with Rule 2A: Min of [Actual HRA: ₹{c1:,.2f}, "
            f"Rent - 10% Salary: ₹{c2:,.2f}, {int(pct*100)}% Salary ({'Metro' if salary_input.is_metro else 'Non-Metro'}): ₹{c3:,.2f}] "
            f"= ₹{exemption:,.2f}"
        )
        return exemption, audit

    def compute_deductions_old_regime(self, inp: SalaryInput) -> Tuple[float, float, float, float, float, float, List[str]]:
        """Calculate deductions under Old Regime."""
        audit = []
        std_ded = STD_DEDUCTION_OLD_2024_25 if self.fy == "2024-25" else STD_DEDUCTION_OLD_2025_26
        std_ded = min(std_ded, inp.gross_salary)
        audit.append(f"Sec 16(ia): Standard deduction allowed = ₹{std_ded:,.2f}")

        hra_exemption, hra_audit = self.compute_hra_exemption(inp)
        audit.extend(hra_audit)

        sec_80c = min(inp.sec_80c, SEC_80C_MAX)
        audit.append(f"Sec 80C: Declared ₹{inp.sec_80c:,.2f}, Allowed capped at ₹{sec_80c:,.2f}")

        sec_80ccd = min(inp.sec_80ccd_1b, SEC_80CCD_1B_MAX)
        if inp.sec_80ccd_1b > 0:
            audit.append(f"Sec 80CCD(1B): NPS contribution ₹{inp.sec_80ccd_1b:,.2f}, Allowed capped at ₹{sec_80ccd:,.2f}")

        # Sec 80D
        limit_self = SEC_80D_SENIOR_MAX if (inp.self_senior_citizen or inp.age >= 60) else SEC_80D_NORMAL_MAX
        limit_parents = SEC_80D_SENIOR_MAX if inp.parents_senior_citizen else SEC_80D_NORMAL_MAX
        ded_self = min(inp.sec_80d_self, limit_self)
        ded_parents = min(inp.sec_80d_parents, limit_parents)
        sec_80d = ded_self + ded_parents
        audit.append(
            f"Sec 80D: Self/Family allowed ₹{ded_self:,.2f} (cap ₹{limit_self:,.2f}), "
            f"Parents allowed ₹{ded_parents:,.2f} (cap ₹{limit_parents:,.2f}), Total = ₹{sec_80d:,.2f}"
        )

        # Sec 24(b)
        sec_24b = min(inp.home_loan_interest, SEC_24B_MAX)
        if inp.home_loan_interest > 0:
            audit.append(f"Sec 24(b): Self-occupied home loan interest loss capped at ₹{sec_24b:,.2f}")

        total_ded = std_ded + hra_exemption + sec_80c + sec_80ccd + sec_80d + sec_24b
        return std_ded, hra_exemption, sec_80c, sec_80ccd, sec_80d, sec_24b, audit

    def _get_slabs(self, regime: str, age: int):
        if regime == "new":
            return NEW_REGIME_SLABS_2025_26 if self.fy == "2025-26" else NEW_REGIME_SLABS_2024_25
        else:
            if age >= 80:
                return OLD_REGIME_SLABS_SUPER_SENIOR
            elif age >= 60:
                return OLD_REGIME_SLABS_SENIOR
            else:
                return OLD_REGIME_SLABS_GENERAL

    def compute_slab_tax(self, taxable_income: float, regime: str, age: int) -> Tuple[float, List[str]]:
        """Compute base income tax according to progressive slab rates."""
        audit = []
        slabs = self._get_slabs(regime, age)
        total_tax = 0.0
        
        for lower, upper, rate in slabs:
            if taxable_income > lower:
                taxable_chunk = min(taxable_income, upper) - lower
                tax_chunk = taxable_chunk * rate
                total_tax += tax_chunk
                audit.append(
                    f"Slab ₹{lower:,.0f} to {('₹'+f'{upper:,.0f}') if upper != float('inf') else 'Above'}: "
                    f"₹{taxable_chunk:,.2f} @ {int(rate*100)}% = ₹{tax_chunk:,.2f}"
                )
            else:
                break
        return total_tax, audit

    def compute_surcharge_and_marginal_relief(
        self, taxable_income: float, base_tax: float, regime: str, age: int
    ) -> Tuple[float, float, List[str]]:
        """
        Compute surcharge and marginal relief.
        Marginal relief ensures tax + surcharge on (threshold + excess) does not exceed
        (tax on threshold) + excess income.
        """
        audit = []
        if taxable_income <= 5000000.0 or base_tax <= 0:
            return 0.0, 0.0, audit

        tiers = SURCHARGE_TIERS_NEW if regime == "new" else SURCHARGE_TIERS_OLD
        rate = 0.0
        threshold = 5000000.0

        for lower, upper, r in tiers:
            if taxable_income > lower:
                rate = r
                threshold = lower

        nominal_surcharge = base_tax * rate
        audit.append(f"Sec 110/111: Nominal surcharge at {int(rate*100)}% on ₹{base_tax:,.2f} = ₹{nominal_surcharge:,.2f}")

        # Check marginal relief
        tax_at_threshold, _ = self.compute_slab_tax(threshold, regime, age)
        # Surcharge on threshold if threshold > 50L
        surch_at_threshold = 0.0
        if threshold > 5000000.0:
            # find previous tier rate
            for l, u, r in tiers:
                if threshold > l and threshold <= u:
                    surch_at_threshold = tax_at_threshold * r
                    break

        excess_income = taxable_income - threshold
        max_total_liability = tax_at_threshold + surch_at_threshold + excess_income
        current_total_liability = base_tax + nominal_surcharge

        marginal_relief = 0.0
        if current_total_liability > max_total_liability:
            marginal_relief = current_total_liability - max_total_liability
            actual_surcharge = max(0.0, nominal_surcharge - marginal_relief)
            audit.append(
                f"Surcharge Marginal Relief: Total tax+surcharge (₹{current_total_liability:,.2f}) exceeded cap "
                f"(₹{max_total_liability:,.2f}) by ₹{marginal_relief:,.2f}. Surcharge reduced to ₹{actual_surcharge:,.2f}"
            )
            return actual_surcharge, marginal_relief, audit

        return nominal_surcharge, 0.0, audit

    def calculate_old_regime(self, inp: SalaryInput) -> TaxBreakdown:
        """Compute full tax liability under Old Regime."""
        audit = [f"--- Old Regime Calculation ({self.fy}) ---"]
        std_ded, hra_ex, sec_80c, sec_80ccd, sec_80d, sec_24b, ded_audit = self.compute_deductions_old_regime(inp)
        audit.extend(ded_audit)

        total_ded = std_ded + hra_ex + sec_80c + sec_80ccd + sec_80d + sec_24b
        net_taxable = max(0.0, inp.gross_salary - total_ded)
        taxable_income = round_it_section(net_taxable)
        audit.append(f"Sec 288A: Net Taxable Income rounded to nearest ₹10 = ₹{taxable_income:,.2f}")

        slab_tax, slab_audit = self.compute_slab_tax(taxable_income, "old", inp.age)
        audit.extend(slab_audit)

        # Sec 87A Rebate
        rebate_87a = 0.0
        if taxable_income <= OLD_REGIME_REBATE_87A_LIMIT:
            rebate_87a = min(slab_tax, OLD_REGIME_REBATE_87A_MAX)
            audit.append(f"Sec 87A Rebate: Full tax rebate of ₹{rebate_87a:,.2f} applied (Income <= ₹5,00,000)")
        else:
            audit.append(f"Sec 87A Rebate: ₹0 (Taxable income ₹{taxable_income:,.2f} exceeds ₹5,00,000)")

        tax_after_rebate = max(0.0, slab_tax - rebate_87a)

        surcharge, marg_relief, surch_audit = self.compute_surcharge_and_marginal_relief(
            taxable_income, tax_after_rebate, "old", inp.age
        )
        audit.extend(surch_audit)

        tax_plus_surcharge = tax_after_rebate + surcharge
        cess = tax_plus_surcharge * CESS_RATE
        audit.append(f"Finance Act: Health and Education Cess @ 4% on ₹{tax_plus_surcharge:,.2f} = ₹{cess:,.2f}")

        total_tax = round_it_section(tax_plus_surcharge + cess)
        audit.append(f"Sec 288B: Final Total Tax rounded to nearest ₹10 = ₹{total_tax:,.2f}")

        effective_rate = (total_tax / inp.gross_salary * 100.0) if inp.gross_salary > 0 else 0.0

        return TaxBreakdown(
            regime="old",
            financial_year=self.fy,
            gross_salary=inp.gross_salary,
            standard_deduction=std_ded,
            hra_exemption=hra_ex,
            sec_80c_deduction=sec_80c,
            sec_80ccd_1b_deduction=sec_80ccd,
            sec_80d_deduction=sec_80d,
            sec_24b_deduction=sec_24b,
            total_deductions=total_ded,
            taxable_income=taxable_income,
            slab_tax=slab_tax,
            sec_87a_rebate=rebate_87a,
            tax_after_rebate=tax_after_rebate,
            surcharge=surcharge,
            marginal_relief_surcharge=marg_relief,
            cess=cess,
            total_tax=total_tax,
            effective_tax_rate=round(effective_rate, 2),
            audit_trail=audit
        )

    def calculate_new_regime(self, inp: SalaryInput) -> TaxBreakdown:
        """Compute full tax liability under New Regime (Section 115BAC)."""
        audit = [f"--- New Regime Calculation ({self.fy}) ---"]
        if self.fy == "2024-25":
            std_ded = min(STD_DEDUCTION_NEW_2024_25, inp.gross_salary)
            rebate_limit = NEW_REGIME_REBATE_87A_LIMIT_2024_25
            rebate_max = NEW_REGIME_REBATE_87A_MAX_2024_25
        else:
            std_ded = min(STD_DEDUCTION_NEW_2025_26, inp.gross_salary)
            rebate_limit = NEW_REGIME_REBATE_87A_LIMIT_2025_26
            rebate_max = NEW_REGIME_REBATE_87A_MAX_2025_26

        audit.append(f"Sec 16(ia) read with Sec 115BAC: Standard deduction allowed = ₹{std_ded:,.2f}")
        audit.append("Sec 115BAC: Chapter VI-A deductions (80C, 80D, 80CCD(1B)), HRA and 24(b) are NOT allowable")

        net_taxable = max(0.0, inp.gross_salary - std_ded)
        taxable_income = round_it_section(net_taxable)
        audit.append(f"Sec 288A: Net Taxable Income rounded to nearest ₹10 = ₹{taxable_income:,.2f}")

        slab_tax, slab_audit = self.compute_slab_tax(taxable_income, "new", inp.age)
        audit.extend(slab_audit)

        # Section 87A Rebate with Marginal Relief
        rebate_87a = 0.0
        if taxable_income <= rebate_limit:
            rebate_87a = min(slab_tax, rebate_max)
            audit.append(f"Sec 87A Rebate: Full rebate ₹{rebate_87a:,.2f} (Income <= ₹{rebate_limit:,.0f}); tax becomes ₹0")
        else:
            # Check Marginal Relief under Section 87A Proviso
            excess_income = taxable_income - rebate_limit
            if slab_tax > excess_income:
                rebate_87a = slab_tax - excess_income
                audit.append(
                    f"Sec 87A Marginal Relief: Slab tax (₹{slab_tax:,.2f}) > excess income over ₹{rebate_limit:,.0f} "
                    f"(₹{excess_income:,.2f}). Rebate ₹{rebate_87a:,.2f} applied; net tax capped at ₹{excess_income:,.2f}"
                )
            else:
                audit.append(f"Sec 87A Rebate: ₹0 (Taxable income ₹{taxable_income:,.2f} exceeds rebate threshold)")

        tax_after_rebate = max(0.0, slab_tax - rebate_87a)

        surcharge, marg_relief, surch_audit = self.compute_surcharge_and_marginal_relief(
            taxable_income, tax_after_rebate, "new", inp.age
        )
        audit.extend(surch_audit)

        tax_plus_surcharge = tax_after_rebate + surcharge
        cess = tax_plus_surcharge * CESS_RATE
        audit.append(f"Finance Act: Health and Education Cess @ 4% on ₹{tax_plus_surcharge:,.2f} = ₹{cess:,.2f}")

        total_tax = round_it_section(tax_plus_surcharge + cess)
        audit.append(f"Sec 288B: Final Total Tax rounded to nearest ₹10 = ₹{total_tax:,.2f}")

        effective_rate = (total_tax / inp.gross_salary * 100.0) if inp.gross_salary > 0 else 0.0

        return TaxBreakdown(
            regime="new",
            financial_year=self.fy,
            gross_salary=inp.gross_salary,
            standard_deduction=std_ded,
            hra_exemption=0.0,
            sec_80c_deduction=0.0,
            sec_80ccd_1b_deduction=0.0,
            sec_80d_deduction=0.0,
            sec_24b_deduction=0.0,
            total_deductions=std_ded,
            taxable_income=taxable_income,
            slab_tax=slab_tax,
            sec_87a_rebate=rebate_87a,
            tax_after_rebate=tax_after_rebate,
            surcharge=surcharge,
            marginal_relief_surcharge=marg_relief,
            cess=cess,
            total_tax=total_tax,
            effective_tax_rate=round(effective_rate, 2),
            audit_trail=audit
        )

    def compare_regimes(self, inp: SalaryInput) -> RegimeComparison:
        """Compare Old and New regimes and provide actionable recommendation."""
        old_res = self.calculate_old_regime(inp)
        new_res = self.calculate_new_regime(inp)

        if old_res.total_tax < new_res.total_tax:
            recommended = "old"
            savings = new_res.total_tax - old_res.total_tax
            explanation = (
                f"Old Regime saves ₹{savings:,.2f} due to significant deductions "
                f"(₹{old_res.total_deductions:,.2f} total: HRA ₹{old_res.hra_exemption:,.2f}, "
                f"80C ₹{old_res.sec_80c_deduction:,.2f}, 80D ₹{old_res.sec_80d_deduction:,.2f}, "
                f"24(b) ₹{old_res.sec_24b_deduction:,.2f})."
            )
        elif new_res.total_tax < old_res.total_tax:
            recommended = "new"
            savings = old_res.total_tax - new_res.total_tax
            explanation = (
                f"New Regime saves ₹{savings:,.2f} due to lower tax slab rates and higher "
                f"standard deduction (₹{new_res.standard_deduction:,.2f}) despite not claiming deductions."
            )
        else:
            recommended = "new"  # Default regime under 115BAC(1A)
            savings = 0.0
            explanation = "Tax is identical under both regimes. New Regime is recommended as the default regime."

        return RegimeComparison(
            old_regime=old_res,
            new_regime=new_res,
            recommended_regime=recommended,
            tax_savings=savings,
            explanation=explanation
        )
