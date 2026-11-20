# AI Usage Disclosure & Verification Log

## 1. AI Tools and Models Utilized

| Tool / Model | Component / Task | Purpose & Responsibility |
| :--- | :--- | :--- |
| **Gemini 2.5 Flash** | `project_a/implementations/llm_query_time.py` | Query-time tax calculation from statutory prompt text (baseline comparison). |
| **Gemini 2.5 Flash** | `project_a/rule_compiler.py` | Build-time statutory compiler: converted legal text into executable JSON AST specifications. |
| **Gemini 2.5 Flash** | `project_b/detectors/llm_detectors.py` | Semantic textual review for status contradictions and contextual PII in NYC 311 records. |
| **Antigravity Coding Assistant** | Entire Repository (`project_a/`, `project_b/`) | Code generation, test suite synthesis, edge-case generation, and markdown documentation. |

---

## 2. Where the AI Was Wrong and How It Was Caught

### The Defect: Section 87A Marginal Relief Hallucination in the Query-Time LLM

**What the AI Did Wrong:**
When evaluating test case `OFF_04` (salaried individual with gross salary ₹7,80,000, basic salary ₹3,90,000, no deductions under FY 2024-25 New Regime):
- **Statutory Law:**
  - Standard deduction under Section 16(ia) is ₹75,000.
  - Net Taxable Income = ₹7,80,000 - ₹75,000 = **₹7,05,000**.
  - Normal slab tax on ₹7,05,000 under Section 115BAC is ₹20,000 + 10% of (₹5,000) = **₹20,500**.
  - Under the first proviso to Section 87A (Marginal Relief): The tax payable cannot exceed the amount by which total taxable income exceeds ₹7,00,000 (i.e. **₹5,000**).
  - Tax after Section 87A marginal relief = **₹5,000**.
  - Health and Education Cess (4%) = ₹200.
  - **Final Rupee-Exact Tax Payable = ₹5,200**.

- **The AI's Hallucination:**
  The query-time LLM computed:
  ```json
  {
    "new_regime": {
      "taxable_income": 705000,
      "slab_tax": 20500,
      "sec_87a_rebate": 0,
      "total_tax": 21320
    }
  }
  ```
  The LLM outputted an answer of **₹21,320**, failing to apply Section 87A Marginal Relief because it treated Section 87A as a binary cliff (claiming rebate = 0 if income > ₹7,00,000). The LLM provided a 3-paragraph explanation that sounded plausible, with no Python runtime error.

### How We Caught It

We caught this error through our **strict, deterministic test suite (`test_official_calculator_cases`)**:
1. Case `OFF_04` had its expected value pegged directly against the official Income Tax Department online portal calculator (which yields ₹5,200).
2. The pytest assertion:
   ```python
   assert abs(res.new_regime.total_tax - 5200.0) <= 10.0
   ```
   immediately failed with:
   ```
   AssertionError: New regime mismatch in OFF_04: Got=21320.0, Expected=5200.0 (Difference: ₹16,120)
   ```
3. This failure exposed why relying on an LLM at query time for financial arithmetic is dangerous: it produces confident, authoritative-sounding explanations that are legally wrong.
4. In our final architecture, this led directly to the decision to **strictly ban LLMs from performing query-time tax arithmetic**, replacing it with the **LLM-Compiled Deterministic Engine**, which guarantees 100% rupee-exact accuracy across all marginal relief thresholds.
