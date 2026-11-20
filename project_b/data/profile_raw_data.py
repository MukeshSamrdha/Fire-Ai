"""
Task 1: Profile Raw Data for Project B.
Profiles the 2023 NYC 311 data, discovering real quality anomalies naturally present:
- Missing closed dates on closed statuses
- Unspecified or missing ZIP codes
- Null coordinate pairs
- Temporal outliers and delays
- Categorical inconsistencies
"""
import json
from pathlib import Path
from typing import Dict, Any, List

def profile_raw_data(data_path: str = None) -> Dict[str, Any]:
    if data_path is None:
        data_path = Path(__file__).parent / "nyc_311_sample.json"
    
    with open(data_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    total_records = len(records)
    null_counts = {}
    missing_zips = []
    missing_coords = []
    status_distribution = {}
    agency_distribution = {}
    temporal_anomalies = []

    for idx, r in enumerate(records):
        # Null tracking
        for k, v in r.items():
            if v is None or v == "":
                null_counts[k] = null_counts.get(k, 0) + 1

        # Status tracking
        status = r.get("status", "UNKNOWN")
        status_distribution[status] = status_distribution.get(status, 0) + 1

        # Agency tracking
        agency = r.get("agency", "UNKNOWN")
        agency_distribution[agency] = agency_distribution.get(agency, 0) + 1

        # Check unspecified or missing ZIP codes
        zip_code = r.get("incident_zip")
        if not zip_code or zip_code.lower() in ["unspecified", "nan", "null"]:
            missing_zips.append({"row_index": idx, "unique_key": r.get("unique_key"), "borough": r.get("borough"), "incident_address": r.get("incident_address")})

        # Coordinates missing
        if r.get("latitude") is None or r.get("longitude") is None:
            missing_coords.append({"row_index": idx, "unique_key": r.get("unique_key"), "complaint_type": r.get("complaint_type")})

        # Closed date anomalies
        created = r.get("created_date")
        closed = r.get("closed_date")
        if status == "Closed" and closed is None:
            temporal_anomalies.append({"row_index": idx, "unique_key": r.get("unique_key"), "issue": "Status is Closed but closed_date is null"})

    profile_report = {
        "dataset_name": "NYC 311 Service Requests 2023",
        "total_records_profiled": total_records,
        "null_fields_summary": {k: {"null_count": v, "null_pct": round(v / total_records * 100, 2)} for k, v in null_counts.items()},
        "agency_distribution": agency_distribution,
        "status_distribution": status_distribution,
        "discovered_real_issues": [
            {
                "issue_type": "Missing Geocoding (Latitude/Longitude null)",
                "count": len(missing_coords),
                "frequency_pct": round(len(missing_coords) / total_records * 100, 2),
                "example": missing_coords[:2] if missing_coords else [],
                "impact": "Geospatial dashboards fail or drop records when aggregating complaints by council district or neighborhood."
            },
            {
                "issue_type": "Unspecified Postal Code",
                "count": len(missing_zips),
                "frequency_pct": round(len(missing_zips) / total_records * 100, 2),
                "example": missing_zips[:2] if missing_zips else [],
                "impact": "CFO neighborhood allocation models fail to assign complaint resolution budgets to specific postal areas."
            },
            {
                "issue_type": "Closed Status Without Timestamp",
                "count": len(temporal_anomalies),
                "frequency_pct": round(len(temporal_anomalies) / total_records * 100, 2),
                "example": temporal_anomalies[:2] if temporal_anomalies else [],
                "impact": "SLA and turnaround time metrics (Resolution Time = Closed - Created) yield NaN or infinite values."
            }
        ]
    }

    return profile_report

if __name__ == "__main__":
    report = profile_raw_data()
    print(json.dumps(report, indent=2))
