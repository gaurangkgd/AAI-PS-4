"""Multi-Turn Memory Agent.

The sixth specialized agent in the Agentic Customer Support System (PS-04).
Responsible for maintaining bounded, isolated conversational memory across turns
within a session. Resolves anaphoric references (e.g. 'it', 'that order'), tracks
active order IDs and recent intents, manages pending action confirmations with strict
guardrails, and clearly distinguishes unverified user claims from verified data.

Notice:
In-memory session storage resets when the server restarts and is not production-grade
persistent storage. Memory records do not confer authentication or ownership rights.
"""

import copy
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ORDER_ID_PATTERN = re.compile(r"\b(ORD\d{4,})\b", re.IGNORECASE)
CUSTOMER_ID_PATTERN = re.compile(r"\b(CUST\d{3,})\b", re.IGNORECASE)

REFERENCE_PRONOUN_PATTERNS = [
    re.compile(r"\b(that|this)\s+(order|package|shipment|item)\b", re.IGNORECASE),
    re.compile(r"\bthe\s+same\s+(order|issue|item)\b", re.IGNORECASE),
    re.compile(r"\b(cancel|return|replace|track|check|where\s+is|status\s+of)\s+it\b", re.IGNORECASE),
    re.compile(r"\b(it|its)\b", re.IGNORECASE),
]

AFFIRMATIVE_CONFIRM_PATTERN = re.compile(
    r"\b(yes|yeah|yep|sure|please\s+proceed|proceed|confirm|go\s+ahead|do\s+it|please\s+do|affirmative)\b",
    re.IGNORECASE,
)

NEGATIVE_CONFIRM_PATTERN = re.compile(
    r"\b(no|nope|don't|do\s+not|cancel\s+that|nevermind|never\s+mind|stop|abort)\b",
    re.IGNORECASE,
)

MAX_TURNS_PER_SESSION = 20
MAX_SESSIONS = 1000


class TurnRecord(BaseModel):
    """Immutable record of an individual conversational turn."""

    turn_index: int
    user_message: str
    assistant_message: str
    intent: Optional[str] = None
    order_id: Optional[str] = None
    decision: Optional[str] = None
    timestamp: str


class PendingConfirmation(BaseModel):
    """Specific action confirmation request awaiting explicit customer response."""

    action: str = Field(..., description="Action awaiting confirmation (e.g. 'cancellation')")
    order_id: str = Field(..., description="Target order ID for the action")
    request_type: Optional[str] = Field(default="return", description="e.g. 'return' or 'replacement'")
    reason: Optional[str] = None
    asked_at_turn: int
    is_pending: bool = True


class MemoryResolutionResult(BaseModel):
    """Validated output from memory resolution preceding workflow execution."""

    session_id: str
    resolved_order_id: Optional[str] = Field(
        default=None,
        description="Active order ID resolved from message or prior turn memory",
    )
    is_reference_resolved: bool = Field(
        default=False,
        description="True if anaphoric pronoun ('it', 'that order') was resolved to an active order",
    )
    reference_term: Optional[str] = Field(
        default=None,
        description="The pronoun or reference term detected in the user message",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if conflicting order mentions or unresolvable references occurred",
    )
    clarification_needed: bool = Field(
        default=False,
        description="True if downstream execution should ask for clarification rather than guess",
    )
    clarification_prompt: Optional[str] = Field(
        default=None,
        description="Suggested clarification prompt for the customer",
    )
    confirmed_action: Optional[str] = Field(
        default=None,
        description="Action authorized via explicit 'yes' confirmation matching pending request",
    )
    confirmed_order_id: Optional[str] = Field(
        default=None,
        description="Order ID authorized by explicit confirmation",
    )
    pending_confirmation_active: bool = Field(
        default=False,
        description="True if a confirmation request remains pending in memory",
    )
    recent_intents: List[str] = Field(
        default_factory=list,
        description="Chronological list of recent intents in this session",
    )
    turn_count: int = Field(
        default=0,
        description="Total turns recorded in this session",
    )
    summary: str = Field(
        ...,
        description="Concise factual summary of current session memory state",
    )


class SessionMemory(BaseModel):
    """Isolated, bounded memory representation for a single session."""

    session_id: str
    active_order_id: Optional[str] = None
    claimed_customer_id: Optional[str] = None
    is_authenticated: bool = False
    recent_intents: List[str] = Field(default_factory=list)
    unresolved_question: Optional[str] = None
    pending_confirmation: Optional[PendingConfirmation] = None
    turn_history: List[TurnRecord] = Field(default_factory=list)
    verified_order_facts: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


# In-memory storage dictionary: maps session_id to SessionMemory
_SESSION_STORE: Dict[str, SessionMemory] = {}


def clear_memory_store() -> None:
    """Clear all session memory records. Useful for testing and environment resets."""
    _SESSION_STORE.clear()


def reset_session_memory(session_id: str) -> None:
    """Reset memory for a specific session ID."""
    if session_id in _SESSION_STORE:
        del _SESSION_STORE[session_id]


class MultiTurnMemoryAgent:
    """Specialized agent for managing cross-turn conversational state and reference resolution."""

    def __init__(self, max_turns: int = MAX_TURNS_PER_SESSION, max_sessions: int = MAX_SESSIONS):
        self.max_turns = max_turns
        self.max_sessions = max_sessions

    def _get_or_create_session(self, session_id: str) -> SessionMemory:
        """Retrieve existing session memory or initialize a fresh bounded session."""
        clean_sid = (session_id or "").strip()
        if not clean_sid:
            clean_sid = "anonymous"

        if clean_sid not in _SESSION_STORE:
            # Enforce max sessions bound via FIFO eviction if needed
            if len(_SESSION_STORE) >= self.max_sessions:
                oldest_sid = next(iter(_SESSION_STORE))
                del _SESSION_STORE[oldest_sid]

            now_iso = datetime.now(timezone.utc).isoformat()
            _SESSION_STORE[clean_sid] = SessionMemory(
                session_id=clean_sid,
                created_at=now_iso,
                updated_at=now_iso,
            )

        return _SESSION_STORE[clean_sid]

    def extract_order_mentions(self, text: str) -> List[str]:
        """Extract all unique order IDs mentioned in the message."""
        if not text or not isinstance(text, str):
            return []
        matches = ORDER_ID_PATTERN.findall(text)
        return list(dict.fromkeys(m.upper() for m in matches))

    def extract_customer_mentions(self, text: str) -> List[str]:
        """Extract customer IDs claimed by the user in message."""
        if not text or not isinstance(text, str):
            return []
        matches = CUSTOMER_ID_PATTERN.findall(text)
        return list(dict.fromkeys(m.upper() for m in matches))

    def _detect_anaphoric_reference(self, text: str) -> Optional[str]:
        """Detect pronoun or anaphoric phrases referencing an earlier order."""
        if not text or not isinstance(text, str):
            return None
        for pattern in REFERENCE_PRONOUN_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    def resolve_memory(
        self,
        session_id: str,
        message: str,
    ) -> MemoryResolutionResult:
        """Resolve conversational references, pending confirmations, and active order context."""
        clean_msg = (message or "").strip()
        session = self._get_or_create_session(session_id)

        turn_count = len(session.turn_history)
        recent_intents = list(session.recent_intents)
        order_mentions = self.extract_order_mentions(clean_msg)
        ref_term = self._detect_anaphoric_reference(clean_msg)

        # 1. Check for conflicting order mentions in the current turn
        if len(order_mentions) > 1:
            return MemoryResolutionResult(
                session_id=session.session_id,
                resolved_order_id=None,
                is_reference_resolved=False,
                reference_term=None,
                is_ambiguous=True,
                clarification_needed=True,
                clarification_prompt=(
                    f"You referenced multiple orders ({', '.join(order_mentions)}). "
                    "Please specify which Order ID you would like to proceed with."
                ),
                confirmed_action=None,
                confirmed_order_id=None,
                pending_confirmation_active=bool(session.pending_confirmation and session.pending_confirmation.is_pending),
                recent_intents=recent_intents,
                turn_count=turn_count,
                summary=f"Conflicting orders {order_mentions} mentioned in message.",
            )

        # 2. Check pending confirmation handling
        confirmed_action = None
        confirmed_order_id = None
        is_pending_active = bool(session.pending_confirmation and session.pending_confirmation.is_pending)

        if is_pending_active:
            pending = session.pending_confirmation
            # Check if current turn is an affirmative confirmation
            if AFFIRMATIVE_CONFIRM_PATTERN.search(clean_msg):
                confirmed_action = pending.action
                confirmed_order_id = pending.order_id
                # Consume pending confirmation
                pending.is_pending = False
                session.pending_confirmation = None
            elif NEGATIVE_CONFIRM_PATTERN.search(clean_msg):
                # User declined or cancelled confirmation
                pending.is_pending = False
                session.pending_confirmation = None

        # If user said an affirmative confirmation but there is NO pending confirmation:
        elif AFFIRMATIVE_CONFIRM_PATTERN.search(clean_msg) and not self.extract_order_mentions(clean_msg):
            cleaned_words = [w for w in re.sub(r"[!.,?]", "", clean_msg.lower()).split() if w]
            standalone_words = {
                "yes", "yeah", "yep", "sure", "please", "proceed", "confirm", "ok", "okay",
                "affirmative", "do", "it", "ahead", "go", "thanks", "thank", "you"
            }
            if cleaned_words and all(w in standalone_words for w in cleaned_words):
                return MemoryResolutionResult(
                    session_id=session.session_id,
                    resolved_order_id=session.active_order_id,
                    is_reference_resolved=False,
                    reference_term=clean_msg,
                    is_ambiguous=True,
                    clarification_needed=True,
                    clarification_prompt="Could you please clarify what order or request you are confirming?",
                    confirmed_action=None,
                    confirmed_order_id=None,
                    pending_confirmation_active=False,
                    recent_intents=recent_intents,
                    turn_count=turn_count,
                    summary="Received affirmative confirmation with no pending confirmation request.",
                )

        # 3. Resolve target order ID
        resolved_order_id = None
        is_reference_resolved = False

        if len(order_mentions) == 1:
            # User explicitly named a specific order ID in this turn
            resolved_order_id = order_mentions[0]
            is_reference_resolved = False
        elif ref_term:
            # User used an anaphoric reference ('it', 'that order', 'same order')
            if session.active_order_id:
                resolved_order_id = session.active_order_id
                is_reference_resolved = True
            else:
                resolved_order_id = None
                is_reference_resolved = False
        else:
            # No explicit order ID and no pronoun reference
            # If confirmed_order_id exists, use it; otherwise retain active order as background context
            resolved_order_id = confirmed_order_id or session.active_order_id

        # Build concise summary
        summary_parts = []
        if resolved_order_id:
            src = "resolved from pronoun" if is_reference_resolved else "identified in message or active memory"
            summary_parts.append(f"Active order: {resolved_order_id} ({src})")
        else:
            summary_parts.append("No active order identified")

        if confirmed_action:
            summary_parts.append(f"Confirmed action: {confirmed_action} on {confirmed_order_id}")
        elif session.pending_confirmation and session.pending_confirmation.is_pending:
            summary_parts.append(f"Pending confirmation: {session.pending_confirmation.action} on {session.pending_confirmation.order_id}")

        summary_parts.append(f"Turns recorded: {turn_count}")

        return MemoryResolutionResult(
            session_id=session.session_id,
            resolved_order_id=resolved_order_id,
            is_reference_resolved=is_reference_resolved,
            reference_term=ref_term,
            is_ambiguous=False,
            clarification_needed=False,
            clarification_prompt=None,
            confirmed_action=confirmed_action,
            confirmed_order_id=confirmed_order_id,
            pending_confirmation_active=bool(session.pending_confirmation and session.pending_confirmation.is_pending),
            recent_intents=recent_intents,
            turn_count=turn_count,
            summary="; ".join(summary_parts) + ".",
        )

    def update_memory(
        self,
        session_id: str,
        user_message: str,
        final_state: Dict[str, Any],
    ) -> SessionMemory:
        """Update session memory after workflow completion using verified outputs."""
        session = self._get_or_create_session(session_id)
        clean_msg = (user_message or "").strip()

        # 1. Update active order ID if reliably extracted or investigated
        order_mentions = self.extract_order_mentions(clean_msg)
        if len(order_mentions) == 1:
            session.active_order_id = order_mentions[0]
        else:
            inv = final_state.get("investigation") or {}
            inv_order_id = inv.get("order_id")
            if inv_order_id and inv.get("status") == "found":
                session.active_order_id = inv_order_id

        # 2. Update claimed customer ID if mentioned in message
        customer_mentions = self.extract_customer_mentions(clean_msg)
        if len(customer_mentions) == 1:
            session.claimed_customer_id = customer_mentions[0]

        # 3. Update verified order facts if order was found
        inv = final_state.get("investigation") or {}
        if inv.get("status") == "found" and inv.get("order"):
            order_rec = inv["order"]
            session.verified_order_facts[order_rec.get("id")] = {
                "status": order_rec.get("status"),
                "total_amount": order_rec.get("total_amount"),
                "customer_id": order_rec.get("customer_id"),
            }

        # 4. Track recent intents (bounded to last 5)
        intent = final_state.get("intent")
        if intent:
            session.recent_intents.append(intent)
            if len(session.recent_intents) > 5:
                session.recent_intents = session.recent_intents[-5:]

        # 5. Check if action execution returned confirmation_required
        action_exec = final_state.get("action_execution") or {}
        if action_exec.get("status") == "confirmation_required":
            session.pending_confirmation = PendingConfirmation(
                action=action_exec.get("action", "unknown"),
                order_id=action_exec.get("order_id") or session.active_order_id or "unknown",
                asked_at_turn=len(session.turn_history) + 1,
                is_pending=True,
            )
        elif action_exec.get("status") in {"executed", "rejected", "failed"}:
            # Clear pending confirmation once executed, rejected, or failed
            session.pending_confirmation = None

        # 6. Record turn history (bounded to max_turns)
        turn_record = TurnRecord(
            turn_index=len(session.turn_history) + 1,
            user_message=clean_msg,
            assistant_message=final_state.get("assistant_message", ""),
            intent=intent,
            order_id=session.active_order_id,
            decision=final_state.get("decision"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        session.turn_history.append(turn_record)
        if len(session.turn_history) > self.max_turns:
            session.turn_history = session.turn_history[-self.max_turns :]

        session.updated_at = datetime.now(timezone.utc).isoformat()
        return session

    def get_memory_summary(self, session_id: str) -> Dict[str, Any]:
        """Return a structured dictionary snapshot of memory for downstream inspection."""
        clean_sid = (session_id or "").strip()
        if clean_sid not in _SESSION_STORE:
            return {
                "session_id": clean_sid,
                "turn_count": 0,
                "active_order_id": None,
                "has_pending_confirmation": False,
                "recent_intents": [],
                "summary": "No prior conversation memory in session.",
            }

        session = _SESSION_STORE[clean_sid]
        return {
            "session_id": session.session_id,
            "turn_count": len(session.turn_history),
            "active_order_id": session.active_order_id,
            "has_pending_confirmation": bool(session.pending_confirmation and session.pending_confirmation.is_pending),
            "recent_intents": list(session.recent_intents),
            "summary": (
                f"Session {session.session_id}: {len(session.turn_history)} turn(s); "
                f"Active order: {session.active_order_id or 'none'}."
            ),
        }


# Global memory agent instance
_MEMORY_AGENT = MultiTurnMemoryAgent()


def resolve_session_memory(session_id: str, message: str) -> MemoryResolutionResult:
    """Convenience helper to resolve memory for a session and message."""
    return _MEMORY_AGENT.resolve_memory(session_id, message)


def update_session_memory(session_id: str, user_message: str, final_state: Dict[str, Any]) -> SessionMemory:
    """Convenience helper to update memory after workflow completion."""
    return _MEMORY_AGENT.update_memory(session_id, user_message, final_state)


def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Convenience helper to retrieve memory summary for a session."""
    return _MEMORY_AGENT.get_memory_summary(session_id)
