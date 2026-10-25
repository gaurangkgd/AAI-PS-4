"""Tool registry for Agentic Customer Support System."""

try:
    from backend.tools.investigation import (
        lookup_order,
        lookup_payment,
        lookup_customer,
        search_knowledge_base,
        check_return_eligibility,
    )
    from backend.tools.actions import (
        cancel_order,
        request_return,
        initiate_refund,
    )
    from backend.tools.tickets import (
        create_support_ticket,
        update_ticket_status,
        search_tickets,
    )
    from backend.tools.metrics import (
        record_csat_rating,
        get_resolution_metrics,
    )
except ImportError:
    from tools.investigation import (
        lookup_order,
        lookup_payment,
        lookup_customer,
        search_knowledge_base,
        check_return_eligibility,
    )
    from tools.actions import (
        cancel_order,
        request_return,
        initiate_refund,
    )
    from tools.tickets import (
        create_support_ticket,
        update_ticket_status,
        search_tickets,
    )
    from tools.metrics import (
        record_csat_rating,
        get_resolution_metrics,
    )

__all__ = [
    "lookup_order",
    "lookup_payment",
    "lookup_customer",
    "search_knowledge_base",
    "check_return_eligibility",
    "cancel_order",
    "request_return",
    "initiate_refund",
    "create_support_ticket",
    "update_ticket_status",
    "search_tickets",
    "record_csat_rating",
    "get_resolution_metrics",
]
