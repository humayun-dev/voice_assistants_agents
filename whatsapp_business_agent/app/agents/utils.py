def extract_text(ai_message) -> str:
    """
    Newer langchain-core versions return AIMessage.content as a list of
    content blocks (e.g. [{'type': 'text', 'text': '...', 'extras': {...}}])
    instead of a plain string. This safely extracts the text either way.
    """
    content = ai_message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)
