'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { apiFetch } from '../lib/api';
import { DATA_REFRESH_EVENT, requestDataRefresh } from '../lib/useCustomer';
import {
  IconChat,
  IconRefresh,
  IconAlertTriangle,
  IconCheck,
  IconPackage,
  IconReturn,
  IconCreditCard,
  IconShield,
  IconSend,
  IconUsers,
  IconLayers,
  IconCpu,
} from './Icons';

import { CUSTOMER_PROFILES, getCustomerProfile } from '../lib/customerContext';

/**
 * Lightweight markdown parser that turns inline and block markdown
 * (**bold**, *italic*, `code`, bullet lists, and paragraphs) into clean React elements.
 */
function renderMarkdown(content) {
  if (!content) return null;
  const rawText = typeof content === 'string' ? content : JSON.stringify(content);
  const lines = rawText.split('\n');

  const elements = [];
  let currentList = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="chat-markdown-ul">
          {currentList.map((item, idx) => (
            <li key={idx}>{parseInlineMarkdown(item)}</li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      currentList.push(trimmed.slice(2));
    } else {
      flushList();
      if (trimmed === '') {
        elements.push(<div key={`spacer-${index}`} className="chat-paragraph-spacer" />);
      } else {
        elements.push(
          <p key={`p-${index}`} className="chat-markdown-p">
            {parseInlineMarkdown(line)}
          </p>
        );
      }
    }
  });

  flushList();
  return elements;
}

function parseInlineMarkdown(text) {
  if (!text) return '';
  // Split on bold (**text**), code (`text`), and italic (*text*)
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
  return tokens.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="chat-md-bold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="chat-md-code">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} className="chat-md-italic">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

export default function ChatPanel({

  initialQuery = '',
  isExpanded = false,
  customHeader = null,
  pendingPrompt = null,
  selectedCustomerId = 'CUST001',
  onCustomerChange = null,
  showCustomerSelector = true,
} = {}) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [inputMessage, setInputMessage] = useState(initialQuery || '');
  const [isLoading, setIsLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [lastFailedMessage, setLastFailedMessage] = useState(null);
  const [csatSubmitted, setCsatSubmitted] = useState({});
  const [activeCustId, setActiveCustId] = useState(selectedCustomerId || 'CUST001');

  useEffect(() => {
    if (selectedCustomerId && selectedCustomerId !== activeCustId) {
      setActiveCustId(selectedCustomerId);
    }
  }, [selectedCustomerId]);

  const activeCustomer = getCustomerProfile(activeCustId);

  // Live orders for the header strip (never stale after a cancel, return or purchase)
  const [liveOrders, setLiveOrders] = useState([]);

  const loadOrders = useCallback(async () => {
    if (!activeCustId || activeCustId === 'none') {
      setLiveOrders([]);
      return;
    }
    try {
      const data = await apiFetch(`/customers/${activeCustId}/orders`);
      setLiveOrders(Array.isArray(data) ? data : []);
    } catch {
      /* backend offline: keep last known orders */
    }
  }, [activeCustId]);

  useEffect(() => {
    loadOrders();
    const timer = setInterval(loadOrders, 10000);
    window.addEventListener(DATA_REFRESH_EVENT, loadOrders);
    return () => {
      clearInterval(timer);
      window.removeEventListener(DATA_REFRESH_EVENT, loadOrders);
    };
  }, [loadOrders]);

  useEffect(() => {
    if (initialQuery) {
      setInputMessage(initialQuery);
    }
  }, [initialQuery]);

  const messagesEndRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Auto-scroll when messages update or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, chatError]);

  // Reset conversation to fresh session
  const handleStartNewChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setChatError(null);
    setLastFailedMessage(null);
    setInputMessage('');
    setCsatSubmitted({});
  }, []);

  const handleSelectCustomer = (newId) => {
    setActiveCustId(newId);
    if (onCustomerChange) {
      onCustomerChange(newId);
    }
    handleStartNewChat();
  };

  // Core send message handler
  const handleSendMessage = useCallback(
    async (textToSend) => {
      const message = (textToSend || inputMessage).trim();
      if (!message || isLoading) return;

      const userMessageId = `user-${Date.now()}`;
      const userMsg = {
        id: userMessageId,
        role: 'user',
        content: message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputMessage('');
      setIsLoading(true);
      setChatError(null);
      setLastFailedMessage(null);

      try {
        const payload = {
          message,
          session_id: sessionId || undefined,
          customer_id: activeCustId && activeCustId !== 'none' ? activeCustId : undefined,
        };

        const response = await apiFetch('/chat', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        if (!isMountedRef.current) return;

        // Update session ID if backend returns one
        if (response.session_id) {
          setSessionId(response.session_id);
        }

        const assistantMsg = {
          id: `asst-${Date.now()}`,
          role: 'assistant',
          content: response.assistant_message,
          intent: response.intent,
          decision: response.decision,
          ticket: response.ticket,
          action_result: response.action_result,
          investigation: response.investigation,
          knowledge_results: response.knowledge_results,
          active_agent: response.understanding?.active_agent || 'supervisor',
          customer_context: response.customer_context,
          agent_stages: response.agent_stages || [],
          mode: response.understanding?.mode || 'deterministic',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        setMessages((prev) => [...prev, assistantMsg]);
        // Actions in the chat can change orders, tickets and inbox messages: refresh them everywhere
        requestDataRefresh();

      } catch (err) {
        if (!isMountedRef.current) return;
        setChatError(err.message || 'Unable to connect to AI Support service. Please try again.');
        setLastFailedMessage(message);
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      }
    },
    [inputMessage, isLoading, sessionId, activeCustId]
  );

  // One-click prompts from the side rail arrive as {text, nonce}; send them straight away
  const sendRef = useRef(null);
  sendRef.current = handleSendMessage;
  useEffect(() => {
    if (pendingPrompt && pendingPrompt.text) {
      sendRef.current(pendingPrompt.text);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingPrompt?.nonce]);

  const handleCsatRating = async (msgId, ticketId, stars) => {
    try {
      await apiFetch('/admin/csat', {
        method: 'POST',
        body: JSON.stringify({
          ticket_id: ticketId || 'general',
          customer_id: activeCustId && activeCustId !== 'none' ? activeCustId : 'CUST001',
          rating: stars,
          feedback: `Rated ${stars} stars via Chat Widget.`,
        }),
      });
      setCsatSubmitted((prev) => ({ ...prev, [msgId]: stars }));
    } catch (err) {

      console.error('Failed to submit CSAT rating', err);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  const handleRetry = () => {
    if (lastFailedMessage) {
      handleSendMessage(lastFailedMessage);
    }
  };

  const lastMessageId = messages.length ? messages[messages.length - 1].id : null;

  return (
    <div className={`chat-panel ${isExpanded ? 'chat-panel-expanded' : ''}`}>
      {/* Header — Use custom header if provided, otherwise default */}
      {customHeader || (
        <div className="chat-header">
          <div className="chat-header-title">
            <span className="status-dot" aria-hidden="true" />
            <span>AI Support Concierge</span>
            <span className="chat-model-badge">Autonomous ReAct</span>
          </div>

          <div className="chat-header-actions">
            {sessionId && (
              <span
                className="chat-session-badge"
                title={`Active Thread ID: ${sessionId}`}
              >
                Session: #{sessionId.slice(0, 8)}
              </span>
            )}
            <button
              type="button"
              className="chat-btn-reset"
              onClick={handleStartNewChat}
              title="Clear conversation and start a new session"
            >
              <IconRefresh size={14} />
              <span>New Chat</span>
            </button>
          </div>
        </div>
      )}

      {/* Interactive Customer Context Selector Bar */}
      {showCustomerSelector && (
        <div className="chat-customer-bar">
          <div className="customer-selector-group">
            <div className="customer-selector-label">
              <IconUsers size={14} />
              <span>Customer:</span>
            </div>
            <select
              className="customer-select-control"
              value={activeCustId}
              onChange={(e) => handleSelectCustomer(e.target.value)}
              aria-label="Select Customer Account Persona"
            >
              {CUSTOMER_PROFILES.map((cust) => (
                <option key={cust.id} value={cust.id}>
                  {cust.name} ({cust.id}) — {cust.badge}
                </option>
              ))}
            </select>
          </div>

          <div className="customer-active-orders-hint">
            {activeCustomer && activeCustomer.id !== 'none' ? (
              <>
                <span className="customer-context-pill">
                  <span className="pill-dot" />
                  <span>Account Linked</span>
                </span>
                <span className="customer-quick-orders-text">
                  {liveOrders.length > 0 ? (
                    <>
                      Orders: {liveOrders.map((o) => `${o.id} (${o.status.replace('_', ' ')})`).join(', ')}
                    </>
                  ) : (
                    <span>0 active orders</span>
                  )}
                </span>
              </>
            ) : (
              <span className="customer-context-guest">
                Guest Mode — Specify Order IDs manually in chat
              </span>
            )}
          </div>
        </div>
      )}

      {/* Messages Scroll Container */}
      <div className="chat-messages" aria-live="polite">
        {/* Welcome State when no messages */}
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">
              <IconChat size={30} />
            </div>
            <h3 className="chat-welcome-title">
              {activeCustomer && activeCustomer.id !== 'none'
                ? `Welcome back, ${activeCustomer.name}`
                : 'How can we assist you today?'}
            </h3>
            <p className="chat-welcome-desc">
              {activeCustomer && activeCustomer.id !== 'none'
                ? `Your account (${activeCustomer.id}) is actively recognized. Ask for order status, cancellation, or returns without writing your Order ID.`
                : 'Inquire about real-time order tracking, cancellation requests, payment status, or warranty guidelines.'}
            </p>

            <div className="chat-prompt-chips">
              {(activeCustomer?.starterPrompts || []).map((prompt, idx) => (
                <button
                  key={`prompt-${idx}`}
                  type="button"
                  className="chat-chip"
                  onClick={() => handleSendMessage(prompt.text)}
                >
                  <span className="chat-chip-tag">{prompt.tag}</span>
                  <span>{prompt.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Bubbles */}
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-row ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="chat-bubble-user">
                <div>{msg.content}</div>
                <div className="chat-timestamp user">{msg.timestamp}</div>
              </div>
            ) : (
              <div className="chat-bubble-assistant">
                {/* Meta Bar */}
                <div className="chat-assistant-meta">
                  <span className="chat-assistant-name">
                    <span className="agent-monogram">AI</span>
                    <span>Support Concierge</span>
                  </span>
                  {msg.customer_context?.order_id && (
                    <span
                      className="tag-order-resolved"
                      title={`Automatically retrieved for ${msg.customer_context.customer_id || 'customer'}`}
                    >
                      <IconCheck size={11} />
                      <span>order: {msg.customer_context.order_id}</span>
                    </span>
                  )}
                  {msg.active_agent && (
                    <span className="chat-agent-pill">
                      agent: {msg.active_agent}
                    </span>
                  )}
                  {msg.intent && (
                    <span className="tag-intent" title={`Detected Intent: ${msg.intent}`}>
                      intent: {msg.intent}
                    </span>
                  )}
                  {msg.decision && (
                    <span className="tag-decision" title={`Workflow Decision: ${msg.decision}`}>
                      decision: {msg.decision}
                    </span>
                  )}
                  {msg.mode === 'agentic_react_supervisor' && (
                    <span className="tag-gemini-live" title="Generated live by Google Gemini ReAct Supervisor">
                      <IconCpu size={11} />
                      <span>Gemini ReAct</span>
                    </span>
                  )}
                </div>

                {/* Agentic Working & Execution Stages (Collapsible) */}
                {msg.agent_stages && msg.agent_stages.length > 0 && (
                  <details className="agentic-stages-accordion" open={true}>
                    <summary className="agentic-stages-summary">
                      <div className="stages-summary-left">
                        <IconLayers size={13} />
                        <span>Agentic Execution Trace ({msg.agent_stages.length} stages)</span>
                      </div>
                      <span className="stages-summary-tag">Live Multi-Agent Reasoning</span>
                    </summary>
                    <div className="agentic-stages-timeline">
                      {msg.agent_stages.map((stg, sIdx) => (
                        <div key={sIdx} className="agentic-stage-item">
                          <div className="stage-indicator">
                            <span className="stage-step-num">{sIdx + 1}</span>
                            {sIdx < msg.agent_stages.length - 1 && <span className="stage-line" />}
                          </div>
                          <div className="stage-content">
                            <div className="stage-title-row">
                              <span className="stage-name">{stg.stage}</span>
                              <span className="stage-agent-badge">{stg.agent}</span>
                            </div>
                            <div className="stage-action-text">{stg.action}</div>
                            {stg.detail && <div className="stage-detail-sub">{stg.detail}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                {/* Main Response Text (Markdown Formatted) */}
                <div className="chat-text">
                  {renderMarkdown(msg.content)}
                </div>

                {/* Structured Support Details */}
                <div className="chat-structured-block">


                  {/* Interactive Confirmation Guard Prompt */}
                  {msg.decision === 'confirmation_required' && (
                    <div className="chat-confirmation-box">
                      <div className="confirmation-header">
                        <IconAlertTriangle size={16} />
                        <span>Action Confirmation Required:</span>
                      </div>
                      <div className="confirmation-actions">
                        <button
                          type="button"
                          onClick={() => handleSendMessage('yes')}
                          disabled={msg.id !== lastMessageId || isLoading}
                          className="btn-confirm-yes"
                        >
                          Confirm Cancellation
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSendMessage('no')}
                          disabled={msg.id !== lastMessageId || isLoading}
                          className="btn-confirm-no"
                        >
                          Keep Order
                        </button>
                      </div>
                    </div>
                  )}

                  {/* 1. Action Result Card */}
                  {msg.action_result && (
                    <div
                      className={`chat-card chat-card-action ${
                        msg.action_result.success ? 'success' : 'rejected'
                      }`}
                    >
                      <div className="chat-card-header">
                        <span className="action-result-label">
                          <IconCheck size={14} />
                          <span>
                            {msg.action_result.success
                              ? 'Action Executed Successfully'
                              : 'Action Request Rejected'}
                          </span>
                        </span>
                        <span className="order-id-code">{msg.action_result.order_id}</span>
                      </div>
                      <div className="action-result-body">{msg.action_result.message}</div>
                      {msg.action_result.return_request && (
                        <div className="return-request-sub">
                          Return Authorization ID: <code>{msg.action_result.return_request.request_id}</code>{' '}
                          (Status: {msg.action_result.return_request.status})
                        </div>
                      )}
                    </div>
                  )}

                  {/* 2. Escalation Support Ticket Card */}
                  {msg.ticket && (
                    <div className="chat-card chat-card-ticket">
                      <div className="chat-card-header">
                        <span className="ticket-title-wrap">
                          <span>Support Ticket ID:</span>
                          <span className="ticket-code">{msg.ticket.ticket_id}</span>
                        </span>
                        <span className={`ticket-priority-pill ${msg.ticket.priority || 'medium'}`}>
                          {msg.ticket.priority || 'medium'}
                        </span>
                      </div>
                      <div className="ticket-escalation-reason">
                        <strong>Reason:</strong> {msg.ticket.escalation_reason}
                      </div>
                      <div className="ticket-dept-line">
                        Department: <strong>{msg.ticket.target_team?.replace('_', ' ').toUpperCase()}</strong> &bull; Status: <code>{msg.ticket.status}</code>
                      </div>
                      {activeCustId && activeCustId !== 'none' && (
                        <div className="ticket-inbox-line">
                          A human specialist will reply in your{' '}
                          <Link href="/orders?tab=inbox">Inbox</Link>.
                        </div>
                      )}
                    </div>
                  )}

                  {/* 3. Verified Order Investigation Card */}
                  {msg.investigation &&
                    msg.investigation.attempted &&
                    msg.investigation.status === 'found' && (
                      <div className="chat-card chat-card-investigation">
                        <div className="chat-card-header">
                          <span className="investigation-title">
                            <IconCheck size={14} />
                            <span>Order Context Verified</span>
                          </span>
                          <span className="order-id-code">{msg.investigation.order_id}</span>
                        </div>
                        <div className="investigation-summary">{msg.investigation.summary}</div>
                        {msg.investigation.order && (
                          <div className="investigation-meta-row">
                            <span className="investigation-meta-item">
                              Status: <strong>{msg.investigation.order.status}</strong>
                            </span>
                            <span className="investigation-meta-divider">&bull;</span>
                            <span className="investigation-meta-item">
                              Total: <strong>${typeof msg.investigation.order.total_amount === 'number' ? msg.investigation.order.total_amount.toFixed(2) : msg.investigation.order.total_amount}</strong>
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                  {/* 4. Knowledge Guidance Accordion */}
                  {msg.knowledge_results && msg.knowledge_results.length > 0 && (
                    <details className="chat-knowledge-accordion">
                      <summary>
                        <span>Policy References ({msg.knowledge_results.length})</span>
                      </summary>
                      <div className="chat-knowledge-list">
                        {msg.knowledge_results.map((kEntry) => (
                          <div key={kEntry.id} className="chat-knowledge-item">
                            <div className="chat-knowledge-title">{kEntry.title}</div>
                            <div>{kEntry.guidance}</div>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {/* 5. Customer Satisfaction (CSAT) Widget */}
                  {(msg.decision === 'action_completed' || msg.decision === 'agentic_resolved') && msg.action_result?.success !== false && (
                    <div className="csat-widget-box">
                      {csatSubmitted[msg.id] ? (
                        <div className="csat-thankyou">
                          <IconCheck size={14} />
                          <span>Thank you! Your rating of {csatSubmitted[msg.id]}/5 has been recorded in the Supervisor Operations Desk.</span>
                        </div>
                      ) : (
                        <div>
                          <div className="csat-prompt">
                            How satisfied are you with this resolution?
                          </div>
                          <div className="csat-stars-row">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <button
                                key={star}
                                type="button"
                                onClick={() => handleCsatRating(msg.id, msg.ticket?.ticket_id, star)}
                                className="csat-star-btn"
                                title={`Rate ${star} out of 5 stars`}
                              >
                                {star} ★
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                </div>

                <div className="chat-timestamp assistant">{msg.timestamp}</div>
              </div>
            )}
          </div>
        ))}

        {/* Loading / Typing Indicator */}
        {isLoading && (
          <div className="chat-row assistant">
            <div className="chat-typing" aria-label="Support Assistant is thinking">
              <span className="chat-typing-dot" />
              <span className="chat-typing-dot" />
              <span className="chat-typing-dot" />
              <span className="chat-typing-text">
                Multi-agent investigation in progress...
              </span>
            </div>
          </div>
        )}

        {/* Inline Error Notice */}
        {chatError && (
          <div className="chat-inline-error" role="alert">
            <div className="error-text">
              <IconAlertTriangle size={16} />
              <span>{chatError}</span>
            </div>
            <button type="button" onClick={handleRetry} className="btn-error-retry">
              Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question (e.g. Track ORD1001, cancel ORD1002, return policy)..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          disabled={isLoading}
          aria-label="Type your message"
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={isLoading || !inputMessage.trim()}
          aria-label="Send message"
        >
          <span>Send</span>
          <IconSend size={15} />
        </button>
      </form>
    </div>
  );
}
