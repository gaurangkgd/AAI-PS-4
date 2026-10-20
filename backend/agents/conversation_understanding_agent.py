"""Conversation Understanding Agent.

The first specialized agent in the Agentic Customer Support System (PS-04).
Interprets customer messages using an LLM (Google Gemini via langchain-google-genai)
with validated structured output, providing deterministic rule-based fallback when
the API key is absent or when provider errors occur.
"""

import logging
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

try:
    from backend.intent_classifier import (
        classify_intent,
        ALL_INTENTS,
        INTENT_GENERAL_INQUIRY,
        INTENT_PAYMENT_ISSUE,
        INTENT_ORDER_TRACKING,
        INTENT_CANCELLATION,
        INTENT_RETURN_OR_REPLACEMENT,
        INTENT_REFUND_STATUS,
        INTENT_ACCOUNT_ISSUE,
        INTENT_PRODUCT_INQUIRY,
    )
except ImportError:
    from intent_classifier import (
        classify_intent,
        ALL_INTENTS,
        INTENT_GENERAL_INQUIRY,
        INTENT_PAYMENT_ISSUE,
        INTENT_ORDER_TRACKING,
        INTENT_CANCELLATION,
        INTENT_RETURN_OR_REPLACEMENT,
        INTENT_REFUND_STATUS,
        INTENT_ACCOUNT_ISSUE,
        INTENT_PRODUCT_INQUIRY,
    )

logger = logging.getLogger(__name__)

VALID_INTENTS = set(ALL_INTENTS)


class ConversationUnderstandingResult(BaseModel):
    """Validated structured output representing customer intent and sentiment."""

    intent: str = Field(
        ...,
        description="One of: payment_issue, order_tracking, cancellation, return_or_replacement, refund_status, account_issue, product_inquiry, general_inquiry",
    )
    category: str = Field(
        ...,
        description="Customer issue category (e.g. billing, logistics, order_management, returns, account, product, general)",
    )
    priority: str = Field(
        default="medium",
        description="Assessed issue priority: low, medium, high, urgent",
    )
    sentiment: str = Field(
        default="neutral",
        description="Detected customer sentiment: positive, neutral, negative, frustrated, urgent",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True if message is ambiguous, incomplete, or requires follow-up details",
    )
    explanation: str = Field(
        ...,
        description="Short factual explanation of classification rationale",
    )
    source: str = Field(
        default="llm",
        description="Origin indicator: 'llm' or 'rule_based_fallback'",
    )

    @field_validator("intent")
    @classmethod
    def validate_and_normalize_intent(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return INTENT_GENERAL_INQUIRY
        norm = v.strip().lower().replace("-", "_").replace(" ", "_")
        if norm in VALID_INTENTS:
            return norm
        # Map common aliases/variations
        if "cancel" in norm:
            return INTENT_CANCELLATION
        if "track" in norm or ("order" in norm and "status" in norm):
            return INTENT_ORDER_TRACKING
        if "pay" in norm or "bill" in norm or "card" in norm:
            return INTENT_PAYMENT_ISSUE
        if "return" in norm or "replace" in norm:
            return INTENT_RETURN_OR_REPLACEMENT
        if "refund" in norm:
            return INTENT_REFUND_STATUS
        if "account" in norm or "login" in norm:
            return INTENT_ACCOUNT_ISSUE
        if "product" in norm or "stock" in norm:
            return INTENT_PRODUCT_INQUIRY
        return INTENT_GENERAL_INQUIRY

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        valid_priorities = {"low", "medium", "high", "urgent"}
        if v and v.strip().lower() in valid_priorities:
            return v.strip().lower()
        return "medium"

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5


SYSTEM_PROMPT = """You are the Conversation Understanding Agent for an e-commerce support system.
Your role is to analyze customer messages and return a validated structured understanding.

Supported intent labels (YOU MUST MAP TO EXACTLY ONE OF THESE):
- payment_issue: Failed payments, duplicate charges, unexpected debits, card declines.
- order_tracking: Delivery status, parcel location, shipping delay, expected arrival.
- cancellation: Order cancellation, stopping processing orders, aborting delivery.
- return_or_replacement: Defective, damaged, or wrong items received; returns or replacements.
- refund_status: Status of processed refunds, refund timelines, reimbursement guarantees.
- account_issue: Login trouble, password reset, authentication or account lockout.
- product_inquiry: Stock availability, specifications, dimensions, features, compatibility, pricing.
- general_inquiry: General store questions, greetings, or inquiries not fitting above.

Handling compound and ambiguous messages:
- For compound requests (e.g. "My order is delayed and I want to cancel it"), prioritize the actionable customer goal (cancellation).
- For payment complaints on missing orders (e.g. "Money was debited but order didn't generate"), select payment_issue.
- If the customer request is vague, incomplete, or one word (e.g. "help", "order"), set needs_clarification=True.
- Provide a confidence score from 0.0 to 1.0 reflecting how clear the intent is.
- Assign appropriate priority: low, medium, high, or urgent.
- Classify customer sentiment: positive, neutral, negative, frustrated, or urgent.
- Provide a concise explanation justifying your classification.
"""


def rule_based_understanding(
    message: str,
    fallback_reason: str = "No API key configured",
) -> ConversationUnderstandingResult:
    """Deterministic fallback using existing rule-based intent classifier."""
    intent = classify_intent(message)

    category_map = {
        INTENT_PAYMENT_ISSUE: "billing",
        INTENT_ORDER_TRACKING: "logistics",
        INTENT_CANCELLATION: "order_management",
        INTENT_RETURN_OR_REPLACEMENT: "returns",
        INTENT_REFUND_STATUS: "billing",
        INTENT_ACCOUNT_ISSUE: "account",
        INTENT_PRODUCT_INQUIRY: "product",
        INTENT_GENERAL_INQUIRY: "general",
    }

    priority_map = {
        INTENT_PAYMENT_ISSUE: "high",
        INTENT_CANCELLATION: "medium",
        INTENT_RETURN_OR_REPLACEMENT: "medium",
        INTENT_ORDER_TRACKING: "low",
        INTENT_REFUND_STATUS: "medium",
        INTENT_ACCOUNT_ISSUE: "medium",
        INTENT_PRODUCT_INQUIRY: "low",
        INTENT_GENERAL_INQUIRY: "low",
    }

    msg_lower = (message or "").lower()
    if any(w in msg_lower for w in ["urgent", "immediately", "asap", "deducted twice", "failed", "stolen", "unacceptable"]):
        sentiment = "frustrated"
        priority = "urgent" if intent == INTENT_PAYMENT_ISSUE else "high"
    elif any(w in msg_lower for w in ["thank", "thanks", "great", "awesome", "hello", "hi"]):
        sentiment = "positive" if "thank" in msg_lower else "neutral"
        priority = priority_map.get(intent, "low")
    elif any(w in msg_lower for w in ["wrong", "damaged", "broken", "delayed", "not working", "decline"]):
        sentiment = "negative"
        priority = priority_map.get(intent, "medium")
    else:
        sentiment = "neutral"
        priority = priority_map.get(intent, "medium")

    needs_clarification = (intent == INTENT_GENERAL_INQUIRY) or len((message or "").strip().split()) <= 2

    return ConversationUnderstandingResult(
        intent=intent,
        category=category_map.get(intent, "general"),
        priority=priority,
        sentiment=sentiment,
        confidence=0.85 if intent != INTENT_GENERAL_INQUIRY else 0.50,
        needs_clarification=needs_clarification,
        explanation=f"Classified via deterministic rule-based keyword patterns ({fallback_reason}).",
        source="rule_based_fallback",
    )


class ConversationUnderstandingAgent:
    """Agent responsible for conversational intent classification and sentiment analysis."""

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
            # Allow pre-configured or injected LLM (e.g. for unit testing)
            if hasattr(self._llm, "with_structured_output"):
                return self._llm.with_structured_output(ConversationUnderstandingResult)
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
                self._structured_llm = chat_model.with_structured_output(ConversationUnderstandingResult)
            except Exception as e:
                logger.warning("Failed to initialize ChatGoogleGenerativeAI: %s", e)
                return None

        return self._structured_llm

    def understand(self, message: str) -> ConversationUnderstandingResult:
        """Analyze message intent and return validated structured understanding.

        Falls back seamlessly to deterministic rule-based understanding if:
        1. No LLM credentials are configured.
        2. LLM provider call times out or throws an error.
        3. Model produces invalid or non-parsable output.
        """
        if not message or not isinstance(message, str) or not message.strip():
            return rule_based_understanding("", fallback_reason="Empty message")

        structured_llm = self._get_structured_llm()

        if structured_llm is None:
            return rule_based_understanding(message, fallback_reason="No LLM API key configured")

        try:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.strip()},
            ]

            result = structured_llm.invoke(prompt)

            # If the model returned a validated Pydantic model directly
            if isinstance(result, ConversationUnderstandingResult):
                result.source = "llm"
                return result

            # If the model returned a dict matching the schema
            if isinstance(result, dict):
                result["source"] = "llm"
                return ConversationUnderstandingResult(**result)

            logger.warning("LLM returned unexpected type %s, falling back to rules.", type(result))
            return rule_based_understanding(message, fallback_reason="Unexpected model response format")

        except Exception as e:
            logger.warning("LLM execution failed (%s), falling back to rule-based classification.", e)
            return rule_based_understanding(message, fallback_reason=f"LLM provider error: {str(e)}")


# Singleton agent instance for application usage
_default_agent = ConversationUnderstandingAgent()


def understand_conversation(
    message: str,
    agent: Optional[ConversationUnderstandingAgent] = None,
) -> ConversationUnderstandingResult:
    """Convenience functional interface for conversation understanding."""
    active_agent = agent or _default_agent
    return active_agent.understand(message)
