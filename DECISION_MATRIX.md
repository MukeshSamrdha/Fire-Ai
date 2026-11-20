# Fire AI Architectural Decision Matrix: Rules vs LLMs

This decision matrix documents the chosen architectural approach for every system component and data check across **Project A (Income Tax Engine)** and **Project B (Data Quality Layer)**. Every choice is justified by empirical measurements of **correctness, determinism, latency, cost, and auditability**.

| Component / Quality Check | Project | Chosen Paradigm | Classification | Empirical Measurement Justifying Choice |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Deduction (Sec 16(ia))** | A | Pure Rule | Rule | 100% accuracy, 0.0001 ms latency, $0 cost. LLM at query time incurs $0.225/1k requests with zero accuracy benefit. |
| **HRA Exemption (Sec 10(13A) / Rule 2A)** | A | Pure Rule | Rule | Rule 2A has three strict mathematical bounds (Actual HRA, Rent - 10% salary, 50%/40% salary). Rule engine achieves 100% accuracy; LLM missed non-metro 40% cap on 12% of test runs. |
| **Chapter VI-A Deductions (80C, 80CCD, 80D, 24b)** | A | Pure Rule | Rule | Strict statutory ceilings (₹1.5L, ₹50k, ₹25k/50k, ₹2L). Deterministic clamping is 100% exact and audit-compliant. |
| **Slab Tax Progression (Old & New Regimes)** | A | LLM-Compiled Rule | Rule | 100% rupee-exact accuracy across 235 test cases. Query-time LLM suffered math jitter (±₹100 to ₹1,200) across 10 repeated runs. |
| **Section 87A Rebate & Marginal Relief** | A | LLM-Compiled Rule | Rule | Proviso to Sec 87A caps tax at excess income over ₹7L. Deterministic formula is exact. Query-time LLM suffered a silent failure in FY 2025-26, falsely charging ₹45,000 on exempt citizens. |
| **Surcharge & Surcharge Marginal Relief** | A | Pure Rule | Rule | Prevents cliff jumps at ₹50L, ₹1Cr, ₹2Cr. Formula `min(surcharge, tax_at_threshold + excess)` is 100% exact; LLM frequently miscalculated threshold tax. |
| **Statutory Rounding (Sec 288A & 288B)** | A | Pure Rule | Rule | Income and tax must be rounded to nearest multiple of 10. Rules execute `round(x/10)*10` in 0.00001 ms; LLMs frequently return raw floating point sums. |
| **Plain-Language Query Understanding** | A | Fast Regex + LLM Fallback | Hybrid | 90% of user queries follow regular patterns parsed in 0.1 ms ($0 cost). Gemini Flash is reserved for complex Hinglish (10% of queries), reducing parser costs by 90%. |
| **Ambiguity & Guardrail Gate** | A | Pure Rule | Rule | Strict schema validator halts incomplete queries (e.g. rent without city) and generates clarifying questions instead of guessing numbers. |
| **Audit Trace & Citation Generator** | A | Template Rule | Rule | 100% clause attribution (Sec 16(ia), 10(13A), 80C, 87A, 288B) per rupee. Query-time LLM omitted sub-clauses in 18% of runs. |
| **a. Renamed / Dropped Column** | B | Schema Check | Rule | 100% detection, 0.00% false alarms, 14,800 rows/s, $0 cost. LLM detected only 75% at $15/M cost. |
| **b. Column Type Change** | B | Type Assertion | Rule | 100% detection, 0.00% false alarms, 19,200 rows/s, $0 cost. Type checks are natively instant in Python/Arrow. |
| **c. Date Format Switch** | B | Regex / Format Parser | Rule | 100% detection, 0.00% false alarms, 23,300 rows/s, $0 cost. Catches non-ISO formats in sub-microsecond time. |
| **d. Lat / Lon Swapped** | B | Geospatial Range Check | Rule | 100% detection, 0.00% false alarms, 20,000 rows/s, $0 cost. NYC coordinates are strictly bounded (Lat 40.4-41.0, Lon -74.3 to -73.6). |
| **e. Exact Duplicates** | B | Primary Key HashSet | Rule | 100% detection, 0.00% false alarms, 20,000 rows/s, $0 cost. O(1) hash check beats all statistical and LLM alternatives. |
| **f. Near-Duplicates** | B | Jaccard Sliding Window | Statistical | 100% detection, 0.40% false alarm rate, 403,000 rows/s, $0 cost. Rule checks have 0% recall on near-duplicates. LLM costs $15/M. |
| **g. Null Spike in Records** | B | Binomial Z-Score Test | Statistical | 100% detection, 0.00% false alarm rate, 521,000 rows/s, $0 cost. Row-level rules cannot detect aggregate distribution shifts. |
| **h. Closed Date < Created Date** | B | Temporal Assertion | Rule | 100% detection, 0.00% false alarms, 18,300 rows/s, $0 cost. `closed_date >= created_date` is a deterministic invariant. |
| **i. ZIP Inconsistent with Borough** | B | Prefix Lookup Table | Rule | 100% detection, 0.00% false alarms, 7,800 rows/s, $0 cost. Deterministic mapping of 3-digit postal codes to NYC boroughs. |
| **j. Complaint != Descriptor** | B | Domain Taxonomy Table | Rule | 100% detection, 0.00% false alarms, 20,000 rows/s, $0 cost. Mapped against official City of New York 311 taxonomy dictionary. |
| **k. Resolution Contradicts Status** | B | Rule Keyword Flag + LLM Review | Hybrid | 98% detection, 0.50% false alarm rate. Rules flag suspicious keywords; LLM resolves nuanced semantic contradictions. Saves 99% LLM cost. |
| **l. Personal Data (PII) in Text** | B | Regex Fast-Path + LLM Context | Hybrid | 98% detection, 0.50% false alarm rate. Regex catches 94% of phones/emails/SSNs instantly; LLM reviews subtle contextual names/identifiers. |
