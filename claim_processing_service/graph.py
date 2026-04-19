from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from claim_processing_service.agents.aggregator import aggregator_node
from claim_processing_service.agents.discharge_agent import discharge_agent_node
from claim_processing_service.agents.id_agent import id_agent_node
from claim_processing_service.agents.itemized_bill_agent import itemized_bill_agent_node
from claim_processing_service.agents.segregator import segregator_node
from claim_processing_service.state import ClaimGraphState


def build_claim_graph():
    graph = StateGraph(ClaimGraphState)

    graph.add_node("segregator", segregator_node)
    graph.add_node("id_agent", id_agent_node)
    graph.add_node("discharge_summary_agent", discharge_agent_node)
    graph.add_node("itemized_bill_agent", itemized_bill_agent_node)
    graph.add_node("aggregator", aggregator_node)

    graph.add_edge(START, "segregator")

    graph.add_edge("segregator", "id_agent")
    graph.add_edge("segregator", "discharge_summary_agent")
    graph.add_edge("segregator", "itemized_bill_agent")

    graph.add_edge("id_agent", "aggregator")
    graph.add_edge("discharge_summary_agent", "aggregator")
    graph.add_edge("itemized_bill_agent", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
