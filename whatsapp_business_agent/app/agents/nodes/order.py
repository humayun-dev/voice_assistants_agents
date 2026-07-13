from langchain_core.messages import SystemMessage
from app.llm import llm
from app.agents.state import AgentState
from app.services.supabase_client import get_catalog_text


def order_node(state: AgentState):
    catalog_text = get_catalog_text()
    system = SystemMessage(content=(
        f"You are a shop assistant collecting order details. Here is the real catalog — "
        f"only confirm orders for products that actually exist here, with the real price:\n\n{catalog_text}\n\n"
        "Politely ask for whatever is still missing from: product name, quantity, delivery "
        "address, contact confirmation. Once you have everything, confirm the order back to "
        "the customer clearly (including the total price) and thank them. "
        "Always reply in the SAME language the customer used — if they wrote or spoke in Urdu, "
        "reply in Urdu; if Pashto, reply in Pashto; if English, reply in English."
    ))
    response = llm.invoke([system] + state["messages"])
    return {"messages": [response]}
