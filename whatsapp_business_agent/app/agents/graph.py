"""
Assembles the full multi-agent graph. This is the one place that wires
together the Intent Agent and its four specialists — if you ever add a new
agent (e.g. a Refund Agent), this is the only file you touch besides the
new node file itself.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes.intent import intent_node, route_from_intent
from app.agents.nodes.catalog import catalog_node
from app.agents.nodes.negotiation import negotiation_node
from app.agents.nodes.order import order_node
from app.agents.nodes.escalation import escalation_node

graph_builder = StateGraph(AgentState)

graph_builder.add_node("intent_agent", intent_node)
graph_builder.add_node("catalog", catalog_node)
graph_builder.add_node("negotiation", negotiation_node)
graph_builder.add_node("order", order_node)
graph_builder.add_node("escalation", escalation_node)

graph_builder.add_edge(START, "intent_agent")
graph_builder.add_conditional_edges(
    "intent_agent",
    route_from_intent,
    {
        "catalog": "catalog",
        "negotiation": "negotiation",
        "order": "order",
        "escalation": "escalation",
    },
)
graph_builder.add_edge("catalog", END)
graph_builder.add_edge("negotiation", END)
graph_builder.add_edge("order", END)
graph_builder.add_edge("escalation", END)

# NOTE: MemorySaver keeps conversation history in RAM only — it resets every
# time the server restarts. Swapping this for a Postgres checkpointer
# (backed by the same Supabase project) is the natural next upgrade.
checkpointer = MemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)
