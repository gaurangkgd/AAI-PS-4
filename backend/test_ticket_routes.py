"""Unit tests for FastAPI ticket routes using unittest."""

import unittest
from fastapi import HTTPException

try:
    from backend.schemas import TicketCreate
    from backend.ticket_routes import create_new_ticket, get_all_tickets, retrieve_ticket
    from backend.ticket_service import clear_tickets
except ImportError:
    from schemas import TicketCreate
    from ticket_routes import create_new_ticket, get_all_tickets, retrieve_ticket
    from ticket_service import clear_tickets


class TestTicketRoutes(unittest.TestCase):
    def setUp(self):
        clear_tickets()

    def tearDown(self):
        clear_tickets()

    def test_create_and_retrieve_ticket_route(self):
        req = TicketCreate(
            session_id="sess-api-1",
            original_message="Payment failed for ORD1004",
            category="payment_issue",
            reason="Unresolved payment failure",
            customer_id="CUST003",
            priority="urgent",
            investigation_summary="Order ORD1004 is payment_failed",
        )
        created = create_new_ticket(req)
        self.assertTrue(created["ticket_id"].startswith("TKT-"))
        self.assertEqual(created["category"], "payment_issue")
        self.assertEqual(created["priority"], "urgent")

        # Retrieve through route
        retrieved = retrieve_ticket(created["ticket_id"])
        self.assertEqual(retrieved["ticket_id"], created["ticket_id"])
        self.assertEqual(retrieved["session_id"], "sess-api-1")

    def test_retrieve_unknown_ticket_raises_404(self):
        with self.assertRaises(HTTPException) as ctx:
            retrieve_ticket("TKT-UNKNOWN-999")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("not found", ctx.exception.detail.lower())

    def test_list_tickets_route_filtering(self):
        create_new_ticket(TicketCreate(session_id="s1", original_message="msg1", category="order_tracking", reason="r1"))
        create_new_ticket(TicketCreate(session_id="s2", original_message="msg2", category="payment_issue", reason="r2"))

        all_t = get_all_tickets(status=None, category=None)
        self.assertEqual(len(all_t), 2)

        order_t = get_all_tickets(status=None, category="order_tracking")
        self.assertEqual(len(order_t), 1)
        self.assertEqual(order_t[0]["category"], "order_tracking")


if __name__ == "__main__":
    unittest.main()
