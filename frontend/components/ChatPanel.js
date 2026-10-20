'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiFetch } from '../lib/api';

const STARTER_PROMPTS = [
  { icon: '📦', text: 'Where is my order ORD1001?' },
  { icon: '❓', text: 'Where is my order?' },
  { icon: '🔄', text: 'Please cancel order ORD1002' },
  { icon: '💳', text: 'Payment failed for order ORD1004' },
  { icon: '📚', text: 'What is your return policy?' },
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [lastFailedMessage, setLastFailedMessage] = useState(null);

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
  }, []);

  // Core send message handler
  const handleSendMessage = useCallback(async (textToSend) => {
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
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      if (!isMountedRef.current) return;
      setChatError(err.message || 'Unable to connect to AI Support service. Please try again.');
      setLastFailedMessage(message);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [inputMessage, isLoading, sessionId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  const handleRetry = () => {
    if (lastFailedMessage) {
      handleSendMessage(lastFailedMessage);
    }
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-title">
          <span className="status-dot" aria-hidden="true"></span>
          <span>AI Support Assistant</span>
        </div>

        <div className="chat-header-actions">
          {sessionId && (
            <span
              className="chat-session-badge"
              title={`Active Session ID: ${sessionId}`}
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
            <span>🔄</span>
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll Container */}
      <div className="chat-messages" aria-live="polite">
        {/* Welcome State when no messages */}
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">💬</div>
            <h3 className="chat-welcome-title">How can we help today?</h3>
            <p className="chat-welcome-desc">
              Ask questions about orders, payments, cancellation policies, returns, or troubleshoot issues.
            </p>

            <div className="chat-prompt-chips">
              {STARTER_PROMPTS.map((prompt, idx) => (
                <button
                  key={`prompt-${idx}`}
                  type="button"
                  className="chat-chip"
                  onClick={() => handleSendMessage(prompt.text)}
                >
                  <span>{prompt.icon}</span>
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
                <div style={{ fontSize: '0.7rem', opacity: 0.8, textAlign: 'right', marginTop: '0.3rem' }}>
                  {msg.timestamp}
                </div>
              </div>
            ) : (
              <div className="chat-bubble-assistant">
                {/* Meta Bar */}
                <div className="chat-assistant-meta">
                  <span className="chat-assistant-name">
                    <span>🤖</span>
                    <span>Support Bot</span>
                  </span>
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
                </div>

                {/* Main Response Text */}
                <div className="chat-text">{msg.content}</div>

                {/* Structured Support Details (Confirmed backend data only) */}
                <div className="chat-structured-block">
                  {/* 1. Action Result Card */}
                  {msg.action_result && (
                    <div className={`chat-card chat-card-action ${msg.action_result.success ? 'success' : 'rejected'}`}>
                      <div className="chat-card-header">
                        <span>{msg.action_result.success ? '✅ Action Succeeded' : '❌ Action Rejected'}</span>
                        <span style={{ fontFamily: 'monospace' }}>{msg.action_result.order_id}</span>
                      </div>
                      <div style={{ color: 'var(--text-secondary)' }}>{msg.action_result.message}</div>
                      {msg.action_result.return_request && (
                        <div style={{ fontSize: '0.75rem', marginTop: '0.2rem', color: 'var(--accent-primary)' }}>
                          Return Request ID: <code>{msg.action_result.return_request.request_id}</code> (Status: {msg.action_result.return_request.status})
                        </div>
                      )}
                    </div>
                  )}

                  {/* 2. Escalation Support Ticket Card */}
                  {msg.ticket && (
                    <div className="chat-card chat-card-ticket">
                      <div className="chat-card-header">
                        <span style={{ fontWeight: '700', color: '#f472b6' }}>
                          🎫 Ticket Created: {msg.ticket.ticket_id}
                        </span>
                        <span className={`ticket-priority-pill ${msg.ticket.priority || 'medium'}`}>
                          {msg.ticket.priority || 'medium'}
                        </span>
                      </div>
                      <div style={{ color: 'var(--text-primary)', fontSize: '0.8rem' }}>
                        <strong>Escalation Reason:</strong> {msg.ticket.escalation_reason}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Status: <code>{msg.ticket.status}</code> • Session: <code>{msg.ticket.session_id?.slice(0, 8)}</code>
                      </div>
                    </div>
                  )}

                  {/* 3. Verified Order Investigation Card */}
                  {msg.investigation && msg.investigation.attempted && msg.investigation.status === 'found' && (
                    <div className="chat-card chat-card-investigation">
                      <div className="chat-card-header">
                        <span>🔍 Order Context Verified</span>
                        <span style={{ fontFamily: 'monospace' }}>{msg.investigation.order_id}</span>
                      </div>
                      <div style={{ color: 'var(--text-secondary)' }}>
                        {msg.investigation.summary}
                      </div>
                      {msg.investigation.order && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: '0.75rem' }}>
                          <span>Status: <strong>{msg.investigation.order.status}</strong></span>
                          <span>Total: <strong>${typeof msg.investigation.order.total_amount === 'number' ? msg.investigation.order.total_amount.toFixed(2) : msg.investigation.order.total_amount}</strong></span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 4. Knowledge Guidance Accordion */}
                  {msg.knowledge_results && msg.knowledge_results.length > 0 && (
                    <details className="chat-knowledge-accordion">
                      <summary>
                        <span>📚</span>
                        <span>View Policy References ({msg.knowledge_results.length})</span>
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
                </div>

                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  {msg.timestamp}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Loading / Typing Indicator */}
        {isLoading && (
          <div className="chat-row assistant">
            <div className="chat-typing" aria-label="Support Assistant is thinking">
              <span className="chat-typing-dot"></span>
              <span className="chat-typing-dot"></span>
              <span className="chat-typing-dot"></span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '0.4rem' }}>
                Investigating &amp; responding...
              </span>
            </div>
          </div>
        )}

        {/* Inline Error Notice */}
        {chatError && (
          <div className="chat-inline-error" role="alert">
            <div>⚠️ {chatError}</div>
            <button
              type="button"
              onClick={handleRetry}
              style={{
                background: 'transparent',
                border: '1px solid #f87171',
                color: '#f87171',
                borderRadius: '4px',
                padding: '0.2rem 0.5rem',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '600',
              }}
            >
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
          placeholder="Ask a question (e.g. Track ORD1001, cancel ORD1002)..."
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
          <span>↗</span>
        </button>
      </form>
    </div>
  );
}
