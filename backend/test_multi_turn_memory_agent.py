"""Unit and integration tests for the Multi-Turn Memory Agent.

Covers:
- Remembering an order ID across turns
- Resolving unambiguous follow-up references ('it', 'that order')
- Switching to an explicitly named new order
- Asking for clarification on conflicting order references
- Isolating memories between session IDs
- Unknown and empty session IDs handling
- Bounded history and session cleanup/reset
- Pending confirmation tied to a specific action and order
- Refusing ambiguous or unsolicited confirmations
- Declining pending confirmations ('no')
- Revalidating live ownership and eligibility before execution
- Memory update after workflow outputs
- API contract compatibility
"""

import copy
import unittest

from backend.mock_data import ORDERS, reset_mock_data
from backend.ticket_service import clear_tickets
from backend.agents.multi_turn_memory_agent import (
    MultiTurnMemoryAgent,
    MemoryResolutionResult,
    SessionMemory,
    resolve_session_memory,
    update_session_memory,
    get_session_summary,
    clear_memory_store,
    reset_session_memory,
    MAX_TURNS_PER_SESSION,
)
from backend.support_workflow import run_support_workflow
from backend.schemas import ChatResponse


class TestMultiTurnMemoryAgent(unittest.TestCase):
    """Test suite for Multi-Turn Memory Agent."""

    def setUp(self):
        clear_tickets()
        reset_mock_data()
        clear_memory_store()
        self.agent = MultiTurnMemoryAgent()

    def tearDown(self):
        clear_tickets()
        reset_mock_data()
        clear_memory_store()

    def test_remember_order_id_across_turns(self):
        """Turn 1 mentions ORD1001; Turn 2 follow-up reuses ORD1001 seamlessly."""
        session_id = "test-session-remember-001"

        # Turn 1: Mention ORD1001
        res1 = run_support_workflow("Where is my order ORD1001?", session_id=session_id)
        self.assertEqual(res1["session_id"], session_id)
        self.assertEqual(res1["decision"], "order_found")
        self.assertIn("ORD1001", res1["investigation"]["order_id"])

        mem1 = get_session_summary(session_id)
        self.assertEqual(mem1["active_order_id"], "ORD1001")
        self.assertEqual(mem1["turn_count"], 1)

        # Turn 2: Follow-up question using pronoun "Where is it?"
        res2 = run_support_workflow("Where is it?", session_id=session_id)
        self.assertEqual(res2["decision"], "order_found")
        self.assertEqual(res2["investigation"]["order_id"], "ORD1001")
        self.assertIn("delivered", res2["assistant_message"].lower())

        mem2 = get_session_summary(session_id)
        self.assertEqual(mem2["turn_count"], 2)
        self.assertEqual(mem2["active_order_id"], "ORD1001")

    def test_resolve_unambiguous_follow_up_reference(self):
        """Resolves 'that order' and 'same order' to active order in session."""
        session_id = "test-session-ref-002"

        # Initialize session with ORD1001
        run_support_workflow("I am checking order ORD1001", session_id=session_id)

        # Check resolution directly
        res = self.agent.resolve_memory(session_id, "What is the delivery estimate for that order?")
        self.assertIsInstance(res, MemoryResolutionResult)
        self.assertEqual(res.resolved_order_id, "ORD1001")
        self.assertTrue(res.is_reference_resolved)
        self.assertFalse(res.is_ambiguous)
        self.assertFalse(res.clarification_needed)

    def test_switch_to_explicitly_named_new_order(self):
        """Explicit new order ID replaces prior active order ID in session."""
        session_id = "test-session-switch-003"

        # Turn 1: ORD1001
        run_support_workflow("Where is ORD1001?", session_id=session_id)
        self.assertEqual(get_session_summary(session_id)["active_order_id"], "ORD1001")

        # Turn 2: Explicitly switch to ORD1003
        res2 = run_support_workflow("Check ORD1003 instead", session_id=session_id)
        self.assertEqual(res2["decision"], "order_found")
        self.assertEqual(res2["investigation"]["order_id"], "ORD1003")
        self.assertEqual(get_session_summary(session_id)["active_order_id"], "ORD1003")

        # Turn 3: "Where is it?" now refers to ORD1003
        res3 = run_support_workflow("Where is it?", session_id=session_id)
        self.assertEqual(res3["investigation"]["order_id"], "ORD1003")

    def test_conflicting_order_references_prompts_clarification(self):
        """When multiple order IDs are provided in a single turn, prompt for clarification."""
        session_id = "test-session-conflict-004"

        res = run_support_workflow("Can you check ORD1001 and ORD1002?", session_id=session_id)
        self.assertEqual(res["decision"], "memory_clarification_required")
        self.assertIn("multiple orders", res["assistant_message"].lower())
        self.assertIn("ORD1001", res["assistant_message"])
        self.assertIn("ORD1002", res["assistant_message"])

    def test_session_isolation(self):
        """Session A's active order never leaks to Session B."""
        session_a = "session-alpha"
        session_b = "session-beta"

        # Session A asks about ORD1001
        run_support_workflow("Where is ORD1001?", session_id=session_a)
        self.assertEqual(get_session_summary(session_a)["active_order_id"], "ORD1001")

        # Session B has no prior memory
        self.assertIsNone(get_session_summary(session_b)["active_order_id"])

        # Session B asking "Where is my order?" cannot resolve to ORD1001
        res_b = run_support_workflow("Where is my order?", session_id=session_b)
        self.assertEqual(res_b["decision"], "order_id_required")
        self.assertIn("provide your Order ID", res_b["assistant_message"])

    def test_unknown_and_empty_session_id(self):
        """Unknown or empty session IDs are handled gracefully and safely."""
        # Empty string session_id allocates a fresh UUID
        res_empty = run_support_workflow("Where is ORD1001?", session_id="")
        self.assertTrue(len(res_empty["session_id"]) > 0)
        self.assertNotEqual(res_empty["session_id"], "")

        # None session_id allocates a fresh UUID
        res_none = run_support_workflow("Where is ORD1001?", session_id=None)
        self.assertTrue(len(res_none["session_id"]) > 0)

        # Non-existent session summary returns clean empty structure
        summary = get_session_summary("non-existent-session-xyz")
        self.assertEqual(summary["turn_count"], 0)
        self.assertIsNone(summary["active_order_id"])
        self.assertFalse(summary["has_pending_confirmation"])

    def test_bounded_history_and_reset(self):
        """Memory respects maximum turn bounds and cleanup/reset functions."""
        session_id = "test-session-bounds-005"
        agent = MultiTurnMemoryAgent(max_turns=3)

        # Simulate 5 turns
        for i in range(5):
            agent.update_memory(
                session_id=session_id,
                user_message=f"Message {i}",
                final_state={"assistant_message": f"Reply {i}", "intent": "general_inquiry"},
            )

        summary = agent.get_memory_summary(session_id)
        # History bounded to max_turns=3
        self.assertEqual(summary["turn_count"], 3)

        # Reset specific session
        reset_session_memory(session_id)
        self.assertEqual(get_session_summary(session_id)["turn_count"], 0)

        # Clear store resets everything
        clear_memory_store()
        self.assertEqual(len(MultiTurnMemoryAgent().get_memory_summary("any")["recent_intents"]), 0)

    def test_pending_confirmation_tied_to_specific_action_and_order(self):
        """Affirmative confirmation authorizes execution only when pending confirmation matches."""
        session_id = "test-session-confirm-006"

        # Turn 1: Inquire about cancelling ORD1002 (processing order)
        res1 = run_support_workflow("Can I cancel order ORD1002?", session_id=session_id)
        self.assertEqual(res1["decision"], "confirmation_required")
        self.assertEqual(res1["action_execution"]["status"], "confirmation_required")
        self.assertIn("confirm", res1["assistant_message"].lower())

        mem1 = get_session_summary(session_id)
        self.assertTrue(mem1["has_pending_confirmation"])

        # Turn 2: Customer confirms: "Yes please proceed"
        res2 = run_support_workflow("Yes please proceed", session_id=session_id)
        self.assertEqual(res2["decision"], "action_completed")
        self.assertEqual(res2["action_execution"]["status"], "executed")
        self.assertTrue(res2["action_execution"]["mutation_performed"])

        # Live order data was updated to cancelled
        target_order = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(target_order["status"], "cancelled")

        # Pending confirmation is now cleared
        mem2 = get_session_summary(session_id)
        self.assertFalse(mem2["has_pending_confirmation"])

    def test_unsolicited_affirmative_confirmation_refused(self):
        """Saying 'yes' with no pending confirmation prompts for clarification without executing."""
        session_id = "test-session-unsolicited-007"

        res = run_support_workflow("Yes please", session_id=session_id)
        self.assertEqual(res["decision"], "memory_clarification_required")
        self.assertIn("clarify", res["assistant_message"].lower())
        self.assertIsNone(res["action_result"])

    def test_declining_pending_confirmation(self):
        """Saying 'no' dismisses pending confirmation without modifying order."""
        session_id = "test-session-decline-008"

        # Turn 1: Request confirmation
        run_support_workflow("Can I cancel order ORD1002?", session_id=session_id)
        self.assertTrue(get_session_summary(session_id)["has_pending_confirmation"])

        # Turn 2: Decline confirmation
        res2 = run_support_workflow("No, don't do that", session_id=session_id)
        self.assertFalse(get_session_summary(session_id)["has_pending_confirmation"])

        # Order status remains processing
        target_order = next(o for o in ORDERS if o["id"] == "ORD1002")
        self.assertEqual(target_order["status"], "processing")

    def test_revalidating_eligibility_before_execution(self):
        """Action execution revalidates live eligibility at execution time."""
        session_id = "test-session-revalidate-009"

        # ORD1001 is 'delivered' and cannot be cancelled
        res = run_support_workflow("Please cancel order ORD1001", session_id=session_id)
        self.assertEqual(res["decision"], "action_rejected")
        self.assertEqual(res["action_execution"]["status"], "rejected")
        self.assertIn("already been delivered", res["assistant_message"])

    def test_memory_update_after_workflow_outputs(self):
        """Workflow outputs attach memory summary to response and update verified records."""
        session_id = "test-session-outputs-010"

        res = run_support_workflow("Where is my order ORD1001?", session_id=session_id)
        self.assertIn("memory", res)
        mem = res["memory"]
        self.assertIsNotNone(mem)
        self.assertEqual(mem["session_id"], session_id)
        self.assertEqual(mem["active_order_id"], "ORD1001")
        self.assertEqual(mem["turn_count"], 1)
        self.assertIn("order_tracking", mem["recent_intents"])

    def test_api_schema_contract_compatibility(self):
        """ChatResponse schema parses and validates workflow output including optional memory."""
        session_id = "test-session-schema-011"
        res = run_support_workflow("Hello, I need help", session_id=session_id)

        chat_response = ChatResponse(**res)
        self.assertEqual(chat_response.session_id, session_id)
        self.assertIsNotNone(chat_response.memory)
        self.assertEqual(chat_response.memory["turn_count"], 1)


if __name__ == "__main__":
    unittest.main()
