"""
Task 2: Corruption Injector for Project B.
Injects all 12 distinct quality problem types into clean NYC 311 batches at controlled rates:
a. Renamed or dropped column
b. Column type change (e.g. numbers arriving as strings)
c. Date format switch partway through a batch
d. Latitude and longitude swapped
e. Exact duplicates
f. Near-duplicates (same request, slightly altered timestamp or text)
g. Null spike in one agency's records
h. Closed date earlier than created date
i. ZIP code inconsistent with borough
j. Complaint Type inconsistent with Descriptor
k. Resolution Description contradicting Status
l. Personal data (phone numbers, emails, names) inside free-text fields
"""
import copy
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from project_b.models import ProblemType

# Contradictory pairs for testing
MISMATCHED_ZIP_BOROUGH = [
    ("10001", "BROOKLYN"),      # Manhattan zip with Brooklyn
    ("11201", "BRONX"),         # Brooklyn zip with Bronx
    ("10451", "STATEN ISLAND"), # Bronx zip with Staten Island
    ("11375", "MANHATTAN")      # Queens zip with Manhattan
]

INCONSISTENT_COMPLAINT_DESCRIPTOR = [
    ("Noise - Residential", "Pothole on roadway"),
    ("HEAT/HOT WATER", "Blocked Hydrant"),
    ("Street Condition", "Loud Music/Party"),
    ("Derelict Vehicles", "No Water/Low Pressure"),
    ("Water System", "Dirty Sidewalk")
]

CONTRADICTING_STATUS_RESOLUTIONS = [
    ("Closed", "Action pending: Case assigned to officer. Investigation currently ongoing."),
    ("Closed", "The department has not yet dispatched inspectors. Ticket is awaiting initial triage."),
    ("Open", "The Department inspected the condition on 03/15/2023 and completed all repairs. Condition closed."),
    ("Open", "Action completed: Summons issued and vehicle towed. Case resolved.")
]

PII_STRINGS = [
    "Complainant Johnathan Doe requested callback at 212-555-0199 or mobile (917) 555-4321.",
    "Contact resident Jane Smith at jane.smith@gmail.com regarding access to apartment 4B.",
    "Property owner Michael Chang provided SSN 123-45-6789 on the building permit.",
    "Please call reporter Sarah Connor at 646-555-8822 or email sconnor@cyberdyne.org immediately."
]

class CorruptionInjector:
    """Injects 12 controlled corruption types into NYC 311 datasets."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def inject_a_renamed_or_dropped_column(self, batch: List[Dict[str, Any]], drop: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        corrupted = copy.deepcopy(batch)
        if drop:
            for r in corrupted:
                r.pop("descriptor", None)
            meta = {"action": "dropped", "target_column": "descriptor"}
        else:
            for r in corrupted:
                if "descriptor" in r:
                    r["issue_description"] = r.pop("descriptor")
            meta = {"action": "renamed", "from": "descriptor", "to": "issue_description"}
        return corrupted, meta

    def inject_b_column_type_change(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            # Change float latitude to formatted string with currency or degree symbol
            if corrupted[idx].get("latitude") is not None:
                corrupted[idx]["latitude"] = f"{corrupted[idx]['latitude']}° N"
            if corrupted[idx].get("unique_key") is not None:
                corrupted[idx]["unique_key"] = float(corrupted[idx]["unique_key"])
        return corrupted, indices

    def inject_c_date_format_switch(self, batch: List[Dict[str, Any]], start_pct: float = 0.50) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        split_idx = int(len(corrupted) * start_pct)
        indices = list(range(split_idx, len(corrupted)))
        for idx in indices:
            orig = corrupted[idx].get("created_date")
            if orig:
                try:
                    dt = datetime.strptime(orig, "%Y-%m-%d %H:%M:%S")
                    # Switch from ISO to MM/DD/YYYY hh:mm:ss AM/PM or DD/MM/YYYY
                    corrupted[idx]["created_date"] = dt.strftime("%m/%d/%Y %I:%M:%S %p")
                except ValueError:
                    pass
        return corrupted, indices

    def inject_d_latitude_longitude_swapped(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            lat = corrupted[idx].get("latitude")
            lon = corrupted[idx].get("longitude")
            if lat is not None and lon is not None:
                corrupted[idx]["latitude"] = lon
                corrupted[idx]["longitude"] = lat
        return corrupted, indices

    def inject_e_exact_duplicates(self, batch: List[Dict[str, Any]], num_dups: int = 20) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        dup_indices = []
        source_indices = self.rng.sample(range(len(corrupted)), num_dups)
        for src in source_indices:
            dup_record = copy.deepcopy(corrupted[src])
            insert_pos = self.rng.randint(0, len(corrupted))
            corrupted.insert(insert_pos, dup_record)
            dup_indices.append(insert_pos)
        return corrupted, dup_indices

    def inject_f_near_duplicates(self, batch: List[Dict[str, Any]], num_dups: int = 20) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        near_indices = []
        source_indices = self.rng.sample(range(len(corrupted)), num_dups)
        for src in source_indices:
            near_rec = copy.deepcopy(corrupted[src])
            # Drift created_date by 5 seconds
            try:
                dt = datetime.strptime(near_rec["created_date"], "%Y-%m-%d %H:%M:%S")
                near_rec["created_date"] = (dt + timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
            # Slightly alter unique key
            near_rec["unique_key"] = str(int(near_rec["unique_key"]) + 9000000)
            insert_pos = self.rng.randint(0, len(corrupted))
            corrupted.insert(insert_pos, near_rec)
            near_indices.append(insert_pos)
        return corrupted, near_indices

    def inject_g_null_spike(self, batch: List[Dict[str, Any]], target_agency: str = "NYPD", null_rate: float = 0.85) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = []
        for idx, r in enumerate(corrupted):
            if r.get("agency") == target_agency:
                if self.rng.random() < null_rate:
                    r["complaint_type"] = None
                    r["descriptor"] = None
                    indices.append(idx)
        return corrupted, indices

    def inject_h_closed_date_earlier_than_created(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            created = corrupted[idx].get("created_date")
            if created:
                try:
                    dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                    # Set closed date to 3 days BEFORE created date
                    corrupted[idx]["closed_date"] = (dt - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
                    corrupted[idx]["status"] = "Closed"
                except Exception:
                    pass
        return corrupted, indices

    def inject_i_zip_borough_inconsistent(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            mismatch_zip, mismatch_borough = self.rng.choice(MISMATCHED_ZIP_BOROUGH)
            corrupted[idx]["incident_zip"] = mismatch_zip
            corrupted[idx]["borough"] = mismatch_borough
        return corrupted, indices

    def inject_j_complaint_descriptor_inconsistent(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            comp, desc = self.rng.choice(INCONSISTENT_COMPLAINT_DESCRIPTOR)
            corrupted[idx]["complaint_type"] = comp
            corrupted[idx]["descriptor"] = desc
        return corrupted, indices

    def inject_k_resolution_contradicting_status(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            stat, reso = self.rng.choice(CONTRADICTING_STATUS_RESOLUTIONS)
            corrupted[idx]["status"] = stat
            corrupted[idx]["resolution_description"] = reso
        return corrupted, indices

    def inject_l_personal_data_exposure(self, batch: List[Dict[str, Any]], rate: float = 0.10) -> Tuple[List[Dict[str, Any]], List[int]]:
        corrupted = copy.deepcopy(batch)
        indices = self.rng.sample(range(len(corrupted)), int(len(corrupted) * rate))
        for idx in indices:
            pii_snippet = self.rng.choice(PII_STRINGS)
            current_desc = corrupted[idx].get("resolution_description", "")
            corrupted[idx]["resolution_description"] = f"{current_desc} {pii_snippet}".strip()
        return corrupted, indices
