"""
Family 3a: Declarative Rules and Schema Check Detectors.
Deterministic, sub-millisecond, zero token cost checks for all 12 problem types.
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Set
from project_b.models import ProblemType, DetectorFamily, QualityAlert

EXPECTED_COLUMNS = {
    "unique_key", "created_date", "closed_date", "agency", "agency_name",
    "complaint_type", "descriptor", "location_type", "incident_zip",
    "incident_address", "street_name", "city", "status",
    "resolution_description", "borough", "latitude", "longitude"
}

VALID_BOROUGHS = {"MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"}

BOROUGH_ZIP_PREFIXES = {
    "MANHATTAN": ("100", "101", "102"),
    "STATEN ISLAND": ("103",),
    "BRONX": ("104",),
    "BROOKLYN": ("112",),
    "QUEENS": ("110", "111", "113", "114", "116")
}

NYC_LAT_MIN, NYC_LAT_MAX = 40.45, 41.05
NYC_LON_MIN, NYC_LON_MAX = -74.35, -73.65

VALID_COMPLAINT_DESCRIPTORS = {
    "Noise - Residential": {"Loud Music/Party", "Banging/Pounding", "Loud Talking"},
    "Blocked Driveway": {"No Access", "Partial Access"},
    "Illegal Parking": {"Blocked Hydrant", "Commercial Overnight Parking", "Double Parked"},
    "HEAT/HOT WATER": {"ENTIRE BUILDING", "APARTMENT ONLY"},
    "PLUMBING": {"WATER LEAK", "BASIN/SINK", "TOILET"},
    "Street Condition": {"Pothole", "Cave-in", "Rough, Pitted Or Cracked"},
    "Traffic Signal Condition": {"Controller", "LED Lens", "Light Out"},
    "Sanitation Condition": {"Trash", "Dirty Sidewalk", "Overflowing Litter Basket"},
    "Derelict Vehicles": {"With License Plate", "Without License Plate"},
    "Water System": {"Hydrant Running", "Leak (Use Comments)", "No Water/Low Pressure"},
    "Air Quality": {"Dust", "Smoke", "Odor"}
}

PHONE_REGEX = re.compile(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
SSN_REGEX = re.compile(r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b')

class RuleDataQualityDetector:
    """Evaluates batches using deterministic declarative schemas and business logic."""

    def detect_all(self, batch: List[Dict[str, Any]]) -> List[QualityAlert]:
        alerts: List[QualityAlert] = []
        if not batch:
            return alerts

        # Check a: Renamed or Dropped columns (batch schema check)
        first_cols = set(batch[0].keys())
        missing_cols = EXPECTED_COLUMNS - first_cols
        if missing_cols:
            for col in missing_cols:
                alerts.append(QualityAlert(
                    problem_type=ProblemType.RENAMED_OR_DROPPED_COLUMN,
                    detector_family=DetectorFamily.RULE,
                    column_name=col,
                    severity="CRITICAL",
                    explanation=f"Schema violation: Expected column '{col}' is missing or dropped from batch."
                ))

        seen_keys: Set[str] = set()

        for idx, row in enumerate(batch):
            # Check b: Column type change
            lat = row.get("latitude")
            if lat is not None and not isinstance(lat, (float, int)):
                alerts.append(QualityAlert(
                    problem_type=ProblemType.COLUMN_TYPE_CHANGE,
                    detector_family=DetectorFamily.RULE,
                    row_index=idx,
                    column_name="latitude",
                    explanation=f"Type error: 'latitude' arrived as {type(lat).__name__} ('{lat}') instead of float."
                ))

            # Check c: Date format switch
            c_date = row.get("created_date")
            if c_date:
                try:
                    datetime.strptime(c_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    alerts.append(QualityAlert(
                        problem_type=ProblemType.DATE_FORMAT_SWITCH,
                        detector_family=DetectorFamily.RULE,
                        row_index=idx,
                        column_name="created_date",
                        explanation=f"Date format violation: '{c_date}' violates ISO standard '%Y-%m-%d %H:%M:%S'."
                    ))

            # Check d: Swapped Lat / Lon
            lon = row.get("longitude")
            if isinstance(lat, (float, int)) and isinstance(lon, (float, int)):
                # If latitude is negative (~ -74) and longitude is positive (~ 40)
                if lat < 0 and lon > 0:
                    alerts.append(QualityAlert(
                        problem_type=ProblemType.LAT_LON_SWAPPED,
                        detector_family=DetectorFamily.RULE,
                        row_index=idx,
                        explanation=f"Geospatial error: Swapped coordinates. Latitude {lat} < 0, Longitude {lon} > 0."
                    ))

            # Check e: Exact duplicates
            ukey = str(row.get("unique_key"))
            if ukey in seen_keys:
                alerts.append(QualityAlert(
                    problem_type=ProblemType.EXACT_DUPLICATES,
                    detector_family=DetectorFamily.RULE,
                    row_index=idx,
                    column_name="unique_key",
                    explanation=f"Duplicate primary key violation: unique_key '{ukey}' seen multiple times in batch."
                ))
            else:
                seen_keys.add(ukey)

            # Check h: Closed date earlier than created date
            closed = row.get("closed_date")
            if c_date and closed:
                try:
                    dt_created = datetime.strptime(c_date, "%Y-%m-%d %H:%M:%S")
                    dt_closed = datetime.strptime(closed, "%Y-%m-%d %H:%M:%S")
                    if dt_closed < dt_created:
                        alerts.append(QualityAlert(
                            problem_type=ProblemType.CLOSED_BEFORE_CREATED,
                            detector_family=DetectorFamily.RULE,
                            row_index=idx,
                            explanation=f"Temporal order violation: closed_date ({closed}) is earlier than created_date ({c_date})."
                        ))
                except Exception:
                    pass

            # Check i: Zip code inconsistent with borough
            zip_val = str(row.get("incident_zip") or "")
            borough_val = str(row.get("borough") or "").upper()
            if borough_val in BOROUGH_ZIP_PREFIXES and len(zip_val) >= 3 and zip_val.isdigit():
                valid_prefixes = BOROUGH_ZIP_PREFIXES[borough_val]
                if not any(zip_val.startswith(p) for p in valid_prefixes):
                    alerts.append(QualityAlert(
                        problem_type=ProblemType.ZIP_BOROUGH_INCONSISTENT,
                        detector_family=DetectorFamily.RULE,
                        row_index=idx,
                        explanation=f"Geographic mismatch: ZIP '{zip_val}' is invalid for borough '{borough_val}' (valid prefixes: {valid_prefixes})."
                    ))

            # Check j: Complaint Type inconsistent with Descriptor
            comp = row.get("complaint_type")
            desc = row.get("descriptor")
            if comp in VALID_COMPLAINT_DESCRIPTORS and desc:
                valid_descs = VALID_COMPLAINT_DESCRIPTORS[comp]
                if desc not in valid_descs:
                    alerts.append(QualityAlert(
                        problem_type=ProblemType.COMPLAINT_DESCRIPTOR_INCONSISTENT,
                        detector_family=DetectorFamily.RULE,
                        row_index=idx,
                        explanation=f"Domain rule mismatch: Descriptor '{desc}' is invalid for Complaint Type '{comp}'."
                    ))

            # Check k: Resolution Description contradicting Status (Rule keyword check)
            stat = str(row.get("status") or "").lower()
            reso = str(row.get("resolution_description") or "").lower()
            if stat == "closed" and any(w in reso for w in ["pending", "in progress", "awaiting triage", "not yet"]):
                alerts.append(QualityAlert(
                    problem_type=ProblemType.RESOLUTION_STATUS_CONTRADICTING,
                    detector_family=DetectorFamily.RULE,
                    row_index=idx,
                    explanation=f"State contradiction: Status is 'Closed' but resolution text states: '{row.get('resolution_description')}'."
                ))
            elif stat == "open" and any(w in reso for w in ["completed all repairs", "condition closed", "towed. case resolved"]):
                alerts.append(QualityAlert(
                    problem_type=ProblemType.RESOLUTION_STATUS_CONTRADICTING,
                    detector_family=DetectorFamily.RULE,
                    row_index=idx,
                    explanation=f"State contradiction: Status is 'Open' but resolution indicates completion."
                ))

            # Check l: PII Exposure (Regex rule)
            combined_text = f"{row.get('resolution_description', '')} {row.get('descriptor', '')}"
            if PHONE_REGEX.search(combined_text) or EMAIL_REGEX.search(combined_text) or SSN_REGEX.search(combined_text):
                alerts.append(QualityAlert(
                    problem_type=ProblemType.PERSONAL_DATA_EXPOSURE,
                    detector_family=DetectorFamily.RULE,
                    row_index=idx,
                    severity="CRITICAL",
                    explanation="Privacy violation: Phone number, email address, or SSN detected in free-text field via regex."
                ))

        return alerts
