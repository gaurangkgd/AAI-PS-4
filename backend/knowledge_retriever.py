"""Support knowledge retrieval service using standard library keyword and intent matching."""

import re
from typing import Any, Dict, List

try:
    from backend.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    from knowledge_base import KNOWLEDGE_BASE


def retrieve_knowledge(
    message: str,
    intent: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Retrieve and rank the most relevant support knowledge base entries.

    Args:
        message: The customer's message text.
        intent: The detected intent category.
        top_k: Maximum number of entries to return (default: 3).

    Returns:
        A list of top_k knowledge entries ranked by relevance, or an empty list
        if no relevant entries are found.
    """
    if not message or not isinstance(message, str):
        return []

    text = message.lower().strip()
    if not text:
        return []

    scored_entries = []

    for entry in KNOWLEDGE_BASE:
        score = 0
        entry_intent = entry.get("intent", "")
        entry_keywords = entry.get("keywords", [])
        entry_title = entry.get("title", "").lower()

        # 1. Intent alignment bonus: strong priority when aligned with classified intent
        if entry_intent == intent:
            score += 15

        # 2. Match curated keywords
        keyword_hits = 0
        for kw in entry_keywords:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, text) or kw.lower() in text:
                keyword_hits += 1
                score += 4

        # 3. Match significant words in title
        title_words = [
            word
            for word in re.findall(r"\b[a-z]{4,}\b", entry_title)
            if word not in {"with", "your", "from", "that", "this", "have"}
        ]
        for word in title_words:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                score += 2

        # If the entry has zero keyword/title hits and is general_inquiry, do not score
        if entry_intent == "general_inquiry" and keyword_hits == 0 and score <= 15:
            # Check if any actual general keyword hit occurred
            title_hits = any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in title_words)
            if not title_hits and keyword_hits == 0:
                score = 0

        # Discard entries with no textual relevance unless their specific intent was directly matched
        # But if the message was completely gibberish (0 total hits across title and keywords), do not return anything
        if keyword_hits == 0 and not any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in title_words):
            score = 0

        if score > 0:
            scored_entries.append((score, entry))

    # Rank by score descending, then by ID for deterministic tie-breaking
    scored_entries.sort(key=lambda item: (-item[0], item[1].get("id", "")))

    return [item[1] for item in scored_entries[:top_k]]
