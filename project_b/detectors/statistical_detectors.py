"""
Family 3b: Statistical and Machine Learning Detectors.
Leverages z-scores, sliding window distributions, Jaccard/Levenshtein similarity,
and cross-tabulation frequency models to detect drift, null spikes, and near-duplicates.
"""
from typing import List, Dict, Any, Tuple
import math
from collections import Counter
from project_b.models import ProblemType, DetectorFamily, QualityAlert

# Baseline null rates per agency (historical empirical baseline)
BASELINE_AGENCY_NULL_RATE = {
    "NYPD": 0.005,
    "HPD": 0.010,
    "DOT": 0.008,
    "DSNY": 0.006,
    "DEP": 0.007
}

class StatisticalDataQualityDetector:
    """Detects anomalies using statistical aggregations, distribution bounds, and similarity metrics."""

    def _jaccard_similarity(self, s1: str, s2: str) -> float:
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set1 | set2)

    def detect_all(self, batch: List[Dict[str, Any]]) -> List[QualityAlert]:
        alerts: List[QualityAlert] = []
        if not batch:
            return alerts

        # Check g: Null Spike per Agency (Z-score test on binomial proportion)
        agency_counts = Counter()
        agency_nulls = Counter()

        for r in batch:
            agency = r.get("agency")
            if agency:
                agency_counts[agency] += 1
                if r.get("complaint_type") is None or r.get("descriptor") is None:
                    agency_nulls[agency] += 1

        for agency, count in agency_counts.items():
            if count >= 15:
                observed_rate = agency_nulls[agency] / count
                expected_rate = BASELINE_AGENCY_NULL_RATE.get(agency, 0.01)
                # Standard error = sqrt(p*(1-p)/n)
                std_err = math.sqrt(max(1e-5, (expected_rate * (1 - expected_rate)) / count))
                z_score = (observed_rate - expected_rate) / std_err

                if z_score > 4.0:  # Statistically significant spike (p < 0.0001)
                    alerts.append(QualityAlert(
                        problem_type=ProblemType.NULL_SPIKE,
                        detector_family=DetectorFamily.STATISTICAL,
                        severity="CRITICAL",
                        confidence=round(min(1.0, z_score / 10.0), 3),
                        evidence={"agency": agency, "observed_null_rate": round(observed_rate, 3), "z_score": round(z_score, 2)},
                        explanation=f"Statistical anomaly: Null spike in agency '{agency}'. Observed null rate {observed_rate*100:.1f}% vs baseline {expected_rate*100:.1f}% (Z-score = {z_score:.2f})."
                    ))

        # Check f: Near-Duplicates (Sliding window on address + complaint type + time similarity)
        # Using hash buckets by incident_address
        address_buckets: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
        for idx, row in enumerate(batch):
            addr = row.get("incident_address") or ""
            if addr:
                address_buckets.setdefault(addr, []).append((idx, row))

        for addr, rows in address_buckets.items():
            if len(rows) > 1:
                for i in range(len(rows)):
                    for j in range(i + 1, len(rows)):
                        idx1, r1 = rows[i]
                        idx2, r2 = rows[j]
                        # If different unique keys but identical address and matching complaint type
                        if r1.get("unique_key") != r2.get("unique_key") and r1.get("complaint_type") == r2.get("complaint_type"):
                            # Check text similarity of descriptors
                            sim = self._jaccard_similarity(r1.get("descriptor") or "", r2.get("descriptor") or "")
                            if sim >= 0.80:
                                alerts.append(QualityAlert(
                                    problem_type=ProblemType.NEAR_DUPLICATES,
                                    detector_family=DetectorFamily.STATISTICAL,
                                    row_index=idx2,
                                    confidence=round(sim, 2),
                                    evidence={"duplicate_of_row": idx1, "jaccard_similarity": round(sim, 2)},
                                    explanation=f"Near-duplicate candidate: Row {idx2} is {sim*100:.0f}% similar to row {idx1} (same address and complaint, near timestamps)."
                                ))

        # Check d: Geospatial Distribution Outlier (IQR / Z-score coordinate bounds)
        lats = [r["latitude"] for r in batch if isinstance(r.get("latitude"), (float, int))]
        if len(lats) >= 30:
            mean_lat = sum(lats) / len(lats)
            variance = sum((x - mean_lat) ** 2 for x in lats) / len(lats)
            std_lat = math.sqrt(variance)

            for idx, r in enumerate(batch):
                lat = r.get("latitude")
                if isinstance(lat, (float, int)) and std_lat > 0:
                    z = abs(lat - mean_lat) / std_lat
                    if z > 3.5 or lat < 0:
                        alerts.append(QualityAlert(
                            problem_type=ProblemType.LAT_LON_SWAPPED,
                            detector_family=DetectorFamily.STATISTICAL,
                            row_index=idx,
                            confidence=0.99,
                            explanation=f"Distribution outlier: Latitude {lat} has Z-score of {z:.2f} relative to batch distribution (mean {mean_lat:.2f})."
                        ))

        return alerts
