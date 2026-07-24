"""
Step 3: Analyze Health Metrics
Parses raw OCR/extracted text to find patient info and lab test values,
then compares each value against reference ranges to flag normal/abnormal.
"""

import re
import pandas as pd

from utils.reference_ranges import REFERENCE_RANGES, get_range

# Matches a number, optionally with a decimal point (handles OCR spacing too)
NUMBER_PATTERN = r"([-+]?\d+(?:\.\d+)?)"


def extract_patient_info(text: str) -> dict:
    """Best-effort extraction of patient ID, name, age, and gender."""
    info = {"patient_id": None, "name": None, "age": None, "gender": None}

    patterns = {
        "patient_id": r"(?:patient\s*id|id\s*no\.?|mrn)\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        "name": r"(?:patient\s*name|name)\s*[:\-]?\s*([A-Za-z][A-Za-z\.\s]{2,40})",
        "age": r"age\s*[:\-]?\s*(\d{1,3})",
        "gender": r"(?:gender|sex)\s*[:\-]?\s*(male|female|m|f)\b",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if key == "name":
                value = value.splitlines()[0].strip()
            info[key] = value

    return info


def _build_alias_lookup():
    """Map every alias string -> canonical test name, longest alias first."""
    lookup = []
    for canonical, meta in REFERENCE_RANGES.items():
        for alias in meta["aliases"]:
            lookup.append((alias, canonical))
    # Longest alias first so "total cholesterol" matches before "cholesterol"
    lookup.sort(key=lambda x: len(x[0]), reverse=True)
    return lookup


ALIAS_LOOKUP = _build_alias_lookup()


def extract_lab_values(text: str) -> list:
    """
    Scan text line by line, and for each line, check if it mentions a known
    lab test alias followed (or preceded) by a numeric value. Returns a list
    of dicts: {test, value, unit}.
    """
    found = []
    seen_tests = set()
    lines = text.splitlines()

    for line in lines:
        line_lower = line.lower()
        for alias, canonical in ALIAS_LOOKUP:
            if canonical in seen_tests:
                continue
            if alias in line_lower:
                # Look for a number anywhere in this line
                num_match = re.search(NUMBER_PATTERN, line)
                if num_match:
                    value = float(num_match.group(1))
                    unit = REFERENCE_RANGES[canonical]["unit"]
                    found.append(
                        {"test": canonical, "value": value, "unit": unit}
                    )
                    seen_tests.add(canonical)
                    break  # move to next line once matched

    return found


def _analyze_report_uncached(text: str) -> dict:
    """
    Full analysis pipeline: extracts patient info + lab values, and
    determines normal/abnormal status for each value found.
    Returns a dict with patient_info, results (list), and a DataFrame.
    """
    patient_info = extract_patient_info(text)
    raw_values = extract_lab_values(text)

    results = []
    for item in raw_values:
        test = item["test"]
        value = item["value"]
        unit = item["unit"]
        rng = get_range(test, patient_info.get("gender"))

        if rng:
            low, high = rng
            if value < low:
                status = "Low"
            elif value > high:
                status = "High"
            else:
                status = "Normal"
            range_str = f"{low} - {high}"
        else:
            status = "Unknown"
            range_str = "N/A"

        results.append(
            {
                "Test": test,
                "Value": value,
                "Unit": unit,
                "Reference Range": range_str,
                "Status": status,
            }
        )

    df = pd.DataFrame(results) if results else pd.DataFrame(
        columns=["Test", "Value", "Unit", "Reference Range", "Status"]
    )

    return {
        "patient_info": patient_info,
        "results": results,
        "dataframe": df,
    }


try:
    import streamlit as st

    analyze_report = st.cache_data(show_spinner=False)(_analyze_report_uncached)
except ImportError:  # allows running analyzer logic outside streamlit (tests)
    analyze_report = _analyze_report_uncached
