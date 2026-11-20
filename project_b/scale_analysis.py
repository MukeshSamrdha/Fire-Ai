"""
Task 6: Scale and Architecture Projections for Project B.
Calculates latency, throughput, hardware footprint, and operational costs
at enterprise scale: 50 Million rows/day across 120 customer schemas.
Analyzes architectural transformations from laptop script to distributed stream processing.
"""
import json
from typing import Dict, Any

def calculate_scale_projections() -> Dict[str, Any]:
    daily_volume = 50_000_000
    num_customers = 120
    avg_rows_per_sec = daily_volume / 86400.0  # ~578.7 rows/sec steady state
    peak_rows_per_sec = avg_rows_per_sec * 3.5  # ~2,025 rows/sec peak burst

    # Pure LLM Architecture (Naive baseline: Every row sent to Gemini Flash)
    tokens_per_row = 150
    daily_llm_tokens = daily_volume * tokens_per_row  # 7.5 Billion tokens/day
    cost_per_m_tokens_input = 0.10
    daily_cost_pure_llm = (daily_llm_tokens / 1e6) * cost_per_m_tokens_input
    annual_cost_pure_llm = daily_cost_pure_llm * 365

    # Hybrid Cascading Architecture (Fire AI Recommended Design)
    # Tier 1 (Rules): 100% of rows (50M rows/day) -> $0.00 compute tokens
    # Tier 2 (Stats): Batch aggregates per 10k batch -> $0.00 compute tokens
    # Tier 3 (LLM): 0.5% flagged suspicious rows + 0.5% audit sample = 1.0% of rows (500k rows/day)
    tier3_rows_daily = daily_volume * 0.010
    tier3_tokens_daily = tier3_rows_daily * tokens_per_row  # 75 Million tokens/day
    daily_cost_hybrid_tokens = (tier3_tokens_daily / 1e6) * cost_per_m_tokens_input
    annual_cost_hybrid_tokens = daily_cost_hybrid_tokens * 365

    # Cloud Infrastructure Sizing (Distributed Flink/Kafka cluster)
    infra_costs = {
        "kafka_msk_cluster_3_brokers": 450.0,      # $450/month
        "flink_compute_nodes_c6g_4xlarge": 720.0,  # 3 worker nodes @ $240/mo
        "redis_metadata_cache": 85.0,              # Schema cache for 120 customers
        "observability_datadog_prometheus": 200.0
    }
    monthly_infra = sum(infra_costs.values())
    annual_infra = monthly_infra * 12

    total_annual_hybrid_cost = annual_cost_hybrid_tokens + annual_infra
    annual_savings_vs_pure_llm = annual_cost_pure_llm - total_annual_hybrid_cost

    return {
        "scale_parameters": {
            "daily_volume_rows": daily_volume,
            "num_tenants_customers": num_customers,
            "average_throughput_rows_sec": round(avg_rows_per_sec, 1),
            "peak_throughput_rows_sec": round(peak_rows_per_sec, 1)
        },
        "pure_llm_cost_comparison": {
            "daily_cost_usd": round(daily_cost_pure_llm, 2),
            "annual_cost_usd": round(annual_cost_pure_llm, 2),
            "latency_p99_ms": 1200.0,
            "feasibility": "Commercially and operationally unviable; burns >$273,000/year and risks API rate-limiting."
        },
        "hybrid_pipeline_cost_projection": {
            "daily_token_cost_usd": round(daily_cost_hybrid_tokens, 2),
            "annual_token_cost_usd": round(annual_cost_hybrid_tokens, 2),
            "annual_cloud_infra_usd": round(annual_infra, 2),
            "total_annual_cost_usd": round(total_annual_hybrid_cost, 2),
            "cost_per_million_rows_usd": round((total_annual_hybrid_cost / (daily_volume * 365)) * 1e6, 3),
            "annual_savings_usd": round(annual_savings_vs_pure_llm, 2),
            "latency_p99_ms": 4.5
        },
        "architectural_transformations_at_scale": [
            {
                "subsystem": "Data Ingestion & Routing",
                "laptop_design": "In-memory Python list / Pandas DataFrame",
                "production_50m_scale": "Apache Kafka partitioned by customer_id with schema header tags. Ensures strict tenant isolation and backpressure."
            },
            {
                "subsystem": "Tier 1: Rule Engine",
                "laptop_design": "Sequential Python loops & Regex",
                "production_50m_scale": "Apache Flink streaming operators running vectorized PyArrow/Cython compiled validators. Latency <0.1ms/row."
            },
            {
                "subsystem": "Schema Registry for 120 Tenants",
                "laptop_design": "Hardcoded dictionary in python file",
                "production_50m_scale": "Apicurio / Confluent Schema Registry with customer-specific Protobuf/Avro schemas cached in Redis."
            },
            {
                "subsystem": "Tier 2: Statistical Anomaly Detection",
                "laptop_design": "Batch-level Counter & Z-score",
                "production_50m_scale": "Flink tumbling event-time windows (5-minute windows) computing HyperLogLog cardinality and online t-digest quantiles."
            },
            {
                "subsystem": "Tier 3: LLM Verification",
                "laptop_design": "Synchronous single-call API invocation",
                "production_50m_scale": "Asynchronous Dead-Letter Queue (Kafka DLQ) with batching and priority token buckets (Gemini Flash API rate-limit protected)."
            }
        ]
    }

if __name__ == "__main__":
    report = calculate_scale_projections()
    print(json.dumps(report, indent=2))
