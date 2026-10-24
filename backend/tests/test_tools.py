"""Unit tests for LangGraph support tools."""

import json
import unittest

from backend.mock_data import reset_mock_data
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


class TestSupportTools(unittest.TestCase):

    def setUp(self):
        reset_mock_data()

    def tearDown(self):
        reset_mock_data()

    def test_lookup_order_found(self):
        raw = lookup_order.invoke({"order_id": "ORD1001"})
        data = json.loads(raw)
        self.assertTrue(data["found"])
        self.assertEqual(data["order_id"], "ORD1001")
        self.assertEqual(data["status"], "delivered")

    def test_lookup_order_not_found(self):
        raw = lookup_order.invoke({"order_id": "ORD9999"})
        data = json.loads(raw)
        self.assertFalse(data["found"])
        self.assertIn("not found", data["message"])

    def test_lookup_payment_found(self):
        raw = lookup_payment.invoke({"order_id": "ORD1001"})
        data = json.loads(raw)
        self.assertTrue(data["has_payments"])
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["payments"][0]["status"], "successful")

    def test_lookup_customer(self):
        raw = lookup_customer.invoke({"customer_id": "CUST001"})
        data = json.loads(raw)
        self.assertTrue(data["found"])
        self.assertEqual(data["tier"], "premium")
        self.assertIn("ORD1001", data["order_ids"])

    def test_search_knowledge_base(self):
        raw = search_knowledge_base.invoke({"query": "how do I cancel an order?", "category": "cancellation"})
        data = json.loads(raw)
        self.assertGreaterEqual(data["matched_count"], 1)
        self.assertIn("Cancel", data["articles"][0]["title"])

    def test_check_return_eligibility_delivered(self):
        raw = check_return_eligibility.invoke({"order_id": "ORD1001"})
        data = json.loads(raw)
        self.assertTrue(data["is_eligible"])
        self.assertEqual(data["current_status"], "delivered")

    def test_check_return_eligibility_processing_rejected(self):
        raw = check_return_eligibility.invoke({"order_id": "ORD1002"})
        data = json.loads(raw)
        self.assertFalse(data["is_eligible"])
        self.assertIn("processing", data["reason"])

    def test_cancel_order_success(self):
        raw = cancel_order.invoke({"order_id": "ORD1002", "reason": "Customer changed mind"})
        data = json.loads(raw)
        self.assertTrue(data["success"])
        self.assertEqual(data["new_status"], "cancelled")

    def test_cancel_order_delivered_rejected(self):
        raw = cancel_order.invoke({"order_id": "ORD1001"})
        data = json.loads(raw)
        self.assertFalse(data["success"])
        self.assertIn("delivered", data["message"])

    def test_cancel_order_shipped_rejected(self):
        raw = cancel_order.invoke({"order_id": "ORD1003"})
        data = json.loads(raw)
        self.assertFalse(data["success"])
        self.assertIn("shipped", data["message"])

    def test_request_return_success(self):
        raw = request_return.invoke({"order_id": "ORD1001", "request_type": "return", "reason": "wrong item"})
        data = json.loads(raw)
        self.assertTrue(data["success"])
        self.assertTrue(data["request_id"].startswith("RET-"))
        self.assertIn("UPS Ground", data["return_label"]["carrier"])

    def test_request_return_duplicate_rejected(self):
        request_return.invoke({"order_id": "ORD1001", "request_type": "return"})
        raw2 = request_return.invoke({"order_id": "ORD1001", "request_type": "replacement"})
        data2 = json.loads(raw2)
        self.assertFalse(data2["success"])
        self.assertIn("already exists", data2["message"])

    def test_initiate_refund(self):
        cancel_order.invoke({"order_id": "ORD1002"})
        raw = initiate_refund.invoke({"order_id": "ORD1002", "reason": "Cancelled order"})
        data = json.loads(raw)
        self.assertTrue(data["success"])
        self.assertTrue(data["refund_id"].startswith("RFD-"))
        self.assertEqual(data["amount"], 49.90)

    def test_create_and_update_ticket(self):
        raw_create = create_support_ticket.invoke({
            "title": "Payment Investigation",
            "category": "payment_issue",
            "priority": "high",
            "escalation_reason": "Deduction on failed order",
            "customer_id": "CUST003",
            "order_id": "ORD1004",
            "target_team": "billing_support",
        })
        tkt = json.loads(raw_create)
        self.assertTrue(tkt["success"])
        tid = tkt["ticket_id"]

        # Lifecycle update: open -> in_progress -> resolved
        raw_update = update_ticket_status.invoke({
            "ticket_id": tid,
            "new_status": "in_progress",
            "assigned_to": "agent_sarah",
            "notes": "Checking gateway logs",
        })
        updated = json.loads(raw_update)
        self.assertTrue(updated["success"])
        self.assertEqual(updated["new_status"], "in_progress")

    def test_csat_and_resolution_metrics(self):
        raw_csat = record_csat_rating.invoke({
            "ticket_id": "TKT-B401A912",
            "customer_id": "CUST003",
            "rating": 5,
            "feedback": "Super fast escalation!",
        })
        csat_res = json.loads(raw_csat)
        self.assertTrue(csat_res["success"])

        raw_metrics = get_resolution_metrics.invoke({})
        metrics = json.loads(raw_metrics)
        self.assertGreaterEqual(metrics["total_tickets"], 3)
        self.assertIn("root_cause_alerts", metrics)
        self.assertGreater(metrics["average_csat"], 0)


if __name__ == "__main__":
    unittest.main()
