from __future__ import annotations

import re
from typing import Dict

from claim_processing_service.state import ClaimGraphState
from claim_processing_service.utils.nlp_utils import extract_dates, extract_person_candidates, iso_date_or_raw, key_value_extract


ID_FIELD_PATTERNS = {
    "patient_name": [
        r"patient_name\s*[:\-]\s*([^\n]+)",
        r"patient\s*name\s*[:\-]\s*([^\n]+)",
        r"name\s*[:\-]\s*([^\n]+)",
    ],
    "dob": [
        r"dob\s*[:\-]\s*([^\n]+)",
        r"(?:date\s*of\s*birth|dob)\s*[:\-]\s*([^\n]+)",
    ],
    "policy_number": [
        r"policy_number\s*[:\-]\s*([^\n]+)",
        r"policy\s*(?:no|number)\s*[:\-]\s*([A-Z0-9\-/]+)",
    ],
    "member_id": [
        r"member_id\s*[:\-]\s*([^\n]+)",
        r"member\s*(?:id|number)\s*[:\-]\s*([A-Z0-9\-/]+)",
    ],
    "id_number": [
        r"id_number\s*[:\-]\s*([^\n]+)",
        r"id\s*(?:no|number)?\s*[:\-]\s*([^\n]+)",
        r"(?:aadhaar|aadhar|pan|passport)\s*(?:no|number)?\s*[:\-]\s*([A-Z0-9\-/]+)",
    ],
}


def id_agent_node(state: ClaimGraphState) -> ClaimGraphState:
    pages = state.get("routed_pages", {}).get("identity_document", [])
    text = "\n".join(p.get("text", "") for p in pages)

    extracted = key_value_extract(text, ID_FIELD_PATTERNS)

    person_candidates = extract_person_candidates(text)
    if not extracted.get("patient_name") and person_candidates:
        extracted["patient_name"] = person_candidates[0]

    dob = extracted.get("dob")
    if dob:
        extracted["dob"] = iso_date_or_raw(dob)
    else:
        dates = extract_dates(text)
        if dates:
            extracted["dob"] = iso_date_or_raw(dates[0])

    # Extract likely policy provider if available.
    insurer_match = re.search(
        r"(?:insurance_provider|insurer|insurance\s*company)\s*[:\-]\s*([^\n]+)",
        text,
        re.IGNORECASE,
    )
    insurer = insurer_match.group(1).strip() if insurer_match else None

    return {
        "id_data": {
            "source_pages": [p["page_number"] for p in pages],
            "identity": {
                **extracted,
                "insurance_provider": insurer,
            },
        }
    }
