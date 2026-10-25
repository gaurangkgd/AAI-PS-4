'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { apiFetch } from '../../lib/api';
import { useCustomer, DATA_REFRESH_EVENT } from '../../lib/useCustomer';
import { CUSTOMER_PROFILES } from '../../lib/customerContext';
import Inbox from '../../components/Inbox';

/**
 * Format ISO datetime string safely.
 */
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Maps raw backend order status to CSS class and human-readable label.
 */
function getStatusInfo(status = '') {
  const norm = status.toLowerCase();
  switch (norm) {
    case 'delivered':
      return { className: 'status-delivered', label: 'Delivered' };
    case 'processing':
      return { className: 'status-processing', label: 'Processing' };
    case 'shipped':
      return { className: 'status-shipped', label: 'Shipped' };
    case 'cancelled':
      return { className: 'status-cancelled', label: 'Cancelled' };
    case 'payment_failed':
      return { className: 'status-payment_failed', label: 'Payment Failed' };
    case 'pending_payment':
      return { className: 'status-pending_payment', label: 'Pending Payment' };
    default:
      return { className: 'status-unknown', label: status || 'Unknown' };
  }
}

function OrdersContent() {
  const searchParams = useSearchParams();
  const [selectedCustomerId, setSelectedCustomerId] = useCustomer();
  const [tab, setTab] = useState(searchParams.get('tab') === 'inbox' ? 'inbox' : 'orders');
  const [unreadCount, setUnreadCount] = useState(0);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Order Detail Modal State
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // Fetch orders for the current customer
  const fetchCustomerOrders = useCallback(async (customerId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch(`/customers/${customerId}/orders`);
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || `Failed to fetch orders for customer ${customerId}.`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Keep the tab in sync with the ?tab= query (navbar Inbox link)
  useEffect(() => {
    setTab(searchParams.get('tab') === 'inbox' ? 'inbox' : 'orders');
  }, [searchParams]);

  // Fetch orders when the customer changes, then keep them fresh (cancellations, returns, new orders)
  useEffect(() => {
    let isMounted = true;

    async function load(silent) {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      try {
        const data = await apiFetch(`/customers/${selectedCustomerId}/orders`);
        if (isMounted) {
          setOrders(Array.isArray(data) ? data : []);
          setError(null);
        }
      } catch (err) {
        if (isMounted && !silent) {
          setError(err.message || `Failed to fetch orders for customer ${selectedCustomerId}.`);
        }
      } finally {
        if (isMounted && !silent) {
          setLoading(false);
        }
      }
    }

    const refresh = () => load(true);
    load(false);
    const timer = setInterval(refresh, 10000);
    window.addEventListener(DATA_REFRESH_EVENT, refresh);

    return () => {
      isMounted = false;
      clearInterval(timer);
      window.removeEventListener(DATA_REFRESH_EVENT, refresh);
    };
  }, [selectedCustomerId]);

  // Unread count for the Inbox tab badge
  useEffect(() => {
    let isMounted = true;
    async function loadUnread() {
      if (!selectedCustomerId || selectedCustomerId === 'none') {
        if (isMounted) setUnreadCount(0);
        return;
      }
      try {
        const data = await apiFetch(`/customers/${selectedCustomerId}/notifications`);
        if (isMounted) setUnreadCount(data?.unread_count || 0);
      } catch {
        /* ignore */
      }
    }
    loadUnread();
    const timer = setInterval(loadUnread, 10000);
    window.addEventListener(DATA_REFRESH_EVENT, loadUnread);
    return () => {
      isMounted = false;
      clearInterval(timer);
      window.removeEventListener(DATA_REFRESH_EVENT, loadUnread);
    };
  }, [selectedCustomerId, tab]);

  // Fetch individual order details via GET /orders/{order_id}
  const handleOpenDetail = useCallback(async (orderId) => {
    setSelectedOrderId(orderId);
    setOrderDetail(null);
    setDetailError(null);
    setDetailLoading(true);

    try {
      const data = await apiFetch(`/orders/${orderId}`);
      setOrderDetail(data);
    } catch (err) {
      setDetailError(err.message || `Failed to retrieve details for order ${orderId}.`);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedOrderId(null);
    setOrderDetail(null);
    setDetailError(null);
    setDetailLoading(false);
  }, []);

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && selectedOrderId) {
        handleCloseDetail();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedOrderId, handleCloseDetail]);

  return (
    <div className="container orders-page">
      {/* Header Bar */}
      <div className="orders-header-bar">
        <div>
          <h1 className="section-title" style={{ fontSize: '2rem' }}>My Orders</h1>
          <p className="section-desc">
            View live order history and statuses, and read replies from our support team.
          </p>
        </div>

        {/* Demo Customer Selector */}
        <div className="customer-selector-box">
          <label htmlFor="customer-select" className="customer-selector-label">
            <span>Customer Profile:</span>
          </label>
          <select
            id="customer-select"
            className="customer-select"
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
          >
            {CUSTOMER_PROFILES.map((cust) => (
              <option key={cust.id} value={cust.id}>
                {cust.id === 'none' ? 'Guest (no account)' : `${cust.name} (${cust.id})`}
              </option>
            ))}
          </select>
          <span className="demo-persona-badge">
            * Same customer as the AI chat, cart and checkout
          </span>
        </div>
      </div>

      {/* Orders / Inbox tabs */}
      <div className="orders-tabs" role="tablist" aria-label="My Orders sections">
        <Link
          href="/orders"
          role="tab"
          aria-selected={tab === 'orders'}
          className={`orders-tab ${tab === 'orders' ? 'active' : ''}`}
        >
          Orders
        </Link>
        <Link
          href="/orders?tab=inbox"
          role="tab"
          aria-selected={tab === 'inbox'}
          className={`orders-tab ${tab === 'inbox' ? 'active' : ''}`}
        >
          <span>Inbox</span>
          {unreadCount > 0 && <span className="nav-badge">{unreadCount}</span>}
        </Link>
      </div>

      {tab === 'inbox' && <Inbox customerId={selectedCustomerId} />}

      {tab === 'orders' && (
      <>
      {/* Loading State: Skeletons */}
      {loading && (
        <div className="orders-list" aria-label="Loading orders">
          {[1, 2].map((n) => (
            <div key={`order-skel-${n}`} className="skeleton-card" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div className="skeleton-box" style={{ width: '120px', height: '22px' }} />
                <div className="skeleton-box" style={{ width: '80px', height: '22px' }} />
              </div>
              <div className="skeleton-box" style={{ width: '60%', height: '18px', marginBottom: '0.5rem' }} />
              <div className="skeleton-box" style={{ width: '40%', height: '18px', marginBottom: '1rem' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem' }}>
                <div className="skeleton-box" style={{ width: '90px', height: '20px' }} />
                <div className="skeleton-box" style={{ width: '100px', height: '28px' }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State with Retry */}
      {!loading && error && (
        <div className="state-container" role="alert">
          <div className="state-icon" style={{ fontSize: '1rem' }}>Alert</div>
          <h2 className="state-title">Unable to Load Orders</h2>
          <p className="state-message">
            Could not retrieve orders from the server ({error}). Ensure the FastAPI backend is running on <code>http://127.0.0.1:8000</code>.
          </p>
          <button
            type="button"
            className="state-btn"
            onClick={() => fetchCustomerOrders(selectedCustomerId)}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && orders.length === 0 && (
        <div className="state-container">
          <div className="state-icon" style={{ fontSize: '1rem' }}>No Orders</div>
          <h2 className="state-title">No Orders Found</h2>
          <p className="state-message">
            No order records were found for customer ID <code>{selectedCustomerId}</code>.
            Switch to another customer persona above or browse products to place a simulated order.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="state-btn"
              onClick={() => setSelectedCustomerId('CUST001')}
            >
              Switch to CUST001
            </button>
            <Link href="/" className="state-btn" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
              Browse Catalog
            </Link>
          </div>
        </div>
      )}

      {/* Orders List */}
      {!loading && !error && orders.length > 0 && (
        <div className="orders-list">
          {orders.map((order) => {
            const statusInfo = getStatusInfo(order.status);
            return (
              <div key={order.id} className="order-card">
                <div className="order-card-header">
                  <div className="order-id-meta">
                    <span className="order-id-label">{order.id}</span>
                    <span className="order-date">Placed on: {formatDate(order.created_at)}</span>
                  </div>
                  <span className={`status-badge ${statusInfo.className}`}>
                    ● {statusInfo.label}
                  </span>
                </div>

                {/* Items Summary */}
                <div className="order-items-summary">
                  {order.items && order.items.map((item, idx) => (
                    <div key={`${order.id}-item-${idx}`} className="order-item-line">
                      <div className="order-item-desc">
                        <span className="order-item-qty">{item.quantity}x</span>
                        <span>{item.name}</span>
                      </div>
                      <span style={{ fontFamily: 'monospace', fontWeight: '500' }}>
                        ${(item.unit_price * item.quantity).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Card Footer */}
                <div className="order-card-footer">
                  <div className="order-total-block">
                    <span className="order-total-label">Total Amount:</span>
                    <span className="order-total-value">
                      ${typeof order.total_amount === 'number' ? order.total_amount.toFixed(2) : order.total_amount}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn-order-detail"
                    onClick={() => handleOpenDetail(order.id)}
                    aria-label={`View details for order ${order.id}`}
                  >
                    <span>View Details</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      </>
      )}

      {/* Order Detail Modal */}
      {selectedOrderId && (
        <div
          className="modal-overlay"
          onClick={handleCloseDetail}
          role="dialog"
          aria-modal="true"
          aria-labelledby="order-modal-title"
        >
          <div
            className="modal-dialog"
            style={{ maxWidth: '580px' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="modal-header-info">
                <span className="modal-category-tag">Order Details</span>
                <span className="modal-product-id">{selectedOrderId}</span>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={handleCloseDetail}
                aria-label="Close order details"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              {detailLoading && (
                <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
                  <h3 className="state-title">Loading Order Information</h3>
                  <p className="state-message">Fetching details from FastAPI backend...</p>
                </div>
              )}

              {detailError && !detailLoading && (
                <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
                  <h3 className="state-title">Failed to Load Order</h3>
                  <p className="state-message">{detailError}</p>
                  <button
                    type="button"
                    className="state-btn"
                    onClick={() => handleOpenDetail(selectedOrderId)}
                  >
                    Retry
                  </button>
                </div>
              )}

              {orderDetail && !detailLoading && (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 id="order-modal-title" className="modal-title">
                      Order #{orderDetail.id}
                    </h3>
                    <span className={`status-badge ${getStatusInfo(orderDetail.status).className}`}>
                      ● {getStatusInfo(orderDetail.status).label}
                    </span>
                  </div>

                  {/* Order Metadata Grid */}
                  <div className="modal-details-grid">
                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Customer ID</span>
                      <span className="modal-grid-val" style={{ fontFamily: 'monospace' }}>
                        {orderDetail.customer_id}
                      </span>
                    </div>
                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Status</span>
                      <span className="modal-grid-val">
                        {getStatusInfo(orderDetail.status).label}
                      </span>
                    </div>
                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Order Date</span>
                      <span className="modal-grid-val" style={{ fontSize: '0.85rem' }}>
                        {formatDate(orderDetail.created_at)}
                      </span>
                    </div>
                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Total Amount</span>
                      <span className="modal-grid-val" style={{ color: 'var(--accent-primary)', fontWeight: '700' }}>
                        ${typeof orderDetail.total_amount === 'number' ? orderDetail.total_amount.toFixed(2) : orderDetail.total_amount}
                      </span>
                    </div>
                  </div>

                  {/* Items Breakdown Table */}
                  <div>
                    <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: '600' }}>
                      Purchased Items ({orderDetail.items ? orderDetail.items.length : 0})
                    </h4>
                    <table className="order-modal-table">
                      <thead>
                        <tr>
                          <th>Item</th>
                          <th style={{ textAlign: 'center' }}>Qty</th>
                          <th style={{ textAlign: 'right' }}>Unit Price</th>
                          <th style={{ textAlign: 'right' }}>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orderDetail.items && orderDetail.items.map((item, idx) => (
                          <tr key={`${orderDetail.id}-modal-item-${idx}`}>
                            <td>
                              <div style={{ fontWeight: '500' }}>{item.name}</div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                {item.product_id}
                              </div>
                            </td>
                            <td style={{ textAlign: 'center' }}>{item.quantity}</td>
                            <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                              ${typeof item.unit_price === 'number' ? item.unit_price.toFixed(2) : item.unit_price}
                            </td>
                            <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: '600' }}>
                              ${(item.quantity * item.unit_price).toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Informational Notice */}
                  <div className="order-modal-notice">
                    <span>
                      Need to track, cancel, or return this order? Ask the{' '}
                      <Link href={`/support?query=${encodeURIComponent(`Where is my order ${orderDetail.id}?`)}`} onClick={handleCloseDetail} style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>
                        AI Support Concierge
                      </Link>{' '}
                      using order reference <strong>{orderDetail.id}</strong>.
                    </span>
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="modal-btn-dismiss"
                onClick={handleCloseDetail}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OrdersPage() {
  return (
    <Suspense
      fallback={
        <div className="container orders-page">
          <p className="section-desc">Loading your orders...</p>
        </div>
      }
    >
      <OrdersContent />
    </Suspense>
  );
}
