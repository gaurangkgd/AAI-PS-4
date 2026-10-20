"""Knowledge Retrieval / Knowledge Base Agent.

The third specialized agent in the Agentic Customer Support System (PS-04).
Responsible for retrieving verified policy guidance and troubleshooting articles
from the approved local knowledge base using scored keyword/intent matching,
with optional LLM-assisted reranking when credentials are available, and deterministic
fallback when absent or unavailable. Strictly prevents hallucinated policies.
"""

import copy
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    from backend.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    from knowledge_base import KNOWLEDGE_BASE

logger = logging.getLogger(__name__)

# Validated knowledge base lookup index by ID for strict verification
KB_INDEX: Dict[str, Dict[str, Any]] = {entry["id"]: copy.deepcopy(entry) for entry in KNOWLEDGE_BASE}


class KnowledgeRetrievalResult(BaseModel):
    """Validated structured result from the Knowledge Retrieval Agent."""

    query: str = Field(
        ...,
        description="The original customer query text",
    )
    detected_intent: str = Field(
        ...,
        description="Detected intent category guiding the retrieval",
    )
    entries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Verified knowledge entries retrieved strictly from the approved knowledge base",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Unique source identifiers (e.g. 'KB-PAY-001') of the retrieved articles",
    )
    source_titles: List[str] = Field(
        default_factory=list,
        description="Titles of the retrieved knowledge base articles",
    )
    relevance_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Calculated relevance score for each retrieved article ID (range 0.0 to 1.0)",
    )
    has_sufficient_knowledge: bool = Field(
        default=False,
        description="True if one or more retrieved entries satisfy the relevance threshold",
    )
    explanation: str = Field(
        ...,
        description="Concise factual explanation of the retrieval findings and rationale",
    )
    retrieval_method: str = Field(
        ...,
        description="Retrieval method used: 'keyword_intent_scored' or 'keyword_intent_scored_with_gemini_rerank'",
    )


class LLMRerankOutput(BaseModel):
    """Structured output schema for optional LLM reranking of verified candidates."""

    selected_ids: List[str] = Field(
        default_factory=list,
        description="Ordered list of candidate IDs that are genuinely relevant to the query",
    )
    has_sufficient_knowledge: bool = Field(
        default=True,
        description="True if the candidates provide adequate guidance for the user's issue",
    )
    explanation: str = Field(
        default="",
        description="Brief justification for the selection and ordering",
    )


def score_knowledge_entries(
    message: str,
    intent: str,
) -> List[Tuple[float, Dict[str, Any]]]:
    """Score knowledge base entries against message and intent using deterministic matching.

    Scoring criteria:
    - Intent alignment: +15 points if entry intent matches the classified intent.
    - Curated keyword hit: +4 points per matched keyword with boundary check.
    - Significant title word hit: +2 points per match (words of 4+ characters).
    - Gibberish / irrelevant suppression: zero score if no text relevance exists.
    """
    if not message or not isinstance(message, str):
        return []

    text = message.lower().strip()
    if not text:
        return []

    scored_entries: List[Tuple[float, Dict[str, Any]]] = []

    for entry in KNOWLEDGE_BASE:
        score = 0
        entry_intent = entry.get("intent", "")
        entry_keywords = entry.get("keywords", [])
        entry_title = entry.get("title", "").lower()

        # 1. Intent alignment bonus
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
        title_hits = 0
        for word in title_words:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                title_hits += 1
                score += 2

        # 4. Filter general inquiries with zero keyword/title hits
        if entry_intent == "general_inquiry" and keyword_hits == 0 and score <= 15:
            if title_hits == 0:
                score = 0

        # 5. Suppress complete gibberish or zero-relevance queries
        if keyword_hits == 0 and title_hits == 0:
            score = 0

        if score > 0:
            scored_entries.append((float(score), copy.deepcopy(entry)))

    # Sort descending by score, tie-breaking deterministically by entry ID
    scored_entries.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    return scored_entries


class KnowledgeRetrievalAgent:
    """Specialized agent for retrieving and ranking verified knowledge base articles."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        llm: Optional[Any] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(temperature)))
        self._llm = llm
        self._structured_llm = None

    def _get_structured_llm(self) -> Optional[Any]:
        """Lazy-initialize structured output client if credentials are valid."""
        if self._llm is not None:
            if hasattr(self._llm, "with_structured_output"):
                return self._llm.with_structured_output(LLMRerankOutput)
            return self._llm

        if not self.api_key or self.api_key.strip() in {"", "your_gemini_api_key_here"}:
            return None

        if self._structured_llm is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                chat_model = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=self.temperature,
                )
                self._structured_llm = chat_model.with_structured_output(LLMRerankOutput)
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI for reranking: %s", e)
                return None

        return self._structured_llm

    def _rerank_with_llm(
        self,
        query: str,
        intent: str,
        candidates: List[Tuple[float, Dict[str, Any]]],
        top_k: int = 3,
    ) -> Optional[KnowledgeRetrievalResult]:
        """Attempt to rerank candidates using Gemini.

        Strict constraints:
        - Must choose strictly from candidate IDs; never hallucinates or adds new entries.
        - If LLM throws or fails schema validation, returns None to trigger deterministic fallback.
        """
        structured_llm = self._get_structured_llm()
        if structured_llm is None or not candidates:
            return None

        candidate_ids = [item[1]["id"] for item in candidates]
        candidate_excerpts = [
            f"ID: {item[1]['id']} | Title: {item[1]['title']} | Excerpt: {item[1]['guidance'][:180]}..."
            for item in candidates
        ]

        system_prompt = (
            "You are the Knowledge Reranking Specialist for an e-commerce support system.\n"
            "Your task is to review a list of candidate knowledge base articles retrieved by keyword matching "
            "and decide which ones best address the customer's inquiry.\n\n"
            "STRICT RULES:\n"
            "1. You may ONLY choose IDs that appear in the candidate list. Never invent new IDs or text.\n"
            "2. Order selected_ids from most relevant to least relevant.\n"
            "3. If none of the candidates adequately address the customer query, set has_sufficient_knowledge to false "
            "and leave selected_ids empty.\n"
            "4. Provide a brief, factual explanation for your selection."
        )

        user_content = (
            f"Customer Query: {query}\n"
            f"Detected Intent: {intent}\n\n"
            f"Candidate Articles:\n" + "\n".join(candidate_excerpts)
        )

        try:
            response: LLMRerankOutput = structured_llm.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ]
            )

            # Defensive verification: Ensure all selected IDs are genuinely in candidates
            valid_selected = [
                eid for eid in response.selected_ids if eid in candidate_ids and eid in KB_INDEX
            ]

            if not valid_selected or not response.has_sufficient_knowledge:
                return KnowledgeRetrievalResult(
                    query=query,
                    detected_intent=intent,
                    entries=[],
                    sources=[],
                    source_titles=[],
                    relevance_scores={},
                    has_sufficient_knowledge=False,
                    explanation=response.explanation or "LLM reranker determined candidates do not sufficiently address the inquiry.",
                    retrieval_method="keyword_intent_scored_with_gemini_rerank",
                )

            # Build final entries and calculate normalized scores
            selected_entries = [copy.deepcopy(KB_INDEX[eid]) for eid in valid_selected[:top_k]]
            sources = [e["id"] for e in selected_entries]
            titles = [e["title"] for e in selected_entries]

            # Assign decaying normalized scores (0.95 down to 0.70)
            scores = {}
            for idx, eid in enumerate(sources):
                score_val = max(0.60, round(0.95 - (idx * 0.10), 2))
                scores[eid] = score_val

            return KnowledgeRetrievalResult(
                query=query,
                detected_intent=intent,
                entries=selected_entries,
                sources=sources,
                source_titles=titles,
                relevance_scores=scores,
                has_sufficient_knowledge=True,
                explanation=response.explanation or f"Selected {len(selected_entries)} verified knowledge articles via Gemini reranking.",
                retrieval_method="keyword_intent_scored_with_gemini_rerank",
            )

        except Exception as e:
            logger.info("LLM reranking encountered an exception (%s); falling back to deterministic scoring.", e)
            return None

    def retrieve(
        self,
        query: str,
        intent: str,
        top_k: int = 3,
    ) -> KnowledgeRetrievalResult:
        """Retrieve relevant knowledge base articles for a query and intent.

        Uses deterministic keyword/intent scoring by default. When Gemini credentials
        are available, attempts candidate reranking while strictly preserving groundedness.
        """
        clean_query = (query or "").strip()
        clean_intent = (intent or "general_inquiry").strip()

        if not clean_query:
            return KnowledgeRetrievalResult(
                query=clean_query,
                detected_intent=clean_intent,
                entries=[],
                sources=[],
                source_titles=[],
                relevance_scores={},
                has_sufficient_knowledge=False,
                explanation="Empty or missing customer query; no knowledge retrieval performed.",
                retrieval_method="keyword_intent_scored",
            )

        scored_candidates = score_knowledge_entries(clean_query, clean_intent)

        if not scored_candidates:
            return KnowledgeRetrievalResult(
                query=clean_query,
                detected_intent=clean_intent,
                entries=[],
                sources=[],
                source_titles=[],
                relevance_scores={},
                has_sufficient_knowledge=False,
                explanation="No relevant knowledge base articles found matching query keywords or intent.",
                retrieval_method="keyword_intent_scored",
            )

        # Attempt optional LLM reranking if configured
        if self._get_structured_llm() is not None:
            llm_result = self._rerank_with_llm(
                query=clean_query,
                intent=clean_intent,
                candidates=scored_candidates[:5],
                top_k=top_k,
            )
            if llm_result is not None:
                return llm_result

        # Deterministic fallback scoring path
        top_entries = scored_candidates[:top_k]
        entries = [item[1] for item in top_entries]
        sources = [item[1]["id"] for item in top_entries]
        titles = [item[1]["title"] for item in top_entries]

        # Calculate normalized relevance scores (scale roughly 0.0 to 1.0)
        relevance_scores = {}
        for score, entry in top_entries:
            # Baseline score 15 + hits -> normalize to 0.0-1.0
            norm_score = round(min(1.0, max(0.1, score / 27.0)), 2)
            relevance_scores[entry["id"]] = norm_score

        explanation = (
            f"Retrieved {len(entries)} verified article(s) matching intent '{clean_intent}' "
            f"and keyword patterns (top source: {sources[0]} with score {relevance_scores.get(sources[0], 0.0)})."
        )

        return KnowledgeRetrievalResult(
            query=clean_query,
            detected_intent=clean_intent,
            entries=entries,
            sources=sources,
            source_titles=titles,
            relevance_scores=relevance_scores,
            has_sufficient_knowledge=True,
            explanation=explanation,
            retrieval_method="keyword_intent_scored",
        )


def retrieve_knowledge_context(
    message: str,
    intent: str,
    top_k: int = 3,
) -> KnowledgeRetrievalResult:
    """Convenience helper to retrieve knowledge using the KnowledgeRetrievalAgent."""
    agent = KnowledgeRetrievalAgent()
    return agent.retrieve(query=message, intent=intent, top_k=top_k)
