"""
50 plain-language user tax descriptions in varied styles:
- Conversational English
- Hinglish (Hindi + English colloquialisms)
- Incomplete descriptions requiring clarification
- Contradictory descriptions requiring clarification
"""
from typing import List, Dict, Any

PLAIN_LANGUAGE_CASES: List[Dict[str, Any]] = [
    # Complete cases - English & Hinglish
    {"id": "PL_01", "text": "My annual CTC is 12 LPA. Basic salary is 50,000 monthly, I invest 1.5 lakh in 80C PPF, no rent, age 29.", "expected_complete": True},
    {"id": "PL_02", "text": "Mera salary package 18 LPA hai, basic 60k per month, rent 30k monthly de raha hu Mumbai me, 80c me 150000 hai, age 32.", "expected_complete": True},
    {"id": "PL_03", "text": "I earn 7.5 lakhs gross. Age 25, no investments or rent paid.", "expected_complete": True},
    {"id": "PL_04", "text": "Package 25 lakhs annual, basic 12 lakhs, 80C 1.5L, NPS 50k, health insurance 25k for self, age 38.", "expected_complete": True},
    {"id": "PL_05", "text": "Gross salary 5,00,000 rupees. Fresher, age 22, no savings.", "expected_complete": True},
    {"id": "PL_06", "text": "Mera annual income 15 lakh hai. Home loan interest 2 lakh de raha hu aur 80C me 1.5 lakh. Age 35.", "expected_complete": True},
    {"id": "PL_07", "text": "I am a retired individual aged 67 years receiving pension of 9 lakhs per annum. Medical insurance premium 50k.", "expected_complete": True},
    {"id": "PL_08", "text": "CTC 30 LPA, age 42, basic 15L, NPS 80CCD 50,000, 80C 150,000, no rent.", "expected_complete": True},
    {"id": "PL_09", "text": "Salary 8,50,000. Age 28, living in Delhi paying 20k monthly rent, basic 40k monthly, HRA received 20k monthly.", "expected_complete": True},
    {"id": "PL_10", "text": "Kolkata resident, earning 14 lakhs gross, basic 7 lakhs, HRA 2.5 lakhs, rent 25,000 per month, age 33.", "expected_complete": True},
    {"id": "PL_11", "text": "Package 4.5 lakhs, age 24. No deductions.", "expected_complete": True},
    {"id": "PL_12", "text": "Gross salary 60 lakhs, age 49, no deductions claimed.", "expected_complete": True},
    {"id": "PL_13", "text": "Earning 1.2 Crore per year, basic 60 lakhs, age 51, no rent.", "expected_complete": True},
    {"id": "PL_14", "text": "Super senior citizen age 82, salary/pension 12 lakhs, 80C 1.5 lakhs.", "expected_complete": True},
    {"id": "PL_15", "text": "Salary 10 LPA in Chennai, basic 45k monthly, HRA 18k monthly, rent paid 15k monthly, age 29.", "expected_complete": True},
    {"id": "PL_16", "text": "Mera package 16 lakh hai Gurgaon mein, basic 8 lakh, HRA 2.4 lakh, rent 22k monthly, 80C full 1.5L.", "expected_complete": True},
    {"id": "PL_17", "text": "Gross 22 LPA, NPS 50k, 80C 1.5L, home loan 1.8L interest, age 41.", "expected_complete": True},
    {"id": "PL_18", "text": "Annual salary 6.5 LPA, age 26, zero investment.", "expected_complete": True},
    {"id": "PL_19", "text": "Gross 11 lakhs, basic 5.5L, 80C 150k, mediclaim 20k, age 34.", "expected_complete": True},
    {"id": "PL_20", "text": "Package 7.75 lakhs, no deductions, age 27.", "expected_complete": True},

    # Incomplete cases - Missing city, missing salary, or missing HRA
    {"id": "PL_21", "text": "I pay 25,000 rent per month and earn 15 lakhs. How much tax?", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_22", "text": "How much tax will I pay if I invest 1.5L in 80C and have home loan interest?", "expected_complete": False, "missing_or_ambiguous": "gross_salary"},
    {"id": "PL_23", "text": "Mera rent 20k per month hai. Tax kitna bachega?", "expected_complete": False, "missing_or_ambiguous": "gross_salary"},
    {"id": "PL_24", "text": "Salary 14 LPA, rent 30k monthly, but don't know my city category.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_25", "text": "I earn 12 lakhs, pay 15,000 rent monthly without knowing if employer gives HRA.", "expected_complete": False, "missing_or_ambiguous": "hra_received"},
    {"id": "PL_26", "text": "Package 20 lakhs, paying 40k rent monthly in India.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_27", "text": "Invested 1.5L in ELSS and PPF. What is my tax rebate?", "expected_complete": False, "missing_or_ambiguous": "gross_salary"},
    {"id": "PL_28", "text": "Salary 9.5 LPA, rent 18k monthly.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_29", "text": "Mera 80C complete hai aur health insurance bhi hai. Salary 13 lakh.", "expected_complete": False, "missing_or_ambiguous": "80d_breakdown"},
    {"id": "PL_30", "text": "Gross 16 LPA. Paying rent 28k monthly.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_31", "text": "I earn 10 LPA. Paying 12k rent.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_32", "text": "Mera package 8 LPA hai. Tax kitna katega?", "expected_complete": True}, # Complete default
    {"id": "PL_33", "text": "Salary 15 LPA. Mediclaim 45,000 paid.", "expected_complete": False, "missing_or_ambiguous": "80d_breakdown"},
    {"id": "PL_34", "text": "Gross 18 LPA, paying 35k rent.", "expected_complete": False, "missing_or_ambiguous": "metro_status"},
    {"id": "PL_35", "text": "Medical insurance 40k paid for family, salary 12 LPA.", "expected_complete": False, "missing_or_ambiguous": "80d_breakdown"},

    # Contradictory & Ambiguous cases
    {"id": "PL_36", "text": "My package is 22 LPA and I invested 3.5 lakhs in Section 80C.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},
    {"id": "PL_37", "text": "Mera salary 16 lakh hai, 80C mein 2.5 lakh invest kiya hai LIC aur FD mein.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},
    {"id": "PL_38", "text": "I earn 15 LPA. Live with parents in Delhi, paying 30,000 rent to father.", "expected_complete": False, "ambiguity": "rent_to_parents"},
    {"id": "PL_39", "text": "Salary 18 LPA, 80C me 3 lakh dala hai tax bachane ke liye.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},
    {"id": "PL_40", "text": "Package 20 LPA, parents ke sath rehta hu aur 25k rent claim karna chahta hu.", "expected_complete": False, "ambiguity": "rent_to_parents"},
    {"id": "PL_41", "text": "Earn 14 lakhs, invested 4 lakhs under 80C mutual funds.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},
    {"id": "PL_42", "text": "CTC 28 LPA, live in my own owned apartment and paying 35k rent to myself.", "expected_complete": False, "ambiguity": "self_rent"},
    {"id": "PL_43", "text": "Salary 9 LPA, 80C 2,00,000 PPF.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},
    {"id": "PL_44", "text": "Mera package 11 lakh hai, living with parents but showing 20k rent receipt.", "expected_complete": False, "ambiguity": "rent_to_parents"},
    {"id": "PL_45", "text": "Gross 17 LPA, claiming 2.8 lakhs in 80C provident fund.", "expected_complete": False, "contradiction": "80c_cap_exceeded"},

    # Varied Colloquial & Hinglish Cases
    {"id": "PL_46", "text": "Bhai meri monthly in-hand nahi gross salary 1 lakh per month hai, age 28, Delhi me rehta hu, rent 20k per month, basic 50k, HRA 25k, 80C 1.5 lakh.", "expected_complete": True},
    {"id": "PL_47", "text": "Company se package mila 10.5 lakh ka. Kuch investment nahi kiya. Kitna tax lagega?", "expected_complete": True},
    {"id": "PL_48", "text": "I am 30 years old, working in Bangalore tech firm. CTC 24 LPA, basic 12L, rent 35,000 p.m., HRA 3.6L, 80C 1.5L, NPS 50k, health insurance 20k.", "expected_complete": True},
    {"id": "PL_49", "text": "Salaried guy here, 8 LPA package, age 26, completely zero tax deductions. Tell me new vs old regime.", "expected_complete": True},
    {"id": "PL_50", "text": "Earn 50 lakhs flat. What is my surcharge liability under old vs new regime?", "expected_complete": True}
]
