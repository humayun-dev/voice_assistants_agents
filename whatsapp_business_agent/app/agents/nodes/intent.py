from typing import Literal
from langchain_core.messages import SystemMessage
from app.llm import llm
from app.agents.state import AgentState
from app.agents.utils import extract_text

INTENT_PROMPT = """Classify the customer's latest message into exactly one category.
Reply with ONLY one word, nothing else:

- catalog        (asking about products, prices, availability, general questions)
- negotiation     (asking for a discount, haggling, "can you do it cheaper")
- order           (ready to buy, confirming purchase, giving delivery details)
- escalation      (complaint, custom/bespoke request, angry tone, anything unclear or sensitive)
"""

VALID_INTENTS = {"catalog", "negotiation", "order", "escalation"}


def intent_node(state: AgentState):
    last_user_msg = state["messages"][-1]
    response = llm.invoke([SystemMessage(content=INTENT_PROMPT), last_user_msg])
    intent = extract_text(response).strip().lower()

    if intent not in VALID_INTENTS:
        intent = "escalation"  # safe default when the classifier is unsure

    print(f"[Intent Agent] classified as: {intent}")
    return {"intent": intent}


def route_from_intent(state: AgentState) -> Literal["catalog", "negotiation", "order", "escalation"]:
    return state["intent"]
