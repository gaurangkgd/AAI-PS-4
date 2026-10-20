"""Specialized multi-agent package for Agentic Customer Support System."""

from backend.agents.conversation_understanding_agent import (
    ConversationUnderstandingAgent,
    ConversationUnderstandingResult,
    understand_conversation,
)
from backend.agents.customer_context_agent import (
    CustomerContextAgent,
    CustomerContextResult,
    resolve_customer_context,
)
from backend.agents.knowledge_retrieval_agent import (
    KnowledgeRetrievalAgent,
    KnowledgeRetrievalResult,
    retrieve_knowledge_context,
)
from backend.agents.troubleshooting_agent import (
    TroubleshootingAgent,
    TroubleshootingResult,
    diagnose_support_issue,
)
from backend.agents.action_execution_agent import (
    ActionExecutionAgent,
    ActionExecutionResult,
    execute_support_action,
)
from backend.agents.multi_turn_memory_agent import (
    MultiTurnMemoryAgent,
    MemoryResolutionResult,
    SessionMemory,
    resolve_session_memory,
    update_session_memory,
    get_session_summary,
    clear_memory_store,
    reset_session_memory,
)

from backend.agents.escalation_decision_agent import (
    EscalationDecisionAgent,
    EscalationDecisionResult,
    LLMEscalationOutput,
    decide_escalation,
)

__all__ = [
    "ConversationUnderstandingAgent",
    "ConversationUnderstandingResult",
    "understand_conversation",
    "CustomerContextAgent",
    "CustomerContextResult",
    "resolve_customer_context",
    "KnowledgeRetrievalAgent",
    "KnowledgeRetrievalResult",
    "retrieve_knowledge_context",
    "TroubleshootingAgent",
    "TroubleshootingResult",
    "diagnose_support_issue",
    "ActionExecutionAgent",
    "ActionExecutionResult",
    "execute_support_action",
    "MultiTurnMemoryAgent",
    "MemoryResolutionResult",
    "SessionMemory",
    "resolve_session_memory",
    "update_session_memory",
    "get_session_summary",
    "clear_memory_store",
    "reset_session_memory",
    "EscalationDecisionAgent",
    "EscalationDecisionResult",
    "LLMEscalationOutput",
    "decide_escalation",
]
