"""Human-in-the-loop (HITL) policy rules shared by the deterministic graph and the action tools.

The thresholds (return window days, high-value order limit) are read from the live knowledge
base, so a supervisor editing a policy on the Supervisor Desk changes the AI's behaviour at once.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from backend.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    from knowledge_base import KNOWLEDGE_BASE

DEFAULT_RETURN_WINDOW_DAYS = 30
DEFAULT_HIGH_VALUE_THRESHOLD = 200.0


def get_policy(policy_id: str) -> Optional[Dict[str, Any]]:
    return next((p for p in KNOWLEDGE_BASE if p.get("id", "").upper() == policy_id.upper()), None)


def get_return_window_days() -> int:
    """Day count written in the 'Return Window Policy' (KB-RET-003)."""
    policy = get_policy("KB-RET-003")
    match = re.search(r"(\d+)\s*-?\s*day", (policy or {}).get("guidance", ""), re.IGNORECASE)
    return int(match.group(1)) if match else DEFAULT_RETURN_WINDOW_DAYS


def get_high_value_threshold() -> float:
    """Dollar limit written in the high-value manager-approval policy (KB-HR-005)."""
    policy = get_policy("KB-HR-005")
    match = re.search(r"\$\s?(\d[\d,]*(?:\.\d+)?)", (policy or {}).get("guidance", ""))
    return float(match.group(1).replace(",", "")) if match else DEFAULT_HIGH_VALUE_THRESHOLD


def days_since(iso_timestamp: Optional[str]) -> Optional[int]:
    if not iso_timestamp:
        return None
    try:
        moment = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - moment).days


# ---------------------------------------------------------------------------
# Order-based review rules (cancellations and returns)
# ---------------------------------------------------------------------------

def cancel_review(order: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Return a human-review descriptor if cancelling this order needs approval."""
    total = float(order.get("total_amount") or 0.0)
    limit = get_high_value_threshold()
    if total >= limit:
        return {
            "policy_ref": "KB-HR-005",
            "category": "high_value_approval",
            "team": "senior_support",
            "priority": "high",
            "reason": (
                f"Cancellation of high-value order {order.get('id')} (${total:.2f}) is at or above the "
                f"${limit:.0f} auto-approval limit and needs manager approval."
            ),
        }
    return None


def return_review(order: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Return a human-review descriptor if a return for this order needs approval."""
    window = get_return_window_days()
    age = days_since(order.get("delivered_at") or order.get("created_at"))
    if age is not None and age > window:
        return {
            "policy_ref": "KB-HR-006",
            "category": "return_exception",
            "team": "senior_support",
            "priority": "medium",
            "reason": (
                f"Order {order.get('id')} was delivered {age} days ago, outside the {window}-day return "
                "window. A return would be an exception that needs specialist approval."
            ),
        }
    total = float(order.get("total_amount") or 0.0)
    limit = get_high_value_threshold()
    if total >= limit:
        return {
            "policy_ref": "KB-HR-005",
            "category": "high_value_approval",
            "team": "senior_support",
            "priority": "high",
            "reason": (
                f"Return of high-value order {order.get('id')} (${total:.2f}) is at or above the "
                f"${limit:.0f} auto-approval limit and needs manager approval."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Message-based review rules, evaluated in order (most serious first)
# ---------------------------------------------------------------------------

HUMAN_REVIEW_RULES = [
    {
        "id": "safety_or_legal",
        "pattern": re.compile(
            r"\b(caught\s+fire|on\s+fire|smoke|smoking|overheat\w*|burn(ed|t|ing)?|explo(de|ded|sion)|"
            r"electric\s+shock|injur\w*|lawyer|attorney|legal\s+action|lawsuit|consumer\s+court|police)\b",
            re.IGNORECASE,
        ),
        "category": "safety_or_legal",
        "team": "senior_support",
        "priority": "urgent",
        "policy_ref": "KB-HR-007",
        "reason": "Customer reports a safety hazard or legal issue. Policy requires immediate human review.",
    },
    {
        "id": "fraud",
        "pattern": re.compile(
            r"\b(fraud\w*|unauthori[sz]ed|hacked|stolen\s+card|scam\w*|not\s+me|"
            r"(did\s*n'?t|did\s+not)\s+(make|authori[sz]e|place|order)|someone\s+else\s+(used|ordered))\b",
            re.IGNORECASE,
        ),
        "category": "fraud_dispute",
        "team": "senior_support",
        "priority": "urgent",
        "policy_ref": "KB-HR-003",
        "reason": "Customer reports a suspected fraudulent or unauthorized transaction. Self-service actions are blocked.",
    },
    {
        "id": "duplicate_charge",
        "pattern": re.compile(
            r"\b(charged\s+twice|billed\s+twice|paid\s+twice|(deducted|debited)\s+twice|"
            r"double[\s-]*(charge[d]?|deduct\w*|debit\w*)|duplicate\s+(charge|payment|transaction))\b",
            re.IGNORECASE,
        ),
        "category": "payment_issue",
        "team": "billing_support",
        "priority": "high",
        "policy_ref": "KB-HR-002",
        "reason": "Customer reports a duplicate charge. Billing must verify settlement and approve any reversal.",
    },
    {
        "id": "missing_refund",
        "pattern": re.compile(
            r"(?=.*\brefund\b)(?=.*(not\s+(yet\s+)?(been\s+)?(received|credited|arrived)|haven'?t\s+(received|got)|"
            r"still\s+waiting|\bmissing\b|where\s+is\s+my\s+refund|no\s+refund|refund\s+delayed|delayed\s+refund))",
            re.IGNORECASE | re.DOTALL,
        ),
        "category": "refund_dispute",
        "team": "billing_support",
        "priority": "high",
        "policy_ref": "KB-HR-008",
        "reason": "Customer reports a missing or delayed refund. Billing must trace it with the bank.",
    },
    {
        "id": "delivery_dispute",
        "pattern": re.compile(
            r"\b(never\s+(received|got|arrived)|not\s+(yet\s+)?(been\s+)?(received|arrived)|haven'?t\s+(received|got)|"
            r"(didn'?t|did\s+not)\s+(receive|get|arrive)|lost\s+(package|parcel|order|shipment)|"
            r"missing\s+(package|parcel|shipment)|(package|parcel)\s+(is\s+)?(lost|missing|stolen))\b",
            re.IGNORECASE,
        ),
        "category": "delivery_dispute",
        "team": "logistics_support",
        "priority": "high",
        "policy_ref": "KB-HR-004",
        "reason": "Customer reports a package marked delivered/shipped that they have not received. Logistics must investigate with the courier.",
    },
]

POLICY_QUESTION_MARKERS = ("policy", "how to", "what is", "rules", "faq", "terms", "tell me about")


def detect_human_review_trigger(message: str) -> Optional[Dict[str, str]]:
    """Return the first matching human-review rule for a customer message, or None."""
    if not message:
        return None
    lower = message.lower()
    is_policy_question = any(marker in lower for marker in POLICY_QUESTION_MARKERS)
    for rule in HUMAN_REVIEW_RULES:
        if rule["pattern"].search(message):
            # Informational questions ("what is your refund policy?") should be answered, not escalated,
            # except for safety and fraud reports which always go to a human.
            if is_policy_question and rule["id"] not in {"safety_or_legal", "fraud"}:
                continue
            return rule
    return None


def kb_has_relevant_match(message: str) -> bool:
    """True when at least one knowledge-base keyword appears in the message as a whole word or phrase."""
    lower = (message or "").lower()
    for entry in KNOWLEDGE_BASE:
        for keyword in entry.get("keywords", []):
            if len(keyword) >= 3 and re.search(r"\b" + re.escape(keyword.lower()) + r"\b", lower):
                return True
    return False
