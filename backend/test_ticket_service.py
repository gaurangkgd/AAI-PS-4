"""Unit tests for in-memory ticket service using unittest."""

import unittest

try:
    from backend.ticket_service import (
        clear_tickets,
        create_ticket,
        get_ticket,
        list_tickets,
    )
except ImportError:
    from ticket_service import (
        clear_tickets,
        create_ticket,
        get_ticket,
        list_tickets,
    )


class TestTicketService(unittest.TestCase):
    def setUp(self):
        clear_tickets()

    def tearDown(self):
        clear_tickets()

    def test_create_ticket_generates_unique_id(self):
        t1 = create_ticket(
            session_id="sess-1",
            original_message="Payment deducted for order ORD1004",
            category="payment_issue",
            escalation_reason="Payment failure",
            customer_id="CUST003",
            priority="urgent",
        )
        t2 = create_ticket(
            session_id="sess-2",
            original_message="Defective item received",
            category="return_or_replacement",
            escalation_reason="Damaged item",
        )

        self.assertTrue(t1["ticket_id"].startswith("TKT-"))
        self.assertTrue(t2["ticket_id"].startswith("TKT-"))
        self.assertNotEqual(t1["ticket_id"], t2["ticket_id"])
        self.assertEqual(t1["status"], "open")
        self.assertEqual(t1["priority"], "urgent")
        self.assertEqual(t1["customer_id"], "CUST003")
        self.assertIsNotNone(t1["created_at"])

    def test_get_ticket_found_and_not_found(self):
        created = create_ticket(
            session_id="sess-3",
            original_message="Help needed",
            category="general_inquiry",
            escalation_reason="Human escalation requested",
        )
        tid = created["ticket_id"]

        # Exact and case-insensitive retrieval
        retrieved = get_ticket(tid)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["ticket_id"], tid)
        self.assertEqual(get_ticket(tid.lower())["ticket_id"], tid)

        # Unknown ID
        self.assertIsNone(get_ticket("TKT-NONEXISTENT"))
        self.assertIsNone(get_ticket(""))

    def test_list_and_filter_tickets(self):
        create_ticket("s1", "m1", "payment_issue", "reason 1", priority="urgent", status="open")
        create_ticket("s2", "m2", "payment_issue", "reason 2", priority="high", status="in_progress")
        create_ticket("s3", "m3", "order_tracking", "reason 3", priority="low", status="open")

        all_tickets = list_tickets()
        self.assertEqual(len(all_tickets), 3)

        open_tickets = list_tickets(status="open")
        self.assertEqual(len(open_tickets), 2)

        payment_tickets = list_tickets(category="payment_issue")
        self.assertEqual(len(payment_tickets), 2)

        open_payment_tickets = list_tickets(status="open", category="payment_issue")
        self.assertEqual(len(open_payment_tickets), 1)

        empty_filter = list_tickets(category="nonexistent_category")
        self.assertEqual(len(empty_filter), 0)


if __name__ == "__main__":
    unittest.main()
