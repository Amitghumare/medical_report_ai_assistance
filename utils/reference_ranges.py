"""
Reference ranges for common lab tests.
Each entry: test_name -> {aliases, unit, low, high, gender_specific(optional)}

Ranges are general adult reference ranges for demonstration purposes only.
They are NOT a substitute for professional medical interpretation.
"""

REFERENCE_RANGES = {
    "Hemoglobin": {
        "aliases": ["hemoglobin", "hgb", "hb"],
        "unit": "g/dL",
        "male": (13.5, 17.5),
        "female": (12.0, 15.5),
        "default": (12.0, 17.5),
    },
    "Blood Sugar (Fasting)": {
        "aliases": ["fasting blood sugar", "fbs", "glucose fasting", "blood sugar", "glucose"],
        "unit": "mg/dL",
        "default": (70, 100),
    },
    "Cholesterol (Total)": {
        "aliases": ["total cholesterol", "cholesterol", "cholesterol total"],
        "unit": "mg/dL",
        "default": (0, 200),
    },
    "LDL Cholesterol": {
        "aliases": ["ldl", "ldl cholesterol", "ldl-c"],
        "unit": "mg/dL",
        "default": (0, 100),
    },
    "HDL Cholesterol": {
        "aliases": ["hdl", "hdl cholesterol", "hdl-c"],
        "unit": "mg/dL",
        "default": (40, 60),
    },
    "Triglycerides": {
        "aliases": ["triglycerides", "tg"],
        "unit": "mg/dL",
        "default": (0, 150),
    },
    "Vitamin D": {
        "aliases": ["vitamin d", "vitamin d3", "25-oh vitamin d", "25-hydroxy vitamin d"],
        "unit": "ng/mL",
        "default": (30, 100),
    },
    "Vitamin B12": {
        "aliases": ["vitamin b12", "b12", "cobalamin"],
        "unit": "pg/mL",
        "default": (200, 900),
    },
    "TSH": {
        "aliases": ["tsh", "thyroid stimulating hormone"],
        "unit": "uIU/mL",
        "default": (0.4, 4.0),
    },
    "Creatinine": {
        "aliases": ["creatinine", "s. creatinine", "serum creatinine"],
        "unit": "mg/dL",
        "male": (0.7, 1.3),
        "female": (0.6, 1.1),
        "default": (0.6, 1.3),
    },
    "WBC Count": {
        "aliases": ["wbc", "white blood cell", "white blood cells", "wbc count", "total leukocyte count", "tlc"],
        "unit": "/uL",
        "default": (4000, 11000),
    },
    "Platelet Count": {
        "aliases": ["platelet", "platelet count", "platelets"],
        "unit": "/uL",
        "default": (150000, 450000),
    },
    "HbA1c": {
        "aliases": ["hba1c", "glycated hemoglobin", "a1c"],
        "unit": "%",
        "default": (4.0, 5.6),
    },
    "Blood Pressure (Systolic)": {
        "aliases": ["systolic", "bp systolic"],
        "unit": "mmHg",
        "default": (90, 120),
    },
    "Blood Pressure (Diastolic)": {
        "aliases": ["diastolic", "bp diastolic"],
        "unit": "mmHg",
        "default": (60, 80),
    },
}


def get_range(test_name: str, gender: str = None):
    """Return (low, high) reference range for a given canonical test name."""
    entry = REFERENCE_RANGES.get(test_name)
    if not entry:
        return None
    if gender:
        gender = gender.strip().lower()
        if gender in ("male", "m") and "male" in entry:
            return entry["male"]
        if gender in ("female", "f") and "female" in entry:
            return entry["female"]
    return entry.get("default")
