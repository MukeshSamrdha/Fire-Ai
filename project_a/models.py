"""
Data models for Project A Income Tax Engine.
Includes rupee-exact validation, audit trail entries, and clarification models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SalaryInput(BaseModel):
    """Structured input representing a salaried taxpayer's financial profile."""
    gross_salary: float = Field(0.0, ge=0.0, description="Total gross annual salary before deductions")
    basic_salary: float = Field(0.0, ge=0.0, description="Annual Basic salary component")
    da: float = Field(0.0, ge=0.0, description="Dearness Allowance forming part of retirement benefits")
    hra_received: float = Field(0.0, ge=0.0, description="House Rent Allowance received from employer")
    rent_paid: float = Field(0.0, ge=0.0, description="Actual annual house rent paid by employee")
    is_metro: bool = Field(False, description="True if residing in Delhi, Mumbai, Kolkata, or Chennai")
    
    # Deductions
    sec_80c: float = Field(0.0, ge=0.0, description="Section 80C investments (EPF, PPF, ELSS, LIC, tuition)")
    sec_80ccd_1b: float = Field(0.0, ge=0.0, description="Section 80CCD(1B) additional NPS contribution (up to 50k)")
    sec_80d_self: float = Field(0.0, ge=0.0, description="Section 80D medical insurance for self, spouse, children")
    sec_80d_parents: float = Field(0.0, ge=0.0, description="Section 80D medical insurance for parents")
    self_senior_citizen: bool = Field(False, description="True if self/spouse is age 60 or above")
    parents_senior_citizen: bool = Field(False, description="True if parents are age 60 or above")
    home_loan_interest: float = Field(0.0, ge=0.0, description="Section 24(b) interest on self-occupied housing loan")
    
    age: int = Field(35, ge=0, le=120, description="Taxpayer age in years")
    financial_year: str = Field("2024-25", description="Financial Year (e.g. '2024-25' or '2025-26')")

    def model_post_init(self, __context: Any) -> None:
        """If gross salary is not explicitly set but components are, sum them."""
        computed_gross = self.basic_salary + self.da + self.hra_received
        if self.gross_salary == 0.0 and computed_gross > 0.0:
            self.gross_salary = computed_gross

class TaxBreakdown(BaseModel):
    """Rupee-exact breakdown of income tax liability with full audit trace."""
    regime: str  # 'old' or 'new'
    financial_year: str
    gross_salary: float
    standard_deduction: float
    hra_exemption: float
    sec_80c_deduction: float
    sec_80ccd_1b_deduction: float
    sec_80d_deduction: float
    sec_24b_deduction: float
    total_deductions: float
    taxable_income: float
    slab_tax: float
    sec_87a_rebate: float
    tax_after_rebate: float
    surcharge: float
    marginal_relief_surcharge: float
    cess: float
    total_tax: float
    effective_tax_rate: float
    audit_trail: List[str] = Field(default_factory=list)

class RegimeComparison(BaseModel):
    """Comparison between Old and New regimes with clear user recommendation."""
    old_regime: TaxBreakdown
    new_regime: TaxBreakdown
    recommended_regime: str
    tax_savings: float
    explanation: str
    breakeven_deduction_point: float = 0.0

class ClarificationRequest(BaseModel):
    """Structured response when user input is incomplete, ambiguous, or contradictory."""
    is_complete: bool
    parsed_input: Optional[SalaryInput] = None
    missing_fields: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)
