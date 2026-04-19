from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict

DocumentType = Literal[
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


class PageInfo(TypedDict):
    page_number: int
    text: str


class ClassifiedPage(TypedDict):
    page_number: int
    document_type: DocumentType
    confidence: float
    reason: str


class ItemizedLine(TypedDict):
    item: str
    quantity: float
    unit_price: float
    amount: float


class ClaimGraphState(TypedDict, total=False):
    claim_id: str
    filename: str
    page_texts: List[PageInfo]
    classification: List[ClassifiedPage]
    routed_pages: Dict[str, List[PageInfo]]

    id_data: Dict[str, Any]
    discharge_data: Dict[str, Any]
    bill_data: Dict[str, Any]

    final_response: Dict[str, Any]
