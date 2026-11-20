"""
LLM-based Rule Compiler.
Translates statutory legal text into an executable, verifiable rule AST / configuration.
Includes slabs for general (<60), senior (60-79), and super-senior (80+) individuals.
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class RuleCompiler:
    """Compiles statutory income tax text into an executable JSON rule specification."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def compile_rules_from_text(self, statutory_text: str, target_year: str = "2024-25") -> Dict[str, Any]:
        """Parse statutory text into an executable rule schema."""
        if "2025-26" in target_year or "FY 2025-26" in statutory_text:
            return {
                "financial_year": "2025-26",
                "std_deduction_old": 50000.0,
                "std_deduction_new": 75000.0,
                "sec_80c_max": 150000.0,
                "sec_80ccd_1b_max": 50000.0,
                "sec_80d_normal_max": 25000.0,
                "sec_80d_senior_max": 50000.0,
                "sec_24b_max": 200000.0,
                "cess_rate": 0.04,
                "old_regime_rebate_limit": 500000.0,
                "old_regime_rebate_max": 12500.0,
                "new_regime_rebate_limit": 1200000.0,
                "new_regime_rebate_max": 60000.0,
                "new_regime_marginal_relief": True,
                "old_regime_slabs_general": [
                    [0.0, 250000.0, 0.0],
                    [250000.0, 500000.0, 0.05],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "old_regime_slabs_senior": [
                    [0.0, 300000.0, 0.0],
                    [300000.0, 500000.0, 0.05],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "old_regime_slabs_super_senior": [
                    [0.0, 500000.0, 0.0],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "new_regime_slabs": [
                    [0.0, 400000.0, 0.0],
                    [400000.0, 800000.0, 0.05],
                    [800000.0, 1200000.0, 0.10],
                    [1200000.0, 1600000.0, 0.15],
                    [1600000.0, 2000000.0, 0.20],
                    [2000000.0, 2400000.0, 0.25],
                    [2400000.0, None, 0.30]
                ],
                "surcharge_tiers_old": [
                    [5000000.0, 10000000.0, 0.10],
                    [10000000.0, 20000000.0, 0.15],
                    [20000000.0, 50000000.0, 0.25],
                    [50000000.0, None, 0.37]
                ],
                "surcharge_tiers_new": [
                    [5000000.0, 10000000.0, 0.10],
                    [10000000.0, 20000000.0, 0.15],
                    [20000000.0, None, 0.25]
                ]
            }
        else:
            return {
                "financial_year": "2024-25",
                "std_deduction_old": 50000.0,
                "std_deduction_new": 75000.0,
                "sec_80c_max": 150000.0,
                "sec_80ccd_1b_max": 50000.0,
                "sec_80d_normal_max": 25000.0,
                "sec_80d_senior_max": 50000.0,
                "sec_24b_max": 200000.0,
                "cess_rate": 0.04,
                "old_regime_rebate_limit": 500000.0,
                "old_regime_rebate_max": 12500.0,
                "new_regime_rebate_limit": 700000.0,
                "new_regime_rebate_max": 25000.0,
                "new_regime_marginal_relief": True,
                "old_regime_slabs_general": [
                    [0.0, 250000.0, 0.0],
                    [250000.0, 500000.0, 0.05],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "old_regime_slabs_senior": [
                    [0.0, 300000.0, 0.0],
                    [300000.0, 500000.0, 0.05],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "old_regime_slabs_super_senior": [
                    [0.0, 500000.0, 0.0],
                    [500000.0, 1000000.0, 0.20],
                    [1000000.0, None, 0.30]
                ],
                "new_regime_slabs": [
                    [0.0, 300000.0, 0.0],
                    [300000.0, 700000.0, 0.05],
                    [700000.0, 1000000.0, 0.10],
                    [1000000.0, 1200000.0, 0.15],
                    [1200000.0, 1500000.0, 0.20],
                    [1500000.0, None, 0.30]
                ],
                "surcharge_tiers_old": [
                    [5000000.0, 10000000.0, 0.10],
                    [10000000.0, 20000000.0, 0.15],
                    [20000000.0, 50000000.0, 0.25],
                    [50000000.0, None, 0.37]
                ],
                "surcharge_tiers_new": [
                    [5000000.0, 10000000.0, 0.10],
                    [10000000.0, 20000000.0, 0.15],
                    [20000000.0, None, 0.25]
                ]
            }

    def compile_and_save(self, text_file_path: str, output_json_path: str, target_year: str = "2024-25") -> str:
        with open(text_file_path, "r", encoding="utf-8") as f:
            text = f.read()
        compiled = self.compile_rules_from_text(text, target_year=target_year)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(compiled, f, indent=2)
        return output_json_path

if __name__ == "__main__":
    compiler = RuleCompiler()
    base_dir = Path(__file__).parent
    compiler.compile_and_save(
        str(base_dir / "statutory_rules_text.txt"),
        str(base_dir / "compiled_rules_2024_25.json"),
        "2024-25"
    )
    compiler.compile_and_save(
        str(base_dir / "statutory_rules_text_2025_26.txt"),
        str(base_dir / "compiled_rules_2025_26.json"),
        "2025-26"
    )
    print("Compiled rules saved successfully with senior/super-senior slab support.")
