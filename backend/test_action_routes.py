"""Unit tests for FastAPI action routes using unittest."""

import unittest
from fastapi import HTTPException

try:
    from backend.schemas import CancelOrderRequest, ReturnRequestCreate
    from backend.action_routes import cancel_order_endpoint, return_order_endpoint
    from backend.action_service import clear_action_data
except ImportError:
    from schemas import CancelOrderRequest, ReturnRequestCreate
    from action_routes import cancel_order_endpoint, return_order_endpoint
    from action_service import clear_action_data


class TestActionRoutes(unittest.TestCase):
    def setUp(self):
        clear_action_data()

    def tearDown(self):
        clear_action_data()

    def test_cancel_order_route_success(self):
        req = CancelOrderRequest(reason="Customer requested")
        res = cancel_order_endpoint("ORD1002", req)
        self.assertTrue(res["success"])
        self.assertEqual(res["order"]["status"], "cancelled")

    def test_cancel_order_route_ineligible_400(self):
        with self.assertRaises(HTTPException) as ctx:
            cancel_order_endpoint("ORD1001", None)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already been delivered", ctx.exception.detail)

    def test_cancel_order_route_not_found_404(self):
        with self.assertRaises(HTTPException) as ctx:
            cancel_order_endpoint("ORD9999", None)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("was not found", ctx.exception.detail)

    def test_return_order_route_success_201(self):
        req = ReturnRequestCreate(request_type="return", reason="Defective product")
        res = return_order_endpoint("ORD1001", req)
        self.assertTrue(res["success"])
        self.assertTrue(res["return_request"]["request_id"].startswith("RET-"))

    def test_return_order_route_ineligible_400(self):
        # ORD1002 is processing
        req = ReturnRequestCreate(request_type="return")
        with self.assertRaises(HTTPException) as ctx:
            return_order_endpoint("ORD1002", req)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("only permitted for 'delivered' orders", ctx.exception.detail)

    def test_return_order_route_not_found_404(self):
        with self.assertRaises(HTTPException) as ctx:
            return_order_endpoint("ORD9999", None)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("was not found", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
