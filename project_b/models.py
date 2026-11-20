"""
Data models for Project B: Data Quality Engine for NYC 311 Service Requests.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProblemType(str, Enum):
    RENAMED_OR_DROPPED_COLUMN = "a_renamed_or_dropped_column"
    COLUMN_TYPE_CHANGE = "b_column_type_change"
    DATE_FORMAT_SWITCH = "c_date_format_switch"
    LAT_LON_SWAPPED = "d_latitude_longitude_swapped"
    EXACT_DUPLICATES = "e_exact_duplicates"
    NEAR_DUPLICATES = "f_near_duplicates"
    NULL_SPIKE = "g_null_spike"
    CLOSED_BEFORE_CREATED = "h_closed_earlier_than_created"
    ZIP_BOROUGH_INCONSISTENT = "i_zip_borough_inconsistent"
    COMPLAINT_DESCRIPTOR_INCONSISTENT = "j_complaint_descriptor_inconsistent"
    RESOLUTION_STATUS_CONTRADICTING = "k_resolution_contradicting_status"
    PERSONAL_DATA_EXPOSURE = "l_personal_data_in_text"

class DetectorFamily(str, Enum):
    RULE = "rule"
    STATISTICAL = "statistical"
    LLM = "llm"
    HYBRID = "hybrid"

class QualityAlert(BaseModel):
    problem_type: ProblemType
    detector_family: DetectorFamily
    row_index: Optional[int] = None
    column_name: Optional[str] = None
    severity: str = "ERROR"  # "ERROR", "WARNING", "CRITICAL"
    explanation: str
    confidence: float = 1.0
    evidence: Dict[str, Any] = Field(default_factory=dict)

class BenchmarkMetric(BaseModel):
    problem_type: str
    detector_family: str
    detection_rate_pct: float     # Recall / Sensitivity
    false_alarm_rate_pct: float   # False Positive Rate (FPR) on clean data
    cost_per_million_rows_usd: float
    throughput_rows_per_sec: float
    alert_clarity_score: float    # 1.0 to 5.0 scale
    recommended: bool = False
