"""Action Execution Agent.

The fifth specialized agent in the Agentic Customer Support System (PS-04).
Responsible for securely validating and executing supported e-commerce support
actions (such as order cancellations and return/replacement requests) through
the underlying service layer.

Strictly enforces:
- Safe read-only checks prior to mutation.
- Refusal of execution on ambiguous identity or ownership mismatch.
- Prohibition of unauthorized mutations (no refunds, no financial debits).
- Accurate reporting of actual mutations vs. no-ops or rejections.
- Zero bypass of business rules.
"""

import copy
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from backend.action_service import cancel_order, request_return, list_return_requests
    from backend.mock_data import ORDERS
except ImportError:
    from action_service import cancel_order, request_return, list_return_requests
    from mock_data import ORDERS

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {
    "cancellation",
    "cancel_order",
    "cancel",
    "return_or_replacement",
    "return",
    "replacement",
    "request_return",
    "request_replacement",
}

UNSUPPORTED_ACTIONS = {
    "refund",
    "payment_reversal",
    "chargeback",
    "change_address",
    "update_shipping_address",
    "change_payment_method",
    "apply_discount",
    "delete_account",
}

CONFIRMATION_INQUIRY_PATTERNS = [
    r"^(can|could|would)\s+(i|you)\s+(cancel|return|replace)",
    r"^is\s+it\s+possible\s+to\s+(cancel|return|replace)",
    r"^how\s+(do|can)\s+i\s+(cancel|return|replace)",
    r"^what\s+if\s+i\s+(cancel|want\s+to\s+cancel|return)",
    r"^am\s+i\s+able\s+to\s+(cancel|return|replace)",
]


class ActionExecutionResult(BaseModel):
    """Validated structured result from the Action Execution Agent."""

    action: str = Field(
        ...,
        description="The normalized requested action name (e.g. 'cancellation', 'return_or_replacement')",
    )
    is_supported: bool = Field(
        ...,
        description="Whether the requested action is supported by the application",
    )
    needs_confirmation: bool = Field(
        default=False,
        description="True if explicit customer confirmation is required prior to execution",
    )
    is_eligible: bool = Field(
        ...,
        description="Whether the order and customer context satisfy business eligibility rules",
    )
    status: str = Field(
        ...,
        description="Execution status: 'executed', 'rejected', 'confirmation_required', 'unsupported', 'failed', or 'no_op'",
    )
    message: str = Field(
        ...,
        description="Concise factual outcome explanation",
    )
    order_id: Optional[str] = Field(
        default=None,
        description="Target order ID, if provided and identified",
    )
    action_id: Optional[str] = Field(
        default=None,
        description="Identifier of created record (e.g. 'RET-ABC12345'), if applicable",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Specific reason for ineligibility or execution refusal, if applicable",
    )
    mutation_performed: bool = Field(
        default=False,
        description="True ONLY if underlying data records were genuinely modified",
    )
    execution_mode: str = Field(
        default="service_backed_deterministic",
        description="Execution pipeline origin: 'service_backed_deterministic'",
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sanitized outcome details from the underlying action service",
    )


class ActionExecutionAgent:
    """Specialized agent for validating and safely executing customer support actions."""

    def __init__(self):
        pass

    def normalize_action(self, action: str) -> str:
        """Normalize action string to canonical action name."""
        if not action or not isinstance(action, str):
            return "unknown"
        clean = action.strip().lower().replace("-", "_").replace(" ", "_")
        if clean in {"cancellation", "cancel", "cancel_order"}:
            return "cancellation"
        if clean in {"return", "replacement", "return_or_replacement", "request_return", "request_replacement"}:
            return "return_or_replacement"
        return clean

    def _is_hypothetical_inquiry(self, message: Optional[str]) -> bool:
        """Check if message is asking about possibility rather than commanding execution."""
        if not message or not isinstance(message, str):
            return False
        clean = message.strip().lower()
        for pat in CONFIRMATION_INQUIRY_PATTERNS:
            if re.search(pat, clean):
                # If message contains imperative confirmation words like "please proceed" or "yes cancel", it's not hypothetical
                if any(w in clean for w in ["please cancel now", "proceed with cancellation", "yes please", "do it"]):
                    return False
                return True
        return False

    def _check_live_eligibility(
        self,
        action: str,
        order_id: str,
    ) -> Dict[str, Any]:
        """Inspect live mock data to verify eligibility at execution time."""
        target_order = None
        for o in ORDERS:
            if o.get("id", "").upper() == order_id:
                target_order = o
                break

        if not target_order:
            return {
                "eligible": False,
                "reason": f"Order '{order_id}' was not found in the order database.",
                "order": None,
            }

        current_status = target_order.get("status", "").lower()

        if action == "cancellation":
            if current_status == "processing":
                return {"eligible": True, "reason": None, "order": copy.deepcopy(target_order)}
            elif current_status == "cancelled":
                return {"eligible": False, "reason": f"Order '{order_id}' is already cancelled.", "order": copy.deepcopy(target_order)}
            elif current_status == "shipped":
                return {
                    "eligible": False,
                    "reason": (
                        f"Order '{order_id}' cannot be cancelled because it has already shipped. "
                        "You may refuse delivery upon arrival or request a return once delivered."
                    ),
                    "order": copy.deepcopy(target_order),
                }
            elif current_status == "delivered":
                return {
                    "eligible": False,
                    "reason": (
                        f"Order '{order_id}' cannot be cancelled because it has already been delivered. "
                        "You may submit a return request instead."
                    ),
                    "order": copy.deepcopy(target_order),
                }
            else:
                return {
                    "eligible": False,
                    "reason": (
                        f"Order '{order_id}' cannot be cancelled because its current status is '{current_status}'. "
                        "Only orders in 'processing' status are eligible for cancellation."
                    ),
                    "order": copy.deepcopy(target_order),
                }

        elif action == "return_or_replacement":
            if current_status != "delivered":
                return {
                    "eligible": False,
                    "reason": (
                        f"Return or replacement requests are only permitted for 'delivered' orders. "
                        f"Order '{order_id}' is currently '{current_status}'."
                    ),
                    "order": copy.deepcopy(target_order),
                }

            # Check duplicate active return
            existing = list_return_requests(order_id)
            for req in existing:
                if req.get("status") in {"pending", "approved"}:
                    return {
                        "eligible": False,
                        "reason": (
                            f"An active {req.get('request_type')} request ({req.get('request_id')}) "
                            f"already exists for order '{order_id}'."
                        ),
                        "order": copy.deepcopy(target_order),
                    }

            return {"eligible": True, "reason": None, "order": copy.deepcopy(target_order)}

        return {"eligible": False, "reason": f"Action '{action}' is not supported.", "order": None}

    def execute(
        self,
        action: str,
        order_id: Optional[str],
        message: Optional[str] = None,
        customer_context: Optional[Dict[str, Any]] = None,
        request_type: Optional[str] = "return",
        reason: Optional[str] = None,
        require_confirmation: bool = False,
    ) -> ActionExecutionResult:
        """Validate and safely execute a customer support action.

        Guarantees:
        - Never mutates data if customer identity is ambiguous or order ownership mismatches.
        - Never mutates data for unsupported actions (e.g. refunds).
        - Accurately reports mutation_performed=True only if the service performs a state change.
        """
        norm_action = self.normalize_action(action)

        # 1. Check if action is supported
        if norm_action not in {"cancellation", "return_or_replacement"}:
            is_unsupported_financial = norm_action in UNSUPPORTED_ACTIONS or "refund" in norm_action or "pay" in norm_action
            rejection_msg = (
                f"Action '{norm_action}' is not supported via automated chat as it involves financial or payment modifications."
                if is_unsupported_financial
                else f"Action '{norm_action}' is not supported. Supported actions are order cancellation and return/replacement requests."
            )
            return ActionExecutionResult(
                action=norm_action,
                is_supported=False,
                needs_confirmation=False,
                is_eligible=False,
                status="unsupported",
                message=rejection_msg,
                order_id=order_id.strip().upper() if order_id and isinstance(order_id, str) else None,
                action_id=None,
                rejection_reason=f"Unsupported action '{norm_action}'",
                mutation_performed=False,
                execution_mode="service_backed_deterministic",
                details=None,
            )

        # 2. Check order ID validity
        if not order_id or not isinstance(order_id, str) or not order_id.strip():
            return ActionExecutionResult(
                action=norm_action,
                is_supported=True,
                needs_confirmation=False,
                is_eligible=False,
                status="rejected",
                message="Target Order ID is missing or invalid. An Order ID (e.g. ORD1001) is strictly required to execute this action.",
                order_id=None,
                action_id=None,
                rejection_reason="Missing or invalid Order ID",
                mutation_performed=False,
                execution_mode="service_backed_deterministic",
                details=None,
            )

        clean_order_id = order_id.strip().upper()

        # 3. Privacy & Ownership Safeguard: Refuse execution if customer context is ambiguous
        if customer_context:
            if customer_context.get("is_ambiguous"):
                return ActionExecutionResult(
                    action=norm_action,
                    is_supported=True,
                    needs_confirmation=False,
                    is_eligible=False,
                    status="rejected",
                    message="Action refused: customer identification or order references are ambiguous. Clarification is required for security.",
                    order_id=clean_order_id,
                    action_id=None,
                    rejection_reason="Ambiguous customer identity context",
                    mutation_performed=False,
                    execution_mode="service_backed_deterministic",
                    details=None,
                )

            # Check cross-customer ownership mismatch
            ctx_cust_id = customer_context.get("customer_id")
            if ctx_cust_id:
                # Lookup target order's actual customer_id
                target_order_record = next((o for o in ORDERS if o.get("id", "").upper() == clean_order_id), None)
                if target_order_record and target_order_record.get("customer_id") != ctx_cust_id:
                    return ActionExecutionResult(
                        action=norm_action,
                        is_supported=True,
                        needs_confirmation=False,
                        is_eligible=False,
                        status="rejected",
                        message=(
                            f"Action refused: order '{clean_order_id}' does not belong to verified customer '{ctx_cust_id}'."
                        ),
                        order_id=clean_order_id,
                        action_id=None,
                        rejection_reason="Customer ownership mismatch",
                        mutation_performed=False,
                        execution_mode="service_backed_deterministic",
                        details=None,
                    )

        # 4. Check if confirmation is required prior to execution
        should_confirm = require_confirmation or self._is_hypothetical_inquiry(message)
        if should_confirm:
            eligibility = self._check_live_eligibility(norm_action, clean_order_id)
            if not eligibility["eligible"]:
                return ActionExecutionResult(
                    action=norm_action,
                    is_supported=True,
                    needs_confirmation=False,
                    is_eligible=False,
                    status="rejected",
                    message=eligibility["reason"],
                    order_id=clean_order_id,
                    action_id=None,
                    rejection_reason=eligibility["reason"],
                    mutation_performed=False,
                    execution_mode="service_backed_deterministic",
                    details={"success": False, "action": norm_action, "order_id": clean_order_id, "message": eligibility["reason"]},
                )
            action_desc = "cancellation" if norm_action == "cancellation" else (request_type or "return")
            return ActionExecutionResult(
                action=norm_action,
                is_supported=True,
                needs_confirmation=True,
                is_eligible=True,
                status="confirmation_required",
                message=(
                    f"Order '{clean_order_id}' is eligible for {action_desc}. "
                    "Please confirm if you would like me to proceed with executing this request."
                ),
                order_id=clean_order_id,
                action_id=None,
                rejection_reason=None,
                mutation_performed=False,
                execution_mode="service_backed_deterministic",
                details=None,
            )

        # 6. Execute action through underlying service layer
        try:
            if norm_action == "cancellation":
                service_res = cancel_order(
                    order_id=clean_order_id,
                    reason=reason or "Customer requested cancellation via support chat",
                )
                success = service_res.get("success", False)
                return ActionExecutionResult(
                    action=norm_action,
                    is_supported=True,
                    needs_confirmation=False,
                    is_eligible=success,
                    status="executed" if success else "rejected",
                    message=service_res.get("message", "Cancellation processed."),
                    order_id=clean_order_id,
                    action_id=None,
                    rejection_reason=None if success else service_res.get("message"),
                    mutation_performed=success,
                    execution_mode="service_backed_deterministic",
                    details=service_res,
                )

            elif norm_action == "return_or_replacement":
                service_res = request_return(
                    order_id=clean_order_id,
                    request_type=request_type or "return",
                    reason=reason or "Customer requested return/replacement via support chat",
                )
                success = service_res.get("success", False)
                ret_req = service_res.get("return_request")
                action_id = ret_req.get("request_id") if ret_req else None

                return ActionExecutionResult(
                    action=norm_action,
                    is_supported=True,
                    needs_confirmation=False,
                    is_eligible=success,
                    status="executed" if success else "rejected",
                    message=service_res.get("message", "Return request processed."),
                    order_id=clean_order_id,
                    action_id=action_id,
                    rejection_reason=None if success else service_res.get("message"),
                    mutation_performed=success,
                    execution_mode="service_backed_deterministic",
                    details=service_res,
                )

        except Exception as e:
            logger.error("ActionExecutionAgent encountered an exception during execution: %s", e)
            return ActionExecutionResult(
                action=norm_action,
                is_supported=True,
                needs_confirmation=False,
                is_eligible=False,
                status="failed",
                message=f"Action execution failed due to an internal service error: {e}",
                order_id=clean_order_id,
                action_id=None,
                rejection_reason=str(e),
                mutation_performed=False,
                execution_mode="service_backed_deterministic",
                details=None,
            )

        return ActionExecutionResult(
            action=norm_action,
            is_supported=True,
            needs_confirmation=False,
            is_eligible=False,
            status="no_op",
            message="No action was executed.",
            order_id=clean_order_id,
            action_id=None,
            rejection_reason="No operation performed",
            mutation_performed=False,
            execution_mode="service_backed_deterministic",
            details=None,
        )


def execute_support_action(
    action: str,
    order_id: Optional[str],
    message: Optional[str] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    request_type: Optional[str] = "return",
    reason: Optional[str] = None,
    require_confirmation: bool = False,
) -> ActionExecutionResult:
    """Convenience helper to validate and execute support actions."""
    agent = ActionExecutionAgent()
    return agent.execute(
        action=action,
        order_id=order_id,
        message=message,
        customer_context=customer_context,
        request_type=request_type,
        reason=reason,
        require_confirmation=require_confirmation,
    )
