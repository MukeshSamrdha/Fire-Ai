"""
Implementation 2c: LLM-compiled Rules Engine.
Loads the rule specification compiled by the LLM (and reviewed by engineers)
and executes deterministically at runtime with zero LLM API latency or cost.
"""
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
from project_a.models import SalaryInput, TaxBreakdown, RegimeComparison

def round_it_section(amount: float) -> float:
    return float(round(amount / 10.0) * 10)

class LLMCompiledTaxEngine:
    """Deterministic runtime engine that executes LLM-compiled rule specifications."""

    def __init__(self, rule_spec_path: str = None, financial_year: str = "2024-25"):
        self.fy = financial_year
        if rule_spec_path is None:
            base_dir = Path(__file__).parent.parent
            filename = f"compiled_rules_{financial_year.replace('-', '_')}.json"
            rule_spec_path = str(base_dir / filename)
        
        with open(rule_spec_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def compute_hra_exemption(self, salary_input: SalaryInput) -> Tuple[float, List[str]]:
        audit = []
        if salary_input.rent_paid <= 0 or salary_input.hra_received <= 0:
            audit.append("Sec 10(13A) [Compiled]: No rent paid or no HRA received; exemption = ₹0")
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
            f"Sec 10(13A) [Compiled]: Min of [Actual HRA: ₹{c1:,.2f}, "
            f"Rent - 10% Salary: ₹{c2:,.2f}, {int(pct*100)}% Salary ({'Metro' if salary_input.is_metro else 'Non-Metro'}): ₹{c3:,.2f}] "
            f"= ₹{exemption:,.2f}"
        )
        return exemption, audit

    def _get_old_slabs(self, age: int):
        if age >= 80:
            return self.rules.get("old_regime_slabs_super_senior", self.rules.get("old_regime_slabs"))
        elif age >= 60:
            return self.rules.get("old_regime_slabs_senior", self.rules.get("old_regime_slabs"))
        else:
            return self.rules.get("old_regime_slabs_general", self.rules.get("old_regime_slabs"))

    def _compute_slab_tax(self, taxable_income: float, slabs: List[List[Any]]) -> Tuple[float, List[str]]:
        audit = []
        total_tax = 0.0
        for item in slabs:
            lower = float(item[0])
            upper = float(item[1]) if item[1] is not None else float('inf')
            rate = float(item[2])

            if taxable_income > lower:
                taxable_chunk = min(taxable_income, upper) - lower
                tax_chunk = taxable_chunk * rate
                total_tax += tax_chunk
                audit.append(
                    f"Compiled Slab ₹{lower:,.0f} - {('₹'+f'{upper:,.0f}') if upper != float('inf') else 'Above'}: "
                    f"₹{taxable_chunk:,.2f} @ {int(rate*100)}% = ₹{tax_chunk:,.2f}"
                )
            else:
                break
        return total_tax, audit

    def _compute_surcharge(self, taxable_income: float, base_tax: float, tiers: List[List[Any]], slabs: List[List[Any]]) -> Tuple[float, float, List[str]]:
        audit = []
        if taxable_income <= 5000000.0 or base_tax <= 0:
            return 0.0, 0.0, audit

        rate = 0.0
        threshold = 5000000.0
        for item in tiers:
            lower = float(item[0])
            upper = float(item[1]) if item[1] is not None else float('inf')
            r = float(item[2])
            if taxable_income > lower:
                rate = r
                threshold = lower

        nominal_surcharge = base_tax * rate
        tax_at_threshold, _ = self._compute_slab_tax(threshold, slabs)
        
        surch_at_threshold = 0.0
        if threshold > 5000000.0:
            for item in tiers:
                l = float(item[0])
                u = float(item[1]) if item[1] is not None else float('inf')
                r = float(item[2])
                if threshold > l and threshold <= u:
                    surch_at_threshold = tax_at_threshold * r
                    break

        excess_income = taxable_income - threshold
        max_total = tax_at_threshold + surch_at_threshold + excess_income
        current_total = base_tax + nominal_surcharge

        marginal_relief = 0.0
        if current_total > max_total:
            marginal_relief = current_total - max_total
            actual_surcharge = max(0.0, nominal_surcharge - marginal_relief)
            audit.append(f"Surcharge Marginal Relief [Compiled]: Relieved ₹{marginal_relief:,.2f}; net surcharge ₹{actual_surcharge:,.2f}")
            return actual_surcharge, marginal_relief, audit

        return nominal_surcharge, 0.0, audit

    def calculate_old_regime(self, inp: SalaryInput) -> TaxBreakdown:
        audit = [f"--- Old Regime [LLM-Compiled Rules] ({self.fy}) ---"]
        std_ded = min(self.rules["std_deduction_old"], inp.gross_salary)
        audit.append(f"Sec 16(ia): Standard deduction allowed = ₹{std_ded:,.2f}")

        hra_ex, hra_audit = self.compute_hra_exemption(inp)
        audit.extend(hra_audit)

        sec_80c = min(inp.sec_80c, self.rules["sec_80c_max"])
        sec_80ccd = min(inp.sec_80ccd_1b, self.rules["sec_80ccd_1b_max"])

        limit_self = self.rules["sec_80d_senior_max"] if (inp.self_senior_citizen or inp.age >= 60) else self.rules["sec_80d_normal_max"]
        limit_parents = self.rules["sec_80d_senior_max"] if inp.parents_senior_citizen else self.rules["sec_80d_normal_max"]
        sec_80d = min(inp.sec_80d_self, limit_self) + min(inp.sec_80d_parents, limit_parents)

        sec_24b = min(inp.home_loan_interest, self.rules["sec_24b_max"])

        total_ded = std_ded + hra_ex + sec_80c + sec_80ccd + sec_80d + sec_24b
        taxable_income = round_it_section(max(0.0, inp.gross_salary - total_ded))
        audit.append(f"Sec 288A: Net Taxable Income = ₹{taxable_income:,.2f}")

        slabs = self._get_old_slabs(inp.age)
        slab_tax, slab_audit = self._compute_slab_tax(taxable_income, slabs)
        audit.extend(slab_audit)

        rebate_87a = 0.0
        if taxable_income <= self.rules["old_regime_rebate_limit"]:
            rebate_87a = min(slab_tax, self.rules["old_regime_rebate_max"])
            audit.append(f"Sec 87A: Full rebate ₹{rebate_87a:,.2f} applied")

        tax_after_rebate = max(0.0, slab_tax - rebate_87a)
        surch, m_relief, surch_audit = self._compute_surcharge(
            taxable_income, tax_after_rebate, self.rules["surcharge_tiers_old"], slabs
        )
        audit.extend(surch_audit)

        tax_plus_surch = tax_after_rebate + surch
        cess = tax_plus_surch * self.rules["cess_rate"]
        total_tax = round_it_section(tax_plus_surch + cess)
        audit.append(f"Sec 288B: Final Total Tax = ₹{total_tax:,.2f}")

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
            surcharge=surch,
            marginal_relief_surcharge=m_relief,
            cess=cess,
            total_tax=total_tax,
            effective_tax_rate=round(effective_rate, 2),
            audit_trail=audit
        )

    def calculate_new_regime(self, inp: SalaryInput) -> TaxBreakdown:
        audit = [f"--- New Regime [LLM-Compiled Rules] ({self.fy}) ---"]
        std_ded = min(self.rules["std_deduction_new"], inp.gross_salary)
        taxable_income = round_it_section(max(0.0, inp.gross_salary - std_ded))
        audit.append(f"Sec 288A: Net Taxable Income = ₹{taxable_income:,.2f}")

        slab_tax, slab_audit = self._compute_slab_tax(taxable_income, self.rules["new_regime_slabs"])
        audit.extend(slab_audit)

        rebate_limit = self.rules["new_regime_rebate_limit"]
        rebate_max = self.rules["new_regime_rebate_max"]
        rebate_87a = 0.0

        if taxable_income <= rebate_limit:
            rebate_87a = min(slab_tax, rebate_max)
            audit.append(f"Sec 87A: Full rebate ₹{rebate_87a:,.2f} applied")
        else:
            excess_income = taxable_income - rebate_limit
            if slab_tax > excess_income:
                rebate_87a = slab_tax - excess_income
                audit.append(f"Sec 87A Marginal Relief [Compiled]: Rebate ₹{rebate_87a:,.2f} applied")

        tax_after_rebate = max(0.0, slab_tax - rebate_87a)
        surch, m_relief, surch_audit = self._compute_surcharge(
            taxable_income, tax_after_rebate, self.rules["surcharge_tiers_new"], self.rules["new_regime_slabs"]
        )
        audit.extend(surch_audit)

        tax_plus_surch = tax_after_rebate + surch
        cess = tax_plus_surch * self.rules["cess_rate"]
        total_tax = round_it_section(tax_plus_surch + cess)
        audit.append(f"Sec 288B: Final Total Tax = ₹{total_tax:,.2f}")

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
            surcharge=surch,
            marginal_relief_surcharge=m_relief,
            cess=cess,
            total_tax=total_tax,
            effective_tax_rate=round(effective_rate, 2),
            audit_trail=audit
        )

    def compare_regimes(self, inp: SalaryInput) -> RegimeComparison:
        old_res = self.calculate_old_regime(inp)
        new_res = self.calculate_new_regime(inp)
        if old_res.total_tax < new_res.total_tax:
            recommended = "old"
            savings = new_res.total_tax - old_res.total_tax
            explanation = f"Old Regime saves ₹{savings:,.2f} due to deductions totaling ₹{old_res.total_deductions:,.2f}."
        elif new_res.total_tax < old_res.total_tax:
            recommended = "new"
            savings = old_res.total_tax - new_res.total_tax
            explanation = f"New Regime saves ₹{savings:,.2f} with lower slab rates."
        else:
            recommended = "new"
            savings = 0.0
            explanation = "Tax is identical under both regimes. New Regime is default."

        return RegimeComparison(
            old_regime=old_res,
            new_regime=new_res,
            recommended_regime=recommended,
            tax_savings=savings,
            explanation=explanation
        )
