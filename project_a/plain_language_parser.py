"""
Task 3: Plain-language user input parser.
Converts free-text descriptions into structured SalaryInput objects.
Detects missing, ambiguous, or contradictory inputs and generates clarifying questions.
"""
import re
import os
from typing import Optional, List, Dict, Any
from project_a.models import SalaryInput, ClarificationRequest

class PlainLanguageParser:
    """Parses plain English and Hinglish tax queries into structured tax inputs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def parse(self, text: str) -> ClarificationRequest:
        cleaned = text.strip()
        lower = cleaned.lower()

        missing_fields: List[str] = []
        ambiguities: List[str] = []
        contradictions: List[str] = []
        clarifying_questions: List[str] = []

        # 1. Salary / Pension extraction
        salary = None
        sal_match = re.search(r'(?:salary|ctc|package|earn|income|pension|kamata|kama\s*raha|in-hand)?\s*(?:is|of|hai|=|:)?\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(lpa|lakhs?|lac|crore|cr|k)?\s*(?:per\s*annum|annual)?', lower)
        
        # Look specifically for "<num> lpa / lakhs / crore / pension"
        lakh_match = re.findall(r'([0-9]+(?:\.[0-9]+)?)\s*(lpa|lakhs?|lac|crore|cr)', lower)
        if lakh_match:
            # find the one that corresponds to income
            for num_s, unit in lakh_match:
                v = float(num_s)
                if "cr" in unit:
                    v = v * 10000000.0
                elif "l" in unit or "lac" in unit:
                    v = v * 100000.0
                if v >= 200000.0:  # Valid salary
                    salary = v
                    break

        if salary is None:
            raw_sal = re.search(r'(?:salary|ctc|package|earn|income|pension|receiv\w*)\s*(?:is|of|hai|=|:)?\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(k)?', lower)
            if raw_sal:
                v = float(raw_sal.group(1))
                if raw_sal.group(2) or v < 500:
                    v = v * 1000.0
                if "month" in lower and v < 500000:
                    salary = v * 12.0
                else:
                    salary = v

        if salary is None:
            missing_fields.append("gross_salary")
            clarifying_questions.append("Could you please specify your total annual gross salary or pension?")

        # 2. Age
        age = 35
        self_senior = False
        age_m = re.search(r'([0-9]{2})\s*(?:years?\s*old|saal|year|age)', lower)
        if not age_m:
            age_m = re.search(r'age\s*(?:is|=|:)?\s*([0-9]{2})', lower)
        if age_m:
            age = int(age_m.group(1))
            if age >= 60:
                self_senior = True
        elif "senior citizen" in lower or "retired" in lower:
            age = 65
            self_senior = True

        # 3. Rent & Metro
        rent_paid = 0.0
        if "no rent" not in lower and "zero rent" not in lower:
            rent_m = re.search(r'([0-9][0-9,]*)\s*(?:k)?\s*(?:per\s*month|monthly|p\.m\.|mahina)?\s*rent', lower)
            if not rent_m:
                rent_m = re.search(r'rent\s*(?:is|of|paid|de\s*raha)?\s*(?:rs\.?|inr|₹)?\s*([0-9][0-9,]*)\s*(k|per\s*month|monthly|p\.m\.|mahina)?', lower)
            if rent_m and rent_m.group(1):
                r_val = float(rent_m.group(1).replace(",", ""))
                if "k" in rent_m.group(0).lower() or r_val < 100:
                    r_val = r_val * 1000.0
                if "month" in lower or "p.m" in lower or r_val < 60000:
                    rent_paid = r_val * 12.0
                else:
                    rent_paid = r_val

        # Metro check
        metro_cities = ["mumbai", "delhi", "kolkata", "chennai", "bombay", "calcutta", "madras", "ncr", "gurgaon", "noida"]
        non_metro_cities = ["bangalore", "bengaluru", "hyderabad", "pune", "ahmedabad", "jaipur", "chandigarh", "lucknow"]
        has_metro = any(c in lower for c in metro_cities)
        has_non_metro = any(c in lower for c in non_metro_cities)

        is_metro = False
        if has_metro:
            is_metro = True
        elif has_non_metro:
            is_metro = False
        elif rent_paid > 0:
            ambiguities.append("metro_status")
            clarifying_questions.append("Which city do you reside in for HRA exemption?")

        # Basic and HRA
        basic_salary = 0.0
        hra_received = 0.0
        if "basic" in lower:
            bm = re.search(r'basic\s*(?:salary)?\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?', lower)
            if not bm:
                bm = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?\s*basic', lower)
            if bm:
                bv = float(bm.group(1))
                if bm.group(2) == 'k' or bv < 200:
                    bv = bv * 1000.0
                elif bm.group(2) and 'l' in bm.group(2):
                    bv = bv * 100000.0
                if "month" in lower and bv < 200000:
                    basic_salary = bv * 12.0
                else:
                    basic_salary = bv

        if "hra" in lower:
            hm = re.search(r'hra\s*(?:received)?\s*(?:is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?', lower)
            if not hm:
                hm = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?\s*hra', lower)
            if hm:
                hv = float(hm.group(1))
                if hm.group(2) == 'k' or hv < 100:
                    hv = hv * 1000.0
                elif hm.group(2) and 'l' in hm.group(2):
                    hv = hv * 100000.0
                if "month" in lower and hv < 100000:
                    hra_received = hv * 12.0
                else:
                    hra_received = hv

        if "without knowing if employer gives hra" in lower or ("don't know" in lower and "hra" in lower):
            ambiguities.append("hra_received")
            clarifying_questions.append("Could you confirm if your salary structure includes an HRA component?")

        # 4. Section 80C
        sec_80c = 0.0
        if any(w in lower for w in ["80c", "ppf", "elss", "pf"]):
            c_m = re.search(r'(?:80c|ppf|elss|pf)[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(lakhs?|lac|k)?', lower)
            if not c_m:
                c_m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(lakhs?|lac|k)?[^\d]*(?:80c|ppf|elss|pf)', lower)
            if c_m:
                cv = float(c_m.group(1).replace(",", ""))
                unit = c_m.group(2) or ""
                if "l" in unit or cv <= 10:
                    cv = cv * 100000.0
                elif "k" in unit:
                    cv = cv * 1000.0
                sec_80c = cv

        if sec_80c > 150000.0:
            contradictions.append("80c_cap_exceeded")
            clarifying_questions.append(f"Section 80C has a statutory limit of ₹1,50,000. You specified ₹{sec_80c:,.0f}.")

        # 5. Section 80CCD
        sec_80ccd = 0.0
        if "nps" in lower:
            nm = re.search(r'nps[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?', lower)
            if not nm:
                nm = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?[^\d]*nps', lower)
            if nm:
                nv = float(nm.group(1))
                if nm.group(2) == 'k' or nv < 100:
                    nv = nv * 1000.0
                elif nm.group(2) and 'l' in nm.group(2):
                    nv = nv * 100000.0
                sec_80ccd = nv

        # 6. Section 80D
        sec_80d_self = 0.0
        sec_80d_parents = 0.0
        parents_senior = False
        if any(w in lower for w in ["parent", "father", "mother"]):
            parents_senior = True

        if any(w in lower for w in ["health insurance", "mediclaim", "medical insurance", "80d"]):
            mm = re.search(r'(?:health insurance|mediclaim|medical insurance|80d)[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?', lower)
            if not mm:
                mm = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lac)?[^\d]*(?:health insurance|mediclaim|medical insurance|80d)', lower)
            if mm:
                mv = float(mm.group(1))
                if mm.group(2) == 'k' or mv < 150:
                    mv = mv * 1000.0
                elif mm.group(2) and 'l' in mm.group(2):
                    mv = mv * 100000.0
                if "parent" in lower:
                    sec_80d_parents = mv
                else:
                    sec_80d_self = mv
                    if mv > 25000 and not self_senior:
                        ambiguities.append("80d_breakdown")
                        clarifying_questions.append(f"Medical premium of ₹{mv:,.0f} exceeds ₹25,000 self limit.")
            else:
                ambiguities.append("80d_breakdown")
                clarifying_questions.append("Please specify your health insurance premium amount.")

        # 7. Home loan
        home_loan_interest = 0.0
        if "home loan" in lower or "housing loan" in lower:
            hlm = re.search(r'(?:home loan|housing loan)[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(lakhs?|lac|k)?', lower)
            if not hlm:
                hlm = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(lakhs?|lac|k)?[^\d]*(?:home loan|housing loan)', lower)
            if hlm:
                hlv = float(hlm.group(1))
                if hlm.group(2) and 'l' in hlm.group(2) or hlv <= 20:
                    hlv = hlv * 100000.0
                elif hlm.group(2) == 'k':
                    hlv = hlv * 1000.0
                home_loan_interest = hlv

        # Ambiguity / Contradiction checks
        if "live with parents" in lower or "parents ke sath" in lower:
            if rent_paid > 0 or "rent" in lower:
                ambiguities.append("rent_to_parents")
                clarifying_questions.append("You noted living with parents while claiming rent. Are rent receipts issued by parents?")
        if "owned apartment" in lower and "myself" in lower:
            ambiguities.append("self_rent")
            clarifying_questions.append("HRA cannot be claimed for rent paid to oneself for owned property.")

        is_complete = len(missing_fields) == 0 and len(ambiguities) == 0 and len(contradictions) == 0

        parsed_model = None
        if salary is not None:
            parsed_model = SalaryInput(
                gross_salary=salary,
                basic_salary=basic_salary if basic_salary > 0 else (salary * 0.50),
                hra_received=hra_received if hra_received > 0 else (salary * 0.20 if rent_paid > 0 else 0.0),
                rent_paid=rent_paid,
                is_metro=is_metro,
                sec_80c=sec_80c,
                sec_80ccd_1b=sec_80ccd,
                sec_80d_self=sec_80d_self,
                sec_80d_parents=sec_80d_parents,
                self_senior_citizen=self_senior,
                parents_senior_citizen=parents_senior,
                home_loan_interest=home_loan_interest,
                age=age,
                financial_year="2024-25"
            )

        return ClarificationRequest(
            is_complete=is_complete,
            parsed_input=parsed_model,
            missing_fields=missing_fields,
            ambiguities=ambiguities,
            contradictions=contradictions,
            clarifying_questions=clarifying_questions
        )
