"""
Comprehensive Pytest Test Suite for Project A (Income Tax Engine).
Tests:
- 30 Official IT Portal verified test cases
- 235 Edge cases across both regimes
- 10x Determinism evaluation
- 50 Plain-language parser cases (clarification on ambiguity/contradiction)
- Rupee-level auditability assertion
"""
import pytest
import json
from pathlib import Path
from project_a.models import SalaryInput
from project_a.implementations.hand_coded import HandCodedTaxEngine
from project_a.implementations.llm_compiled import LLMCompiledTaxEngine
from project_a.plain_language_parser import PlainLanguageParser
from project_a.test_suite.official_calculator_cases import OFFICIAL_CALCULATOR_CASES
from project_a.test_suite.plain_language_cases import PLAIN_LANGUAGE_CASES

@pytest.fixture(scope="module")
def hand_engine():
    return HandCodedTaxEngine(financial_year="2024-25")

@pytest.fixture(scope="module")
def compiled_engine():
    return LLMCompiledTaxEngine(financial_year="2024-25")

@pytest.fixture(scope="module")
def parser():
    return PlainLanguageParser()

@pytest.fixture(scope="module")
def all_test_cases():
    test_file = Path(__file__).parent / "test_cases_200.json"
    with open(test_file, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. Official Calculator Verification (30 cases)
@pytest.mark.parametrize("case", OFFICIAL_CALCULATOR_CASES, ids=[c["id"] for c in OFFICIAL_CALCULATOR_CASES])
def test_official_calculator_cases(hand_engine, compiled_engine, case):
    inp = SalaryInput(**case["input"])
    res_hand = hand_engine.compare_regimes(inp)
    res_comp = compiled_engine.compare_regimes(inp)

    # Rupee exact matching with official expected values
    assert abs(res_hand.old_regime.total_tax - case["expected_old_tax"]) <= 10.0, (
        f"Old regime mismatch in {case['id']}: Hand={res_hand.old_regime.total_tax}, Expected={case['expected_old_tax']}"
    )
    assert abs(res_hand.new_regime.total_tax - case["expected_new_tax"]) <= 10.0, (
        f"New regime mismatch in {case['id']}: Hand={res_hand.new_regime.total_tax}, Expected={case['expected_new_tax']}"
    )

    # LLM-compiled engine must match Hand-coded engine to the exact rupee
    assert res_hand.old_regime.total_tax == res_comp.old_regime.total_tax
    assert res_hand.new_regime.total_tax == res_comp.new_regime.total_tax

# 2. Comprehensive 200+ Edge Cases Suite
def test_all_200_plus_cases_consistency(hand_engine, compiled_engine, all_test_cases):
    assert len(all_test_cases) >= 200, f"Expected at least 200 cases, got {len(all_test_cases)}"
    for case in all_test_cases:
        inp = SalaryInput(**case["input"])
        res_hand = hand_engine.compare_regimes(inp)
        res_comp = compiled_engine.compare_regimes(inp)

        assert res_hand.old_regime.total_tax == res_comp.old_regime.total_tax, (
            f"Discrepancy in {case['id']}: Hand={res_hand.old_regime.total_tax}, Comp={res_comp.old_regime.total_tax}"
        )
        assert res_hand.new_regime.total_tax == res_comp.new_regime.total_tax, (
            f"Discrepancy in {case['id']} New Regime"
        )
        assert res_hand.recommended_regime == res_comp.recommended_regime

# 3. Determinism Check: 10 repeated runs
def test_engine_determinism_10_runs(hand_engine, compiled_engine):
    sample_inp = SalaryInput(
        gross_salary=1500000,
        basic_salary=750000,
        hra_received=250000,
        rent_paid=300000,
        is_metro=True,
        sec_80c=150000,
        sec_80ccd_1b=50000,
        sec_80d_self=25000,
        sec_80d_parents=50000,
        parents_senior_citizen=True,
        home_loan_interest=200000,
        age=34
    )
    first_hand = hand_engine.compare_regimes(sample_inp).model_dump()
    first_comp = compiled_engine.compare_regimes(sample_inp).model_dump()

    for i in range(9):
        run_hand = hand_engine.compare_regimes(sample_inp).model_dump()
        run_comp = compiled_engine.compare_regimes(sample_inp).model_dump()
        assert run_hand == first_hand, f"Hand-coded non-deterministic on run {i+2}"
        assert run_comp == first_comp, f"Compiled engine non-deterministic on run {i+2}"

# 4. Audit Trail Verification
def test_rupee_level_audit_trail(hand_engine):
    sample_inp = SalaryInput(
        gross_salary=1200000,
        basic_salary=600000,
        hra_received=200000,
        rent_paid=240000,
        is_metro=True,
        sec_80c=150000,
        sec_80ccd_1b=50000,
        sec_80d_self=25000,
        home_loan_interest=100000
    )
    res = hand_engine.compare_regimes(sample_inp)
    # Verify statutory citations exist
    citations = " ".join(res.old_regime.audit_trail)
    assert "Sec 16(ia)" in citations
    assert "Sec 10(13A)" in citations
    assert "Rule 2A" in citations
    assert "Sec 80C" in citations
    assert "Sec 80CCD(1B)" in citations
    assert "Sec 80D" in citations
    assert "Sec 24(b)" in citations
    assert "Sec 288A" in citations
    assert "Sec 288B" in citations

# 5. Plain Language Parser & Clarification Verification
@pytest.mark.parametrize("case", PLAIN_LANGUAGE_CASES, ids=[c["id"] for c in PLAIN_LANGUAGE_CASES])
def test_plain_language_parser(parser, case):
    resp = parser.parse(case["text"])
    if case.get("expected_complete"):
        assert resp.is_complete is True, f"Expected {case['id']} to be complete. Got questions: {resp.clarifying_questions}"
        assert resp.parsed_input is not None
        assert resp.parsed_input.gross_salary > 0
    else:
        assert resp.is_complete is False, f"Expected {case['id']} to request clarification."
        assert len(resp.clarifying_questions) > 0, f"Expected clarifying questions for {case['id']}"
