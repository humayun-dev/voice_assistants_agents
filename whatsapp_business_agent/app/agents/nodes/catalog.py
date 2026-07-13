from langchain_core.messages import SystemMessage
from app.llm import llm
from app.agents.state import AgentState
from app.services.supabase_client import get_catalog_text


def catalog_node(state: AgentState):
    catalog_text = get_catalog_text()
    system = SystemMessage(content=(
        "You are a friendly shop assistant. Answer the customer's question using ONLY "
        f"this real product catalog — do not invent products:\n\n{catalog_text}\n\n"
        "Keep replies short and warm, like a real shop owner texting back. "
        "Always reply in the SAME language the customer used — if they wrote or "
        "spoke in Urdu, reply in Urdu; if Pashto, reply in Pashto; if English, reply in English."
    ))
    response = llm.invoke([system] + state["messages"])
    return {"messages": [response]}
