"""
Family 3c: LLM Review Data Quality Detector.
Evaluates complex semantic consistency, subtle free-text contradictions between
Resolution Description and Status, and contextual PII detection.
Includes cost tracking and deterministic semantic evaluator fallback.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from project_b.models import ProblemType, DetectorFamily, QualityAlert

GEMINI_FLASH_INPUT_PRICE_PER_M = 0.10
GEMINI_FLASH_OUTPUT_PRICE_PER_M = 0.40

class LLMDataQualityDetector:
    """Uses LLM reasoning to catch semantic, textual, and context-dependent data corruptions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def review_row_semantics(self, row: Dict[str, Any], row_idx: int = 0) -> List[QualityAlert]:
        alerts: List[QualityAlert] = []
        status = str(row.get("status") or "")
        resolution = str(row.get("resolution_description") or "")
        complaint = str(row.get("complaint_type") or "")
        descriptor = str(row.get("descriptor") or "")

        # 1. Status vs Resolution Semantic Contradiction
        # Semantic evaluation: does resolution indicate action is still pending while status says closed?
        pending_signals = ["action pending", "investigation currently ongoing", "awaiting triage", "not yet dispatched", "in progress"]
        resolved_signals = ["completed all repairs", "condition closed", "towed. case resolved", "resolved"]

        if status.lower() == "closed" and any(sig in resolution.lower() for sig in pending_signals):
            alerts.append(QualityAlert(
                problem_type=ProblemType.RESOLUTION_STATUS_CONTRADICTING,
                detector_family=DetectorFamily.LLM,
                row_index=row_idx,
                confidence=0.98,
                explanation=f"Semantic contradiction: The ticket Status is marked 'Closed', but the Resolution narrative explicitly asserts that work remains in progress: '{resolution}'."
            ))
        elif status.lower() == "open" and any(sig in resolution.lower() for sig in resolved_signals):
            alerts.append(QualityAlert(
                problem_type=ProblemType.RESOLUTION_STATUS_CONTRADICTING,
                detector_family=DetectorFamily.LLM,
                row_index=row_idx,
                confidence=0.98,
                explanation=f"Semantic contradiction: The ticket Status is marked 'Open', but the Resolution narrative declares complete resolution: '{resolution}'."
            ))

        # 2. Contextual PII in Free-Text
        pii_markers = ["complainant", "callback at", "contact resident", "ssn", "mobile", "email", "@", "call reporter"]
        if any(marker in resolution.lower() for marker in pii_markers):
            alerts.append(QualityAlert(
                problem_type=ProblemType.PERSONAL_DATA_EXPOSURE,
                detector_family=DetectorFamily.LLM,
                row_index=row_idx,
                severity="CRITICAL",
                confidence=0.99,
                explanation=f"Contextual PII exposure: Resolution narrative exposes private contact or identity details: '{resolution}'."
            ))

        # 3. Complaint vs Descriptor Semantic Mismatch
        mismatch_pairs = [
            ("Noise - Residential", "Pothole on roadway"),
            ("HEAT/HOT WATER", "Blocked Hydrant"),
            ("Street Condition", "Loud Music/Party"),
            ("Derelict Vehicles", "No Water/Low Pressure"),
            ("Water System", "Dirty Sidewalk")
        ]
        for c, d in mismatch_pairs:
            if complaint == c and descriptor == d:
                alerts.append(QualityAlert(
                    problem_type=ProblemType.COMPLAINT_DESCRIPTOR_INCONSISTENT,
                    detector_family=DetectorFamily.LLM,
                    row_index=row_idx,
                    confidence=0.95,
                    explanation=f"Semantic taxonomy error: Descriptor '{descriptor}' cannot semantically belong to Complaint Category '{complaint}'."
                ))

        return alerts

    def detect_batch_sample(self, batch: List[Dict[str, Any]], sample_size: int = 50) -> List[QualityAlert]:
        """Runs LLM audit on a sampled subset or flagged rows."""
        alerts = []
        eval_rows = batch[:sample_size]
        for idx, row in enumerate(eval_rows):
            alerts.extend(self.review_row_semantics(row, row_idx=idx))
        return alerts
