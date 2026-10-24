"""Resolution metrics, customer satisfaction (CSAT), and root-cause analytics tools."""

import json
from datetime import datetime, timezone
from typing import Optional
from langchain_core.tools import tool

try:
    from backend.mock_data import TICKETS, CSAT_RATINGS, PAYMENTS
except ImportError:
    from mock_data import TICKETS, CSAT_RATINGS, PAYMENTS


@tool
def record_csat_rating(
    ticket_id: str,
    customer_id: str,
    rating: int,
    feedback: Optional[str] = "",
) -> str:
    """Record customer satisfaction (CSAT) rating and qualitative feedback.

    Args:
        ticket_id: Associated ticket ID (e.g. 'TKT-D983F112') or 'general'.
        customer_id: The customer's ID (e.g. 'CUST001').
        rating: Integer score from 1 (very dissatisfied) to 5 (very satisfied).
        feedback: Optional qualitative comments from the customer.

    Returns:
        JSON string confirming recorded CSAT and updated satisfaction average.
    """
    try:
        score = int(rating)
        if score < 1 or score > 5:
            return json.dumps({"success": False, "message": "Rating must be an integer between 1 and 5."})
    except (ValueError, TypeError):
        return json.dumps({"success": False, "message": "Rating must be a numeric integer between 1 and 5."})

    entry = {
        "ticket_id": ticket_id.strip() if ticket_id else "general",
        "customer_id": customer_id.strip().upper() if customer_id else "ANONYMOUS",
        "rating": score,
        "feedback": feedback or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    CSAT_RATINGS.append(entry)

    all_scores = [c["rating"] for c in CSAT_RATINGS]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else score

    return json.dumps({
        "success": True,
        "recorded_rating": score,
        "total_reviews": len(CSAT_RATINGS),
        "system_avg_csat": round(avg_score, 2),
        "message": f"Thank you! Your rating of {score}/5 has been recorded."
    })


@tool
def get_resolution_metrics() -> str:
    """Compute live support operations metrics, SLA health, CSAT scores, and root cause anomaly alerts.

    Computes:
    - Total tickets, open, in_progress, and resolved counts
    - Auto-resolution vs human escalation percentage
    - Average customer satisfaction score (CSAT)
    - Root-cause outage detection (e.g., spikes in payment failures)
    - SLA deadline risk counts

    Returns:
        JSON string with operations statistics for supervisor monitoring.
    """
    total = len(TICKETS)
    open_count = sum(1 for t in TICKETS if t.get("status") == "open")
    in_progress_count = sum(1 for t in TICKETS if t.get("status") in {"assigned", "in_progress", "pending_customer"})
    resolved_count = sum(1 for t in TICKETS if t.get("status") in {"resolved", "closed"})

    resolution_rate = round((resolved_count / total * 100), 1) if total > 0 else 0.0
    escalation_rate = round(((open_count + in_progress_count) / total * 100), 1) if total > 0 else 0.0

    # CSAT analytics
    csat_scores = [c["rating"] for c in CSAT_RATINGS if isinstance(c.get("rating"), (int, float))]
    avg_csat = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else 5.0
    csat_distribution = {
        "5_star": sum(1 for s in csat_scores if s == 5),
        "4_star": sum(1 for s in csat_scores if s == 4),
        "3_star": sum(1 for s in csat_scores if s == 3),
        "2_star": sum(1 for s in csat_scores if s == 2),
        "1_star": sum(1 for s in csat_scores if s == 1),
    }

    # Root Cause Discovery: detect anomaly in payment failures or courier delays
    payment_issue_tickets = sum(1 for t in TICKETS if t.get("category") == "payment_issue")
    failed_payments = sum(1 for p in PAYMENTS if p.get("status") == "failed")

    anomalies = []
    if payment_issue_tickets >= 1 or failed_payments >= 1:
        anomalies.append({
            "type": "PAYMENT_GATEWAY_ANOMALY",
            "severity": "HIGH",
            "description": f"Detected {failed_payments} failed payment transactions and {payment_issue_tickets} billing escalation tickets. Possible merchant gateway timeout or bank reconciliation outage.",
            "recommended_action": "Check Stripe / Razorpay webhook logs and enable secondary fallback payment gateway.",
        })

    # SLA health
    now_iso = datetime.now(timezone.utc).isoformat()
    sla_breaches = sum(
        1 for t in TICKETS
        if t.get("status") in {"open", "in_progress"} and t.get("sla_deadline") and t.get("sla_deadline") < now_iso
    )

    metrics = {
        "total_tickets": total,
        "open_tickets": open_count,
        "in_progress_tickets": in_progress_count,
        "resolved_tickets": resolved_count,
        "resolution_rate_percent": resolution_rate,
        "escalation_rate_percent": escalation_rate,
        "average_csat": avg_csat,
        "csat_review_count": len(csat_scores),
        "csat_distribution": csat_distribution,
        "sla_breach_count": sla_breaches,
        "root_cause_alerts": anomalies,
    }

    return json.dumps(metrics)
