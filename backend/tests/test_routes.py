"""API endpoint integration tests."""

import unittest
from fastapi.testclient import TestClient

from backend.mock_data import reset_mock_data
from backend.main import app


class TestAPIRoutes(unittest.TestCase):

    def setUp(self):
        reset_mock_data()
        self.client = TestClient(app)

    def tearDown(self):
        reset_mock_data()

    def test_root_and_health(self):
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertEqual(r_root.json()["framework"], "LangGraph")

        r_health = self.client.get("/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "healthy")

    def test_chat_order_tracking(self):
        r = self.client.post("/chat", json={"message": "Where is my order ORD1001?"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["intent"], "order_tracking")
        self.assertEqual(data["decision"], "order_found")
        self.assertIn("delivered", data["assistant_message"])

    def test_chat_payment_escalation(self):
        r = self.client.post("/chat", json={"message": "My payment failed for order ORD1004 but funds were deducted!"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["decision"], "escalated")
        self.assertIsNotNone(data["ticket"])
        self.assertEqual(data["ticket"]["category"], "payment_issue")

    def test_admin_metrics(self):
        r = self.client.get("/admin/metrics")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_tickets", data)
        self.assertIn("resolution_rate_percent", data)
        self.assertIn("average_csat", data)
        self.assertIn("root_cause_alerts", data)

    def test_admin_tickets_and_status_update(self):
        r_list = self.client.get("/admin/tickets")
        self.assertEqual(r_list.status_code, 200)
        tickets = r_list.json()
        self.assertGreaterEqual(len(tickets), 1)

        first_tid = tickets[0]["ticket_id"]
        r_patch = self.client.patch(
            f"/admin/tickets/{first_tid}/status",
            json={
                "new_status": "in_progress",
                "assigned_to": "agent_jordan",
                "notes": "Reviewing transaction traces",
            },
        )
        self.assertEqual(r_patch.status_code, 200)
        self.assertTrue(r_patch.json()["success"])
        self.assertEqual(r_patch.json()["new_status"], "in_progress")

    def test_csat_submission(self):
        r = self.client.post(
            "/admin/csat",
            json={
                "ticket_id": "TKT-B401A912",
                "customer_id": "CUST003",
                "rating": 5,
                "feedback": "Agent was super helpful!",
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["recorded_rating"], 5)

    def test_order_cancellation_endpoint(self):
        r = self.client.post("/orders/ORD1002/cancel", json={"reason": "Test cancel"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["order"]["status"], "cancelled")

    def test_order_return_endpoint(self):
        r = self.client.post("/orders/ORD1001/return", json={"request_type": "return", "reason": "Defective"})
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertIn("RET-", data["return_request"]["request_id"])

    def test_checkout_creates_order_and_reduces_stock(self):
        before = self.client.get("/products/PROD004").json()["stock"]
        r = self.client.post(
            "/checkout",
            json={
                "customer_id": "CUST999",
                "items": [{"product_id": "PROD004", "quantity": 2}],
                "payment_method": "upi",
            },
        )
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["order"]["status"], "processing")
        self.assertEqual(data["order"]["total_amount"], 49.9)
        after = self.client.get("/products/PROD004").json()["stock"]
        self.assertEqual(after, before - 2)

    def test_take_and_resolve_case_notifies_customer(self):
        ticket_id = "TKT-B401A912"
        r_take = self.client.post(f"/admin/tickets/{ticket_id}/take", json={"agent_name": "agent_test"})
        self.assertEqual(r_take.status_code, 200)

        r_blank = self.client.post(f"/admin/tickets/{ticket_id}/resolve", json={"resolution_message": "   "})
        self.assertEqual(r_blank.status_code, 400)

        r_resolve = self.client.post(
            f"/admin/tickets/{ticket_id}/resolve",
            json={"resolution_message": "Refund approved.", "agent_name": "agent_test"},
        )
        self.assertEqual(r_resolve.status_code, 200)

        inbox = self.client.get("/customers/CUST003/notifications").json()
        self.assertTrue(
            any(n["type"] == "ticket_resolved" and n["message"] == "Refund approved." for n in inbox["notifications"])
        )


if __name__ == "__main__":
    unittest.main()
