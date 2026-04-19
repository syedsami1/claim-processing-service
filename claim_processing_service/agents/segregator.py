from __future__ import annotations

from typing import Dict, List

from claim_processing_service.state import ClassifiedPage, ClaimGraphState, DocumentType, PageInfo

DOC_TYPES: List[DocumentType] = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other",
]


def _heuristic_classify(text: str) -> DocumentType:
    t = text.lower()
    if any(k in t for k in ["claim form", "claim no", "pre-auth", "intimation"]):
        return "claim_forms"
    if any(k in t for k in ["ifsc", "account no", "bank", "cancelled cheque"]):
        return "cheque_or_bank_details"
    if any(k in t for k in ["aadhaar", "passport", "pan", "identity", "policy holder", "patient name", "date of birth"]):
        return "identity_document"
    if any(k in t for k in ["itemized", "invoice", "qty", "unit price", "amount", "total", "bill details"]):
        return "itemized_bill"
    if any(k in t for k in ["discharge summary", "diagnosis", "admission date", "discharge date", "treatment"]):
        return "discharge_summary"
    if "prescription" in t:
        return "prescription"
    if any(k in t for k in ["lab report", "investigation", "test result", "radiology", "pathology"]):
        return "investigation_report"
    if any(k in t for k in ["cash receipt", "receipt no", "paid amount"]):
        return "cash_receipt"
    return "other"


def segregator_node(state: ClaimGraphState) -> ClaimGraphState:
    page_texts = state.get("page_texts", [])

    classification: List[ClassifiedPage] = []
    routed_pages: Dict[str, List[PageInfo]] = {
        "identity_document": [],
        "discharge_summary": [],
        "itemized_bill": [],
    }

    for page in page_texts:
        page_no = page["page_number"]
        doc_type = _heuristic_classify(page["text"])
        classified: ClassifiedPage = {
            "page_number": page_no,
            "document_type": doc_type,
            "confidence": 0.7,
            "reason": "local heuristic classifier",
        }

        classification.append(classified)

        if classified["document_type"] in routed_pages:
            routed_pages[classified["document_type"]].append(page)

    return {
        "classification": classification,
        "routed_pages": routed_pages,
    }
