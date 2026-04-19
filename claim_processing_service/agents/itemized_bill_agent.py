from __future__ import annotations

from typing import List

from claim_processing_service.state import ClaimGraphState, ItemizedLine
from claim_processing_service.utils.pdf_utils import extract_tables_by_page, parse_amount


def _from_tables(tables: List[List[List[str]]]) -> List[ItemizedLine]:
    lines: List[ItemizedLine] = []
    for table in tables:
        for row in table:
            if not row:
                continue
            raw = [c.strip() for c in row if c is not None]
            if len(raw) < 2:
                continue

            item = raw[0]
            amount = parse_amount(raw[-1])
            qty = 1.0
            unit_price = amount

            if len(raw) >= 3:
                parsed_qty = parse_amount(raw[1])
                parsed_unit = parse_amount(raw[2]) if len(raw) > 3 else 0.0
                if parsed_qty > 0:
                    qty = parsed_qty
                if parsed_unit > 0:
                    unit_price = parsed_unit

            if amount <= 0 and qty > 0 and unit_price > 0:
                amount = qty * unit_price

            if item and amount > 0:
                lines.append(
                    {
                        "item": item,
                        "quantity": round(qty, 2),
                        "unit_price": round(unit_price, 2),
                        "amount": round(amount, 2),
                    }
                )
    return lines


def itemized_bill_agent_node(state: ClaimGraphState) -> ClaimGraphState:
    pages = state.get("routed_pages", {}).get("itemized_bill", [])
    source_pages = [p["page_number"] for p in pages]

    all_lines: List[ItemizedLine] = []
    pdf_path = state.get("filename")
    if pdf_path:
        tables_by_page = extract_tables_by_page(pdf_path)
        for page_no in source_pages:
            page_tables = tables_by_page.get(page_no, [])
            if page_tables:
                all_lines.extend(_from_tables(page_tables))

    total_amount = round(sum(line["amount"] for line in all_lines), 2)

    return {
        "bill_data": {
            "source_pages": source_pages,
            "itemized_lines": all_lines,
            "total_amount": total_amount,
            "currency": "INR",
        }
    }
