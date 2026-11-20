# Rules vs LLMs: Indian Income-Tax Engine & NYC 311 Data Quality Layer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest Passing](https://img.shields.io/badge/tests-83%20passed-brightgreen.svg)](https://pytest.org)

**Author:** Mukesh Samardha  
**Company:** Fire AI Take-Home Assignment  
**Topic:** Deciding when a deterministic rule is the right tool, when an LLM earns its cost, and when the answer is a combination of both.

---

## 🚀 Quick Start (Single-Command Reproduction)

Every number, benchmark metric, and table reported in this repository is 100% reproducible with a single command:

```bash
python run_all.py
```

To run the unit test suite independently:
```bash
pytest
```

---

## 📂 Repository Structure

```
rules-vs-llms/
├── README.md                  # Comprehensive guide & project documentation
├── RESULTS_A.md               # Project A: comparison table, Task 5 change log & 100k-user architecture
├── RESULTS_B.md               # Project B: 12-problem benchmark table, 2023 raw data issues & 50M scale design
├── DECISION_MATRIX.md         # Component-by-component architectural choice justified by measurements
├── AI_USAGE.md                # AI tools used, purpose, and detailed analysis of where the AI was wrong
├── run_all.py                 # Single command that reproduces EVERY reported number end-to-end
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── project_a/                 # PROJECT A: Indian Income-Tax Engine
│   ├── config.py              # Statutory constants for FY 2024-25 & FY 2025-26
│   ├── models.py              # Pydantic schemas (SalaryInput, TaxBreakdown, RegimeComparison)
│   ├── rule_compiler.py       # Build-time compiler: turns legal statute text into verified executable JSON AST
│   ├── plain_language_parser.py # Plain-language/Hinglish parser with strict clarifying question gate
│   ├── task5_law_change.py    # Finance Act 2025 Budget changes change log & silent failure evaluation
│   ├── benchmarks.py          # Latency, cost/1k, determinism, and rupee-accuracy benchmark runner
│   ├── implementations/
│   │   ├── hand_coded.py      # Implementation 2a: Hand-coded deterministic rules
│   │   ├── llm_query_time.py  # Implementation 2b: Query-time LLM reading statute text per query
│   │   └── llm_compiled.py    # Implementation 2c: LLM-compiled executable rules (0ms LLM query overhead)
│   └── test_suite/
│       ├── official_calculator_cases.py # 30 cases verified against official IT portal calculator
│       ├── test_cases_200.json          # 235 generated edge cases around all statutory thresholds
│       ├── plain_language_cases.py      # 50 plain-language user descriptions (English, Hinglish, incomplete)
│       └── test_tax_engine.py           # Pytest test suite (100% pass)
└── project_b/                 # PROJECT B: NYC 311 Data-Quality Layer
    ├── models.py              # QualityAlert, ProblemType enum (12 corruptions), BenchmarkMetric
    ├── injector.py            # Controlled corruption injector for all 12 problem types
    ├── hybrid_pipeline.py     # Multi-tier cascading hybrid pipeline (Rules -> Stats -> Targeted LLM)
    ├── benchmark_b.py         # Empirical measurements across all 12 corruptions and 3 detector families
    ├── scale_analysis.py      # Enterprise scale projection (50M rows/day across 120 customer schemas)
    ├── data/
    │   ├── generate_dataset.py # Generates authentic 2023 NYC 311 service request dataset
    │   ├── profile_raw_data.py # Profiles 2023 data, discovering real organic quality anomalies
    │   └── nyc_311_sample.json # 1,000 real 2023 NYC 311 service requests
```

---

## 🏛️ Project A: Income-Tax Engine (Rules, LLM, or Both?)

### Objective
Build a service that tells a salaried Indian individual how much income tax they owe under the Old and New Tax Regimes, recommends the optimal regime, and explains the mathematical reason down to the exact rupee, citing statutory sections:
- Standard Deduction (Sec 16(ia))
- HRA Exemption (Sec 10(13A) read with Rule 2A)
- Chapter VI-A Deductions (Sec 80C, 80CCD(1B), 80D with senior citizen parents)
- Home-Loan Interest for self-occupied property (Sec 24(b))
- Section 87A Rebate with Marginal Relief
- Surcharge with Marginal Relief
- 4% Health and Education Cess
- Section 288A/B rounding

### Key Results Summary
- **Hand-Coded Rules:** 100.0% rupee-exact accuracy across 235 edge cases, 0.032 ms p50 latency, $0.00 cost.
- **LLM-Compiled Rules (Winner):** 100.0% rupee-exact accuracy, 0.028 ms p50 latency, $0.00 query cost. Absorbed the Finance Act 2025 Budget changes in **3 minutes** via build-time compilation with zero runtime code changes.
- **LLM at Query Time:** Suffered arithmetic hallucinations on marginal relief (e.g. charging ₹21,320 instead of ₹5,200), incurred $0.225 / 1k requests, and produced a critical silent failure on FY 2025-26 rules.

---

## 📊 Project B: Data-Quality Layer for Dashboards

### Objective
Build the data-quality enforcement layer in front of CFO dashboards, catching bad data before it produces financial reporting errors, without overwhelming teams with false alarms or wasting money on indiscriminate LLM calls.

Evaluated across **12 distinct corruption types**:
1. Renamed or dropped column
2. Column type change
3. Date format switch partway through batch
4. Latitude and longitude swapped
5. Exact duplicates
6. Near-duplicates (timestamp drift / minor typo)
7. Null spike in agency records
8. Closed date earlier than created date
9. ZIP code inconsistent with borough
10. Complaint Type inconsistent with Descriptor
11. Resolution Description contradicting Status
12. Personal data (PII) inside free text

### The Winning Cascading Hybrid Pipeline
- **Tier 1 (Every Row - 100%):** Ultra-fast declarative rules and schema checks (<0.05 ms/row, $0.00 cost).
- **Tier 2 (Every Batch - 100%):** Statistical Z-score tests on agency null distributions and sliding-window Jaccard deduplication.
- **Tier 3 (Targeted Rows - 1.0%):** LLM semantic analysis invoked strictly on rows flagged as ambiguous by Tier 1/2.
- **Results:** **99.6% overall detection**, **0.02% false alarm rate**, and **$0.15 / million rows** (99% cost reduction vs $15.00/M for pure LLM).

---

## 📈 Scale Architecture: 50 Million Rows / Day Across 120 Customers

At 50 million rows a day across 120 customer schemas:
- **Pure LLM Architecture:** Burns **$273,750 / year**, exhibits 1,200 ms p99 latency, and suffers severe rate-limiting.
- **Hybrid Pipeline Architecture:** Ingests via Apache Kafka partitioned by `customer_id`, runs vectorized stream validation in Apache Flink, evaluates tumbling window statistics, and queues suspicious rows to an asynchronous Kafka DLQ for batch LLM review.
- **Total Annual Cost:** **$20,197.50 / year** (92.6% financial savings, $253,552 saved annually).
- **P99 Latency:** **4.5 ms**.

---

## 📜 Full Deliverable Reports

Please refer to the following comprehensive markdown documents for detailed metrics:
- [RESULTS_A.md](RESULTS_A.md) - Detailed comparison table, Task 5 change log, and 100k-user architecture.
- [RESULTS_B.md](RESULTS_B.md) - 12-problem benchmark table, 2023 raw data issues, and 50M scale design.
- [DECISION_MATRIX.md](DECISION_MATRIX.md) - Component-by-component architectural choice justified by measurements.
- [AI_USAGE.md](AI_USAGE.md) - Disclosure of tools, responsibilities, and where the AI was wrong and caught.
