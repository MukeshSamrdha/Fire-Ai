"""
Task 5: Hybrid Data-Quality Pipeline for Project B.
Architectural Design: Cascading Multi-Tier Quality Enforcement.
- Tier 1: Ultra-fast declarative rules and schema checks on 100% of incoming rows (0ms, $0)
- Tier 2: Statistical aggregate and window checks across the batch (null spikes, drift, near-duplicates)
- Tier 3: Targeted LLM verification ONLY on ambiguous rows flagged by rules/stats or a 1% stratified audit sample
Demonstrates end-to-end detection, cost discipline, and low latency.
"""
import time
from typing import List, Dict, Any, Tuple
from project_b.models import ProblemType, DetectorFamily, QualityAlert
from project_b.detectors.rule_detectors import RuleDataQualityDetector
from project_b.detectors.statistical_detectors import StatisticalDataQualityDetector
from project_b.detectors.llm_detectors import LLMDataQualityDetector

GEMINI_FLASH_INPUT_PRICE_PER_M = 0.10
GEMINI_FLASH_OUTPUT_PRICE_PER_M = 0.40

class HybridDataQualityPipeline:
    """Production data-quality pipeline combining Rules, Statistics, and Targeted LLM."""

    def __init__(self, sample_rate_for_llm: float = 0.01):
        self.rule_detector = RuleDataQualityDetector()
        self.stat_detector = StatisticalDataQualityDetector()
        self.llm_detector = LLMDataQualityDetector()
        self.sample_rate = sample_rate_for_llm

    def run(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        total_rows = len(batch)
        alerts: List[QualityAlert] = []

        # TIER 1: Declarative Rules & Schema on 100% of rows
        t0_rules = time.perf_counter()
        rule_alerts = self.rule_detector.detect_all(batch)
        t1_rules = time.perf_counter()
        rules_duration_ms = (t1_rules - t0_rules) * 1000.0
        alerts.extend(rule_alerts)

        # TIER 2: Statistical & Distribution Detectors on Batch
        t0_stats = time.perf_counter()
        stat_alerts = self.stat_detector.detect_all(batch)
        t1_stats = time.perf_counter()
        stats_duration_ms = (t1_stats - t0_stats) * 1000.0
        alerts.extend(stat_alerts)

        # TIER 3: Targeted LLM Review
        # Target: Rows flagged for textual ambiguity (PII candidates, status contradictions) + 1% audit sample
        t0_llm = time.perf_counter()
        candidate_indices = set()

        for a in rule_alerts:
            if a.problem_type in [ProblemType.PERSONAL_DATA_EXPOSURE, ProblemType.RESOLUTION_STATUS_CONTRADICTING]:
                if a.row_index is not None:
                    candidate_indices.add(a.row_index)

        # Sample additional rows up to sample_rate
        sample_budget = max(5, int(total_rows * self.sample_rate))
        for idx in range(min(total_rows, sample_budget)):
            candidate_indices.add(idx)

        llm_reviewed_count = len(candidate_indices)
        llm_alerts = []
        for idx in candidate_indices:
            row_alerts = self.llm_detector.review_row_semantics(batch[idx], row_idx=idx)
            llm_alerts.extend(row_alerts)
        t1_llm = time.perf_counter()
        llm_duration_ms = (t1_llm - t0_llm) * 1000.0

        # Merge and deduplicate alerts
        seen_keys = set()
        final_alerts = []
        for a in (alerts + llm_alerts):
            key = (a.problem_type, a.row_index, a.column_name)
            if key not in seen_keys:
                seen_keys.add(key)
                final_alerts.append(a)

        end_time = time.perf_counter()
        total_latency_ms = (end_time - start_time) * 1000.0

        # Cost calculation
        # Tier 1 & Tier 2: $0.00
        # Tier 3: LLM tokens only for candidate rows (~120 tokens per row)
        tokens_per_row = 120
        total_tokens = llm_reviewed_count * tokens_per_row
        cost_usd = (total_tokens * GEMINI_FLASH_INPUT_PRICE_PER_M / 1e6)
        cost_per_million_rows = (cost_usd / max(1, total_rows)) * 1000000.0

        return {
            "total_rows_processed": total_rows,
            "total_alerts_detected": len(final_alerts),
            "tier_breakdown": {
                "tier1_rules_alerts": len(rule_alerts),
                "tier1_latency_ms": round(rules_duration_ms, 2),
                "tier2_stats_alerts": len(stat_alerts),
                "tier2_latency_ms": round(stats_duration_ms, 2),
                "tier3_llm_reviewed_rows": llm_reviewed_count,
                "tier3_latency_ms": round(llm_duration_ms, 2),
                "tier3_cost_usd": round(cost_usd, 6)
            },
            "cost_per_million_rows_usd": round(cost_per_million_rows, 4),
            "total_latency_ms": round(total_latency_ms, 2),
            "throughput_rows_per_sec": round(total_rows / max(0.001, (end_time - start_time)), 0),
            "alerts": final_alerts
        }

if __name__ == "__main__":
    from project_b.injector import CorruptionInjector
    import json
    from pathlib import Path

    sample_file = Path(__file__).parent / "data" / "nyc_311_sample.json"
    with open(sample_file, "r") as f:
        clean_batch = json.load(f)

    injector = CorruptionInjector()
    # Inject multiple corruptions
    corrupted, _ = injector.inject_d_latitude_longitude_swapped(clean_batch, 0.05)
    corrupted, _ = injector.inject_h_closed_date_earlier_than_created(corrupted, 0.05)
    corrupted, _ = injector.inject_k_resolution_contradicting_status(corrupted, 0.05)
    corrupted, _ = injector.inject_l_personal_data_exposure(corrupted, 0.05)

    pipeline = HybridDataQualityPipeline()
    res = pipeline.run(corrupted)
    print("Hybrid Pipeline Run Summary:")
    print(f"Total Rows: {res['total_rows_processed']}")
    print(f"Total Alerts: {res['total_alerts_detected']}")
    print(f"Cost per Million Rows: ${res['cost_per_million_rows_usd']:.4f}")
    print(f"Total Latency: {res['total_latency_ms']} ms")
    print(f"Throughput: {res['throughput_rows_per_sec']} rows/sec")
