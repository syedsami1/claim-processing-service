from __future__ import annotations

import re
from typing import Dict, List

import fitz  # PyMuPDF
import pdfplumber

from claim_processing_service.state import PageInfo


def extract_page_texts(pdf_path: str) -> List[PageInfo]:
    pages: List[PageInfo] = []
    doc = fitz.open(pdf_path)
    try:
        for page_index in range(len(doc)):
            text = doc[page_index].get_text("text") or ""
            pages.append({"page_number": page_index + 1, "text": text})
    finally:
        doc.close()
    return pages


def extract_tables_by_page(pdf_path: str) -> Dict[int, List[List[List[str]]]]:
    """Return tables grouped by 1-based page number."""
    tables_by_page: Dict[int, List[List[List[str]]]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            raw_tables = page.extract_tables() or []
            cleaned: List[List[List[str]]] = []
            for table in raw_tables:
                table_rows: List[List[str]] = []
                for row in table:
                    normalized = [((cell or "").strip()) for cell in row]
                    if any(normalized):
                        table_rows.append(normalized)
                if table_rows:
                    cleaned.append(table_rows)
            if cleaned:
                tables_by_page[idx] = cleaned
    return tables_by_page


_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def parse_amount(value: str) -> float:
    if not value:
        return 0.0
    match = _NUMBER_RE.search(value.replace("₹", "").replace("Rs.", ""))
    if not match:
        return 0.0
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return 0.0
