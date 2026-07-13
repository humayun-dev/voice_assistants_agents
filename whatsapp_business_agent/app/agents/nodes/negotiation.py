from langchain_core.messages import SystemMessage
from app.llm import llm
from app.config import settings
from app.agents.state import AgentState
from app.services.supabase_client import get_catalog_text


def negotiation_node(state: AgentState):
    catalog_text = get_catalog_text()
    system = SystemMessage(content=(
        f"You are a shop assistant handling price negotiation. Here is the real catalog "
        f"with real prices — use these exact numbers, never invent a price:\n\n{catalog_text}\n\n"
        f"You may offer discounts up to {settings.MAX_DISCOUNT_PERCENT}% off the listed price, "
        "and no further. If the customer wants more than that, politely say you'll need to "
        "check with the owner rather than agreeing yourself. Keep it warm and human, not robotic. "
        "Always reply in the SAME language the customer used — if they wrote or spoke in Urdu, "
        "reply in Urdu; if Pashto, reply in Pashto; if English, reply in English."
    ))
    response = llm.invoke([system] + state["messages"])
    return {"messages": [response]}
