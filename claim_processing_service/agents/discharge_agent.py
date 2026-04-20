from __future__ import annotations

import re

from claim_processing_service.state import ClaimGraphState
from claim_processing_service.utils.nlp_utils import extract_dates, iso_date_or_raw


def _extract_field(text: str, pattern: str):
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def discharge_agent_node(state: ClaimGraphState) -> ClaimGraphState:
    pages = state.get("routed_pages", {}).get("discharge_summary", [])
    text = "\n".join(p.get("text", "") for p in pages)

    diagnosis = _extract_field(text, r"diagnosis\s*[:\-]\s*([^\n]+)")
    admit_date = _extract_field(text, r"(?:admit_date|admit(?:ted)?\s*date|admission\s*date)\s*[:\-]\s*([^\n]+)")
    discharge_date = _extract_field(text, r"(?:discharge_date|discharge\s*date)\s*[:\-]\s*([^\n]+)")
    physician = _extract_field(text, r"(?:physician|doctor|consultant)\s*[:\-]\s*([^\n]+)")

    if not (admit_date and discharge_date):
        dates = extract_dates(text)
        if dates:
            if not admit_date:
                admit_date = dates[0]
            if len(dates) > 1 and not discharge_date:
                discharge_date = dates[1]

    return {
        "discharge_data": {
            "source_pages": [p["page_number"] for p in pages],
            "medical": {
                "diagnosis": diagnosis,
                "admit_date": iso_date_or_raw(admit_date) if admit_date else None,
                "discharge_date": iso_date_or_raw(discharge_date) if discharge_date else None,
                "physician": physician,
            },
        }
    }
