'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { apiFetch } from '../lib/api';
import { DATA_REFRESH_EVENT, requestDataRefresh } from '../lib/useCustomer';

const TYPE_LABELS = {
  ticket_opened: 'Case opened',
  ticket_assigned: 'Specialist assigned',
  ticket_resolved: 'Case resolved',
  order_update: 'Order update',
};

const RATED_KEY = 'ns_rated_cases';

function readRated() {
  try {
    return JSON.parse(window.localStorage.getItem(RATED_KEY) || '{}');
  } catch {
    return {};
  }
}

function formatWhen(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

/**
 * Customer inbox: order updates plus replies from the human specialists who handled
 * escalated cases. Polls every 10 seconds so a resolved case shows up without a refresh.
 */
export default function Inbox({ customerId }) {
  const [data, setData] = useState({ unread_count: 0, notifications: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rated, setRated] = useState({});

  const isGuest = !customerId || customerId === 'none';

  const load = useCallback(async () => {
    if (isGuest) {
      setData({ unread_count: 0, notifications: [] });
      setLoading(false);
      return;
    }
    try {
      const res = await apiFetch(`/customers/${customerId}/notifications`);
      setData(res);
      setError(null);
    } catch (err) {
      setError(err.message || 'Could not load your inbox.');
    } finally {
      setLoading(false);
    }
  }, [customerId, isGuest]);

  useEffect(() => {
    setRated(readRated());
  }, []);

  useEffect(() => {
    setLoading(true);
    load();
    const timer = setInterval(load, 10000);
    window.addEventListener(DATA_REFRESH_EVENT, load);
    return () => {
      clearInterval(timer);
      window.removeEventListener(DATA_REFRESH_EVENT, load);
    };
  }, [load]);

  const markRead = async (id) => {
    try {
      await apiFetch(`/notifications/${id}/read`, { method: 'POST' });
      await load();
      requestDataRefresh();
    } catch {
      /* non-fatal */
    }
  };

  const markAllRead = async () => {
    try {
      await apiFetch(`/customers/${customerId}/notifications/read-all`, { method: 'POST' });
      await load();
      requestDataRefresh();
    } catch {
      /* non-fatal */
    }
  };

  const rateCase = async (note, stars) => {
    try {
      await apiFetch('/admin/csat', {
        method: 'POST',
        body: JSON.stringify({
          ticket_id: note.ticket_id,
          customer_id: customerId,
          rating: stars,
          feedback: `Rated ${stars} stars from the inbox.`,
        }),
      });
      const next = { ...readRated(), [note.id]: stars };
      try {
        window.localStorage.setItem(RATED_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      setRated(next);
    } catch {
      /* non-fatal */
    }
  };

  if (isGuest) {
    return (
      <div className="state-container">
        <h2 className="state-title">Pick a customer to see an inbox</h2>
        <p className="state-message">Guests do not have an inbox. Choose a customer account above.</p>
      </div>
    );
  }

  if (loading) {
    return <p className="section-desc">Loading your inbox...</p>;
  }

  if (error) {
    return (
      <div className="state-container" role="alert">
        <h2 className="state-title">Unable to load inbox</h2>
        <p className="state-message">{error}</p>
        <button type="button" className="state-btn" onClick={load}>Try Again</button>
      </div>
    );
  }

  if (data.notifications.length === 0) {
    return (
      <div className="state-container">
        <h2 className="state-title">Your inbox is empty</h2>
        <p className="state-message">Order updates and replies from our support specialists will appear here.</p>
      </div>
    );
  }

  return (
    <div className="inbox-wrap">
      <div className="inbox-toolbar">
        <span>{data.unread_count} unread</span>
        {data.unread_count > 0 && (
          <button type="button" className="inbox-markall" onClick={markAllRead}>Mark all as read</button>
        )}
      </div>

      <ul className="inbox-list">
        {data.notifications.map((note) => (
          <li
            key={note.id}
            className={`inbox-item ${note.read ? '' : 'unread'} ${note.type}`}
            onClick={() => !note.read && markRead(note.id)}
          >
            <div className="inbox-item-head">
              <span className="inbox-type-chip">{TYPE_LABELS[note.type] || 'Update'}</span>
              {!note.read && <span className="inbox-unread-dot" aria-label="Unread" />}
              <span className="inbox-time">{formatWhen(note.created_at)}</span>
            </div>
            <div className="inbox-title">{note.title}</div>

            {note.type === 'ticket_resolved' ? (
              <div className="inbox-reply">
                <div className="inbox-reply-label">
                  Reply from {note.from_agent || 'our specialist'}:
                </div>
                <p className="inbox-reply-text">{note.message}</p>
              </div>
            ) : (
              <p className="inbox-message">{note.message}</p>
            )}

            <div className="inbox-meta">
              {note.ticket_id && <code>{note.ticket_id}</code>}
              {note.order_id && (
                <Link href="/orders" className="inbox-link">Order {note.order_id}</Link>
              )}
              {note.ticket_id && note.type === 'ticket_resolved' && (
                <span className="inbox-rate" onClick={(e) => e.stopPropagation()}>
                  {rated[note.id] ? (
                    <span>You rated this {rated[note.id]}/5. Thank you!</span>
                  ) : (
                    <>
                      <span>Rate this answer:</span>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className="csat-star-btn"
                          onClick={() => rateCase(note, star)}
                          title={`Rate ${star} out of 5`}
                        >
                          {star} &#9733;
                        </button>
                      ))}
                    </>
                  )}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
