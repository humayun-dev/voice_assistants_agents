import re
from langchain_core.messages import SystemMessage, AIMessage
from app.llm import llm
from app.agents.state import AgentState
from app.agents.utils import extract_text

# Anything matching this pattern means the LLM tried to promise something it's
# not allowed to (a discount, refund, replacement, specific amount, etc.).
# Prompts alone don't reliably stop this — under emotional pressure (e.g. a
# complaint), the model will often break an instruction like "don't promise
# a discount" if it feels helpful in the moment. So this is enforced in code,
# not just asked for in the prompt.
FORBIDDEN_PROMISE_PATTERN = re.compile(
    r"(\d+\s?%|discount|refund|replace(ment)?|free|rs\.?\s?\d+|rupees|voucher|compensat)",
    re.IGNORECASE,
)

SAFE_FALLBACK_LINE = "I'm really sorry to hear that — that's not the experience we want you to have."


def escalation_node(state: AgentState):
    last_msg = state["messages"][-1]
    last_user_msg = extract_text(last_msg) if hasattr(last_msg, "content") else str(last_msg)

    # In production this would WhatsApp-message the real owner's number.
    print(f"[OWNER ALERT] A conversation needs your attention. Latest message: {last_user_msg}")

    system = SystemMessage(content=(
        "You are a shop assistant acknowledging a customer's complaint or difficult request. "
        "Write ONE short, warm sentence acknowledging their concern with empathy. "
        "You are NOT authorized to offer or mention any discount, refund, replacement, "
        "free item, or specific resolution of any kind — you can only acknowledge and reassure. "
        "Reply in the SAME language the customer used — Urdu, Pashto, or English."
    ))
    response = llm.invoke([system] + state["messages"])
    empathy_line = extract_text(response)

    if FORBIDDEN_PROMISE_PATTERN.search(empathy_line):
        print("[Escalation Agent] LLM tried to make an unauthorized promise — using safe fallback instead.")
        empathy_line = SAFE_FALLBACK_LINE

    final_reply = (
        f"{empathy_line} I've let the shop owner know and they'll personally "
        "get back to you shortly to sort this out. 🙏"
    )
    return {"messages": [AIMessage(content=final_reply)]}
