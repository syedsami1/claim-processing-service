from __future__ import annotations

from claim_processing_service.state import ClaimGraphState


def aggregator_node(state: ClaimGraphState) -> ClaimGraphState:
    final = {
        "claim_id": state.get("claim_id"),
        "document_classification": state.get("classification", []),
        "identity_extraction": state.get("id_data", {}),
        "discharge_summary_extraction": state.get("discharge_data", {}),
        "itemized_bill_extraction": state.get("bill_data", {}),
    }

    return {"final_response": final}
