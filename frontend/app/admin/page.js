'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { apiFetch } from '../../lib/api';
import { getProductImageData } from '../../lib/unsplash';
import {
  IconDashboard,
  IconUsers,
  IconPackage,
  IconCreditCard,
  IconRefresh,
  IconSearch,
  IconCheck,
  IconAlertTriangle,
  IconShield,
  IconFileText,
  IconEdit,
} from '../../components/Icons';

const AGENT_NAME = 'Supervisor Desk';

export default function SupervisorDashboard() {
  // Operational state
  const [metrics, setMetrics] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [payments, setPayments] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Main Section Navigation
  const [activeSection, setActiveSection] = useState('tickets'); // 'tickets' | 'customers' | 'products' | 'orders' | 'payments' | 'policies'

  // Sub-filters
  const [ticketStatusTab, setTicketStatusTab] = useState('all');
  const [customerSearch, setCustomerSearch] = useState('');
  const [productCategoryFilter, setProductCategoryFilter] = useState('All');
  const [productSearch, setProductSearch] = useState('');
  const [orderStatusFilter, setOrderStatusFilter] = useState('all');
  const [orderSearch, setOrderSearch] = useState('');
  const [policyCategoryFilter, setPolicyCategoryFilter] = useState('All');
  const [policySearch, setPolicySearch] = useState('');

  // Policy Modal & Edit State
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [isEditingPolicy, setIsEditingPolicy] = useState(false);
  const [policyForm, setPolicyForm] = useState({
    title: '',
    intent: '',
    guidance: '',
    keywords: '',
  });
  const [savingPolicy, setSavingPolicy] = useState(false);
  const [policySuccess, setPolicySuccess] = useState(null);

  // Ticket update state
  const [updatingTicketId, setUpdatingTicketId] = useState(null);
  const [updateSuccess, setUpdateSuccess] = useState(null);

  // Human-in-the-loop case workspace (popup)
  const [caseTicketId, setCaseTicketId] = useState(null);
  const [caseFile, setCaseFile] = useState(null);
  const [caseLoading, setCaseLoading] = useState(false);
  const [caseError, setCaseError] = useState(null);
  const [resolutionText, setResolutionText] = useState('');
  const [resolving, setResolving] = useState(false);

  // Fetch all operations data
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, t, c, p, o, pay, pol] = await Promise.all([
        apiFetch('/admin/metrics').catch(() => null),
        apiFetch('/admin/tickets').catch(() => []),
        apiFetch('/customers').catch(() => []),
        apiFetch('/products').catch(() => []),
        apiFetch('/orders').catch(() => []),
        apiFetch('/payments').catch(() => []),
        apiFetch('/admin/policies').catch(() => []),
      ]);

      setMetrics(m);
      setTickets(Array.isArray(t) ? t : []);
      setCustomers(Array.isArray(c) ? c : []);
      setProducts(Array.isArray(p) ? p : []);
      setOrders(Array.isArray(o) ? o : []);
      setPayments(Array.isArray(pay) ? pay : []);
      setPolicies(Array.isArray(pol) ? pol : []);
    } catch (err) {
      setError(err.message || 'Failed to connect to Supervisor Operations backend.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 20000); // Polling every 20s
    return () => clearInterval(interval);
  }, [loadData]);

  // Update ticket status handler
  const handleUpdateStatus = async (ticketId, newStatus) => {
    setUpdatingTicketId(ticketId);
    setUpdateSuccess(null);
    try {
      await apiFetch(`/admin/tickets/${ticketId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({
          new_status: newStatus,
          notes: `Status updated to ${newStatus} via Supervisor Desk`,
          assigned_to: 'agent_supervisor',
        }),
      });
      setUpdateSuccess(`Ticket ${ticketId} updated to ${newStatus}`);
      await loadData();
    } catch (err) {
      alert(`Failed to update ticket: ${err.message}`);
    } finally {
      setUpdatingTicketId(null);
    }
  };

  // Open the case workspace popup with the full case file
  const openCase = useCallback(async (ticketId) => {
    setCaseTicketId(ticketId);
    setCaseFile(null);
    setCaseError(null);
    setResolutionText('');
    setCaseLoading(true);
    try {
      const data = await apiFetch(`/admin/tickets/${ticketId}/case`);
      setCaseFile(data);
    } catch (err) {
      setCaseError(err.message || 'Could not load the case file.');
    } finally {
      setCaseLoading(false);
    }
  }, []);

  const closeCase = () => {
    if (resolving) return;
    setCaseTicketId(null);
    setCaseFile(null);
    setCaseError(null);
    setResolutionText('');
  };

  // "Take Case": claim it (customer is notified) and open the workspace
  const handleTakeCase = async (ticketId) => {
    setUpdatingTicketId(ticketId);
    setUpdateSuccess(null);
    try {
      await apiFetch(`/admin/tickets/${ticketId}/take`, {
        method: 'POST',
        body: JSON.stringify({ agent_name: AGENT_NAME }),
      });
      await loadData();
      await openCase(ticketId);
    } catch (err) {
      alert(`Failed to take case: ${err.message}`);
    } finally {
      setUpdatingTicketId(null);
    }
  };

  // Resolve with a written answer that lands in the customer's inbox
  const handleResolveCase = async () => {
    if (!caseTicketId || !resolutionText.trim()) return;
    setResolving(true);
    try {
      const res = await apiFetch(`/admin/tickets/${caseTicketId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_message: resolutionText.trim(), agent_name: AGENT_NAME }),
      });
      setUpdateSuccess(res.message || `Case ${caseTicketId} resolved.`);
      setResolving(false);
      setCaseTicketId(null);
      setCaseFile(null);
      setResolutionText('');
      await loadData();
    } catch (err) {
      setResolving(false);
      alert(`Failed to resolve case: ${err.message}`);
    }
  };

  // Filtered tickets
  const filteredTickets = useMemo(() => {
    return tickets.filter((t) => {
      if (ticketStatusTab === 'all') return true;
      if (ticketStatusTab === 'open') return t.status === 'open';
      if (ticketStatusTab === 'in_progress') return t.status === 'in_progress' || t.status === 'assigned';
      if (ticketStatusTab === 'resolved') return t.status === 'resolved' || t.status === 'closed';
      return true;
    });
  }, [tickets, ticketStatusTab]);

  // Filtered customers
  const filteredCustomers = useMemo(() => {
    if (!customerSearch.trim()) return customers;
    const q = customerSearch.toLowerCase().trim();
    return customers.filter(
      (c) =>
        c.name?.toLowerCase().includes(q) ||
        c.email?.toLowerCase().includes(q) ||
        c.id?.toLowerCase().includes(q) ||
        c.tier?.toLowerCase().includes(q)
    );
  }, [customers, customerSearch]);

  // Filtered products
  const filteredProducts = useMemo(() => {
    let result = [...products];
    if (productCategoryFilter !== 'All') {
      result = result.filter(
        (p) => p.category?.toLowerCase() === productCategoryFilter.toLowerCase()
      );
    }
    if (productSearch.trim()) {
      const q = productSearch.toLowerCase().trim();
      result = result.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.id?.toLowerCase().includes(q) ||
          p.category?.toLowerCase().includes(q)
      );
    }
    return result;
  }, [products, productCategoryFilter, productSearch]);

  // Filtered orders
  const filteredOrders = useMemo(() => {
    let result = [...orders];
    if (orderStatusFilter !== 'all') {
      result = result.filter(
        (o) => o.status?.toLowerCase() === orderStatusFilter.toLowerCase()
      );
    }
    if (orderSearch.trim()) {
      const q = orderSearch.toLowerCase().trim();
      result = result.filter(
        (o) =>
          o.id?.toLowerCase().includes(q) ||
          o.customer_id?.toLowerCase().includes(q) ||
          o.status?.toLowerCase().includes(q)
      );
    }
    return result;
  }, [orders, orderStatusFilter, orderSearch]);

  // Unique policy categories for filter
  const policyCategories = useMemo(() => {
    const set = new Set();
    policies.forEach((p) => {
      if (p.category) set.add(p.category);
      if (p.intent) set.add(p.intent);
    });
    return ['All', ...Array.from(set)];
  }, [policies]);

  // Filtered policies
  const filteredPolicies = useMemo(() => {
    let result = [...policies];
    if (policyCategoryFilter !== 'All') {
      result = result.filter(
        (p) =>
          p.category?.toLowerCase() === policyCategoryFilter.toLowerCase() ||
          p.intent?.toLowerCase() === policyCategoryFilter.toLowerCase()
      );
    }
    if (policySearch.trim()) {
      const q = policySearch.toLowerCase().trim();
      result = result.filter(
        (p) =>
          p.title?.toLowerCase().includes(q) ||
          p.id?.toLowerCase().includes(q) ||
          p.intent?.toLowerCase().includes(q) ||
          p.guidance?.toLowerCase().includes(q) ||
          p.keywords?.some((k) => k.toLowerCase().includes(q))
      );
    }
    return result;
  }, [policies, policyCategoryFilter, policySearch]);

  // Open Edit Modal for a policy
  const handleOpenEditPolicy = (policy) => {
    setSelectedPolicy(policy);
    setPolicyForm({
      title: policy.title || '',
      intent: policy.intent || policy.category || '',
      guidance: policy.guidance || '',
      keywords: Array.isArray(policy.keywords) ? policy.keywords.join(', ') : '',
    });
    setIsEditingPolicy(true);
    setPolicySuccess(null);
  };

  // Save Policy changes
  const handleSavePolicy = async (e) => {
    e?.preventDefault();
    if (!selectedPolicy) return;

    setSavingPolicy(true);
    setPolicySuccess(null);

    const parsedKeywords = policyForm.keywords
      .split(',')
      .map((k) => k.trim())
      .filter(Boolean);

    try {
      const updated = await apiFetch(`/admin/policies/${selectedPolicy.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          title: policyForm.title.trim(),
          intent: policyForm.intent.trim(),
          guidance: policyForm.guidance.trim(),
          keywords: parsedKeywords,
        }),
      });

      // Update in local state
      setPolicies((prev) =>
        prev.map((p) => (p.id === selectedPolicy.id ? { ...p, ...updated.policy } : p))
      );

      setPolicySuccess(`Policy "${policyForm.title}" updated successfully! The AI will now refer to this updated guidance immediately.`);
      setIsEditingPolicy(false);
      setSelectedPolicy(null);
    } catch (err) {
      alert(`Failed to save policy: ${err.message}`);
    } finally {
      setSavingPolicy(false);
    }
  };

  return (
    <div className="supervisor-desk-container">
      {/* Top Header Bar */}
      <header className="supervisor-header">
        <div>
          <div className="supervisor-title-row">
            <h1 className="supervisor-title">Supervisor Operations Desk</h1>
            <span className="live-ops-badge">Live Multi-Agent Oversight</span>
          </div>
          <p className="supervisor-subtitle">
            Complete operational visibility into customer accounts, inventory catalog, order fulfillment, payment statements, and agent escalation cases.
          </p>
        </div>

        <div className="supervisor-header-actions">
          <button type="button" onClick={loadData} className="btn-ops-refresh" title="Reload live database records">
            <IconRefresh size={14} />
            <span>Refresh Data</span>
          </button>
          <button
            type="button"
            onClick={async () => {
              if (window.confirm("Reset the demo? Orders, stock, tickets, inbox messages, CSAT scores and AI policies go back to their clean starting state.")) {
                try {
                  const res = await apiFetch('/admin/reset', { method: 'POST' });
                  setUpdateSuccess(res.message || "Database reset to initial baseline successfully.");
                  await loadData();
                } catch (err) {
                  alert(`Failed to reset database: ${err.message}`);
                }
              }
            }}
            className="btn-ops-reset"
            title="Restore all mock database records to initial baseline"
          >
            <IconRefresh size={14} />
            <span>Reset Demo DB</span>
          </button>
          <Link href="/support" className="btn-ops-concierge">
            Open AI Concierge &rarr;
          </Link>
        </div>
      </header>


      {/* Notifications */}
      {error && (
        <div className="ops-banner error" role="alert">
          <IconAlertTriangle size={18} />
          <span>Alert: {error} &mdash; Please verify the FastAPI backend is active on port 8000.</span>
        </div>
      )}

      {updateSuccess && (
        <div className="ops-banner success">
          <IconCheck size={18} />
          <span>{updateSuccess}</span>
        </div>
      )}

      {policySuccess && (
        <div className="ops-banner success">
          <IconCheck size={18} />
          <span>{policySuccess}</span>
        </div>
      )}


      {/* Root-Cause Anomaly Detection Banner */}
      {metrics?.root_cause_alerts && metrics.root_cause_alerts.length > 0 && (
        <div className="root-cause-alert-box">
          <div className="alert-badge-row">
            <span className="badge-alert-label">INCIDENT DETECTED</span>
            <strong className="alert-type-title">
              Root Cause Discovery: {metrics.root_cause_alerts[0].type}
            </strong>
            <span className="alert-severity-pill">
              {metrics.root_cause_alerts[0].severity?.toUpperCase()}
            </span>
          </div>
          <p className="alert-desc-text">
            {metrics.root_cause_alerts[0].description}
          </p>
          <div className="alert-action-rec">
            <strong>Recommended Ops Action:</strong> {metrics.root_cause_alerts[0].recommended_action}
          </div>
        </div>
      )}

      {/* Operations KPI Metrics Cards */}
      <div className="ops-kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">Active Support Cases</span>
          <div className="kpi-value">{metrics?.total_tickets ?? (loading ? '...' : 0)}</div>
          <span className="kpi-subtext">
            {metrics?.open_tickets ?? 0} open &bull; {metrics?.in_progress_tickets ?? 0} in progress
          </span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Autonomous Resolution Rate</span>
          <div className="kpi-value kpi-success">
            {metrics?.resolution_rate_percent ?? 0}%
          </div>
          <div className="kpi-progress-bar">
            <div
              className="kpi-progress-fill"
              style={{ width: `${metrics?.resolution_rate_percent ?? 0}%` }}
            />
          </div>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Human Escalation Rate</span>
          <div className="kpi-value">{metrics?.escalation_rate_percent ?? 0}%</div>
          <span className="kpi-subtext">Rerouted to billing &amp; logistics specialists</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Customer Satisfaction (CSAT)</span>
          <div className="kpi-value kpi-warning">
            {metrics?.average_csat ?? 5.0} / 5.0
          </div>
          <span className="kpi-subtext">
            Across {metrics?.csat_review_count ?? 1} verified customer evaluations
          </span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">SLA Compliance Health</span>
          <div
            className={`kpi-value ${
              (metrics?.sla_breach_count ?? 0) > 0 ? 'kpi-error' : 'kpi-success'
            }`}
          >
            {metrics?.sla_breach_count ?? 0} Breaches
          </div>
          <span className="kpi-subtext">SLA Target: VIP (2h), Standard (8h)</span>
        </div>
      </div>

      {/* Primary Supervisor Section Tabs */}
      <nav className="supervisor-nav-tabs" role="tablist" aria-label="Supervisor Sections">
        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'tickets'}
          className={`tab-btn ${activeSection === 'tickets' ? 'active' : ''}`}
          onClick={() => setActiveSection('tickets')}
        >
          <span>Support Tickets</span>
          <span className="tab-count-badge">{tickets.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'customers'}
          className={`tab-btn ${activeSection === 'customers' ? 'active' : ''}`}
          onClick={() => setActiveSection('customers')}
        >
          <span>Customer Accounts</span>
          <span className="tab-count-badge">{customers.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'products'}
          className={`tab-btn ${activeSection === 'products' ? 'active' : ''}`}
          onClick={() => setActiveSection('products')}
        >
          <span>Product Inventory</span>
          <span className="tab-count-badge">{products.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'orders'}
          className={`tab-btn ${activeSection === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveSection('orders')}
        >
          <span>All Orders</span>
          <span className="tab-count-badge">{orders.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'payments'}
          className={`tab-btn ${activeSection === 'payments' ? 'active' : ''}`}
          onClick={() => setActiveSection('payments')}
        >
          <span>Payment Statements</span>
          <span className="tab-count-badge">{payments.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeSection === 'policies'}
          className={`tab-btn ${activeSection === 'policies' ? 'active' : ''}`}
          onClick={() => setActiveSection('policies')}
        >
          <IconFileText size={15} />
          <span>AI Policies &amp; Rules</span>
          <span className="tab-count-badge">{policies.length}</span>
        </button>
      </nav>


      {/* =========================================================================
          SECTION 1: SUPPORT TICKETS & ESCALATIONS
         ========================================================================= */}
      {activeSection === 'tickets' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">Support Ticket Lifecycle &amp; Resolution Tracking</h2>
              <p className="card-desc">
                Review automated escalations and transition cases through Opened &rarr; Assigned &rarr; In Progress &rarr; Resolved.
              </p>
            </div>

            <div className="sub-filter-pills">
              {['all', 'open', 'in_progress', 'resolved'].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`sub-pill ${ticketStatusTab === tab ? 'active' : ''}`}
                  onClick={() => setTicketStatusTab(tab)}
                >
                  {tab.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="table-wrapper">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Title &amp; Issue Summary</th>
                  <th>Customer / Order</th>
                  <th>Priority</th>
                  <th>Assigned Team</th>
                  <th>Status</th>
                  <th>Supervisor Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="empty-table-cell">
                      No support tickets found matching filter '{ticketStatusTab}'.
                    </td>
                  </tr>
                ) : (
                  filteredTickets.map((t) => {
                    const isUpdating = updatingTicketId === t.ticket_id;
                    return (
                      <tr key={t.ticket_id}>
                        <td>
                          <code className="code-cell">{t.ticket_id}</code>
                        </td>
                        <td style={{ maxWidth: '280px' }}>
                          <div className="ticket-title-text">{t.title}</div>
                          <div className="ticket-reason-sub">{t.escalation_reason}</div>
                        </td>
                        <td>
                          <div style={{ fontWeight: '500' }}>{t.customer_id || 'Guest'}</div>
                          {t.order_id && <code className="code-sub">{t.order_id}</code>}
                        </td>
                        <td>
                          <span className={`priority-pill ${t.priority || 'medium'}`}>
                            {t.priority || 'medium'}
                          </span>
                        </td>
                        <td>
                          <span className="team-pill">
                            {(t.target_team || 'General').replace('_', ' ').toUpperCase()}
                          </span>
                        </td>
                        <td>
                          <span className={`status-pill-badge ${t.status}`}>
                            {t.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <div className="action-button-group">
                            {t.status === 'open' && (
                              <button
                                type="button"
                                disabled={isUpdating}
                                onClick={() => handleTakeCase(t.ticket_id)}
                                className="btn-action-status in_progress"
                              >
                                {isUpdating ? 'Taking...' : 'Take Case'}
                              </button>
                            )}
                            {(t.status === 'in_progress' || t.status === 'assigned' || t.status === 'pending_customer') && (
                              <button
                                type="button"
                                disabled={isUpdating}
                                onClick={() => openCase(t.ticket_id)}
                                className="btn-action-status resolved"
                              >
                                Open Case
                              </button>
                            )}
                            {(t.status === 'resolved' || t.status === 'closed') && (
                              <button
                                type="button"
                                onClick={() => openCase(t.ticket_id)}
                                className="btn-action-status"
                              >
                                View
                              </button>
                            )}
                            {t.status === 'resolved' && (
                              <button
                                type="button"
                                disabled={isUpdating}
                                onClick={() => handleUpdateStatus(t.ticket_id, 'closed')}
                                className="btn-action-status closed"
                              >
                                Close
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* =========================================================================
          SECTION 2: CUSTOMER DIRECTORY & ACCOUNTS
         ========================================================================= */}
      {activeSection === 'customers' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">Customer Directory &amp; Tier Profiles</h2>
              <p className="card-desc">
                Review registered customer tiers, contact channels, active memberships, and order histories.
              </p>
            </div>

            <div className="search-wrap">
              <IconSearch size={15} />
              <input
                type="text"
                placeholder="Search by customer name, email, ID..."
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
                className="table-search-input"
              />
            </div>
          </div>

          <div className="table-wrapper">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Customer Name</th>
                  <th>Email Address</th>
                  <th>Phone</th>
                  <th>Customer Tier</th>
                  <th>Subscription</th>
                  <th>Account Status</th>
                  <th>Member Since</th>
                  <th>Orders</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="empty-table-cell">
                      No customer records match query "{customerSearch}".
                    </td>
                  </tr>
                ) : (
                  filteredCustomers.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <code className="code-cell">{c.id}</code>
                      </td>
                      <td>
                        <strong>{c.name}</strong>
                      </td>
                      <td>
                        <span className="email-text">{c.email}</span>
                      </td>
                      <td>{c.phone || '&mdash;'}</td>
                      <td>
                        <span className={`tier-badge ${c.tier?.toLowerCase()}`}>
                          {c.tier?.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <span className={`sub-status-pill ${c.subscription?.toLowerCase()}`}>
                          {c.subscription?.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <span className="status-pill-badge active">{c.account_status}</span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(c.joined_date).toLocaleDateString([], {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-table-link"
                          onClick={() => {
                            setOrderSearch(c.id);
                            setActiveSection('orders');
                          }}
                        >
                          View Orders &rarr;
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* =========================================================================
          SECTION 3: PRODUCT INVENTORY & STOCK HEALTH
         ========================================================================= */}
      {activeSection === 'products' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">Product Inventory &amp; Stock Levels</h2>
              <p className="card-desc">
                Real-time catalog pricing, warehouse stock counts, category distribution, and availability health.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div className="sub-filter-pills">
                {['All', 'Electronics', 'Apparel', 'Home & Kitchen'].map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    className={`sub-pill ${productCategoryFilter === cat ? 'active' : ''}`}
                    onClick={() => setProductCategoryFilter(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              <div className="search-wrap">
                <IconSearch size={15} />
                <input
                  type="text"
                  placeholder="Search SKU, product name..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  className="table-search-input"
                />
              </div>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>SKU / Product ID</th>
                  <th>Product Details</th>
                  <th>Category</th>
                  <th>Unit Price</th>
                  <th>Stock Quantity</th>
                  <th>Inventory Status</th>
                  <th>Storefront Link</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="empty-table-cell">
                      No products found matching criteria.
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((p) => {
                    const imgData = getProductImageData(p);
                    const isOutOfStock = p.stock === 0;
                    const isLowStock = p.stock > 0 && p.stock <= 20;

                    return (
                      <tr key={p.id}>
                        <td>
                          <code className="code-cell">{p.id}</code>
                        </td>
                        <td>
                          <div className="product-table-cell">
                            <img
                              src={imgData.thumbnail}
                              alt={p.name}
                              className="product-thumb-img"
                            />
                            <div>
                              <div className="ticket-title-text">{p.name}</div>
                              <div className="product-rating-inline">
                                <span>&#9733; {imgData.rating}</span>
                                <span>({imgData.reviewsCount} reviews)</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="team-pill">{p.category}</span>
                        </td>
                        <td>
                          <strong>${typeof p.price === 'number' ? p.price.toFixed(2) : p.price}</strong>
                        </td>
                        <td>
                          <span style={{ fontFamily: 'monospace', fontWeight: '700', fontSize: '0.9rem' }}>
                            {p.stock} units
                          </span>
                        </td>
                        <td>
                          <span
                            className={`stock-badge ${
                              isOutOfStock
                                ? 'out-of-stock'
                                : isLowStock
                                ? 'low-stock'
                                : 'in-stock'
                            }`}
                          >
                            &bull; {isOutOfStock ? 'Out of Stock' : isLowStock ? 'Low Stock' : 'Optimal'}
                          </span>
                        </td>
                        <td>
                          <Link href="/products" className="btn-table-link">
                            Inspect in Catalog &rarr;
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* =========================================================================
          SECTION 4: ALL ORDERS & FULFILLMENT LOG
         ========================================================================= */}
      {activeSection === 'orders' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">Orders Fulfillment &amp; Dispatch Log</h2>
              <p className="card-desc">
                Centralized transaction log showing line items, order progression, total values, and customer IDs.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <div className="sub-filter-pills">
                {['all', 'delivered', 'processing', 'shipped', 'cancelled', 'payment_failed', 'pending_payment'].map((st) => (
                  <button
                    key={st}
                    type="button"
                    className={`sub-pill ${orderStatusFilter === st ? 'active' : ''}`}
                    onClick={() => setOrderStatusFilter(st)}
                  >
                    {st.replace('_', ' ')}
                  </button>
                ))}
              </div>

              <div className="search-wrap">
                <IconSearch size={15} />
                <input
                  type="text"
                  placeholder="Search by Order ID, Customer ID..."
                  value={orderSearch}
                  onChange={(e) => setOrderSearch(e.target.value)}
                  className="table-search-input"
                />
              </div>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Order Reference</th>
                  <th>Customer ID</th>
                  <th>Purchased Items</th>
                  <th>Order Value</th>
                  <th>Fulfillment Status</th>
                  <th>Placed Timestamp</th>
                  <th>Concierge Inquiry</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="empty-table-cell">
                      No orders found matching current filters.
                    </td>
                  </tr>
                ) : (
                  filteredOrders.map((o) => (
                    <tr key={o.id}>
                      <td>
                        <code className="code-cell">{o.id}</code>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-table-link"
                          onClick={() => {
                            setCustomerSearch(o.customer_id);
                            setActiveSection('customers');
                          }}
                        >
                          {o.customer_id}
                        </button>
                      </td>
                      <td>
                        <div className="order-items-summary">
                          {o.items?.map((it, idx) => (
                            <div key={idx} className="item-row-sub">
                              <span>{it.quantity}x {it.name}</span>
                              <code>(${it.unit_price?.toFixed(2)})</code>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td>
                        <strong>${typeof o.total_amount === 'number' ? o.total_amount.toFixed(2) : o.total_amount}</strong>
                      </td>
                      <td>
                        <span className={`status-pill-badge ${o.status}`}>
                          {o.status?.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(o.created_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td>
                        <Link
                          href={`/support?query=${encodeURIComponent(
                            `Where is my order ${o.id}?`
                          )}`}
                          className="btn-table-link"
                        >
                          Query AI Concierge &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* =========================================================================
          SECTION 5: PAYMENT RECORDS & SETTLEMENTS
         ========================================================================= */}
      {activeSection === 'payments' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">Payment Statements &amp; Gateway Transactions</h2>
              <p className="card-desc">
                Payment gateway authorization records, transaction references, amounts, and settlement statuses.
              </p>
            </div>
          </div>

          <div className="table-wrapper">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Payment ID</th>
                  <th>Order Reference</th>
                  <th>Amount</th>
                  <th>Payment Method</th>
                  <th>Transaction Reference</th>
                  <th>Status</th>
                  <th>Authorization Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="empty-table-cell">
                      No payment records available.
                    </td>
                  </tr>
                ) : (
                  payments.map((pay) => (
                    <tr key={pay.id}>
                      <td>
                        <code className="code-cell">{pay.id}</code>
                      </td>
                      <td>
                        <code className="code-sub">{pay.order_id}</code>
                      </td>
                      <td>
                        <strong>${typeof pay.amount === 'number' ? pay.amount.toFixed(2) : pay.amount}</strong>
                      </td>
                      <td>
                        <span className="team-pill">
                          {pay.payment_method?.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {pay.transaction_ref}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`status-pill-badge ${
                            pay.status === 'successful' || pay.status === 'success' ? 'resolved' : 'open'
                          }`}
                        >
                          {pay.status?.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(pay.timestamp).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* =========================================================================
          SECTION 6: AI POLICIES & KNOWLEDGE BASE OVERSIGHT
         ========================================================================= */}
      {activeSection === 'policies' && (
        <section className="ops-data-card">
          <div className="card-header-bar">
            <div>
              <h2 className="card-title">AI Policies &amp; Knowledge Base Grounding</h2>
              <p className="card-desc">
                Review the exact business rules, SLA requirements, and resolution directives that the AI Concierge consults before answering customers.
              </p>
            </div>
            <div className="card-header-actions">
              <span className="live-pill-tag">Live Policy Grounding</span>
            </div>
          </div>

          <div className="policy-info-banner">
            <IconShield size={16} />
            <span>
              <strong>Supervisor Control:</strong> Any edits made to these policies take effect immediately. The Multi-Agent reasoning engine dynamically cites and adheres to updated guidance in live conversations.
            </span>
          </div>

          {/* Filter & Search Bar */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="sub-filter-pills">
              {policyCategories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`sub-pill ${policyCategoryFilter === cat ? 'active' : ''}`}
                  onClick={() => setPolicyCategoryFilter(cat)}
                >
                  {cat === 'All' ? 'All Policies' : cat.replace(/_/g, ' ')}
                </button>
              ))}
            </div>

            <div className="search-wrap">
              <IconSearch size={15} />
              <input
                type="text"
                placeholder="Search policies by title, ID, guidance or keyword..."
                value={policySearch}
                onChange={(e) => setPolicySearch(e.target.value)}
                className="table-search-input"
                style={{ minWidth: '320px' }}
              />
            </div>
          </div>


          {/* Policies Grid */}
          <div className="policies-grid">
            {filteredPolicies.length === 0 ? (
              <div className="policy-empty-state">
                No policy rules match your search criteria.
              </div>
            ) : (
              filteredPolicies.map((pol) => (
                <div key={pol.id} className="policy-card">
                  <div className="policy-card-header">
                    <div className="policy-header-left">
                      <span className="policy-id-tag">{pol.id}</span>
                      <span className="policy-intent-pill">
                        {(pol.intent || pol.category || 'GENERAL').replace(/_/g, ' ')}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleOpenEditPolicy(pol)}
                      className="btn-policy-edit"
                      title="Edit this AI policy"
                    >
                      <IconEdit size={13} />
                      <span>Edit Policy</span>
                    </button>
                  </div>

                  <h3 className="policy-title">{pol.title}</h3>

                  <div className="policy-guidance-container">
                    <span className="policy-guidance-label">AI Directive &amp; Customer Guidance:</span>
                    <p className="policy-guidance-text">{pol.guidance}</p>
                  </div>

                  {pol.keywords && pol.keywords.length > 0 && (
                    <div className="policy-keywords-row">
                      <span className="policy-keywords-label">Triggers:</span>
                      <div className="policy-keywords-chips">
                        {pol.keywords.map((kw, i) => (
                          <span key={i} className="policy-keyword-chip">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>
      )}


      {/* =========================================================================
          HUMAN-IN-THE-LOOP CASE WORKSPACE (popup)
         ========================================================================= */}
      {caseTicketId && (
        <div className="modal-backdrop" onClick={closeCase}>
          <div
            className="case-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="case-modal-title"
          >
            <div className="case-modal-header">
              <div>
                <span className="modal-badge">HUMAN REVIEW CASE</span>
                <h3 id="case-modal-title" className="modal-title">
                  {caseFile?.ticket?.title || caseTicketId}
                </h3>
                <div className="case-header-meta">
                  <code className="code-cell">{caseTicketId}</code>
                  {caseFile?.ticket && (
                    <>
                      <span className={`priority-pill ${caseFile.ticket.priority || 'medium'}`}>
                        {caseFile.ticket.priority || 'medium'}
                      </span>
                      <span className={`status-pill-badge ${caseFile.ticket.status}`}>
                        {caseFile.ticket.status?.replace('_', ' ')}
                      </span>
                      <span className="team-pill">
                        {(caseFile.ticket.target_team || 'General').replace('_', ' ').toUpperCase()}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <button
                type="button"
                className="btn-modal-close"
                onClick={closeCase}
                disabled={resolving}
                aria-label="Close case"
              >
                &times;
              </button>
            </div>

            <div className="case-modal-body">
              {caseLoading && <p className="case-muted">Loading case file...</p>}
              {caseError && <p className="cart-inline-error" role="alert">{caseError}</p>}

              {caseFile && (() => {
                const { ticket, customer, order, payments, policy, other_cases } = caseFile;
                const isFinished = ticket.status === 'resolved' || ticket.status === 'closed';
                return (
                  <>
                    <section className="case-section">
                      <h4 className="case-section-title">What the customer said</h4>
                      <blockquote className="case-quote">
                        {ticket.original_message || 'No message was recorded for this case.'}
                      </blockquote>
                    </section>

                    <section className="case-section">
                      <h4 className="case-section-title">Why the AI handed this to a human</h4>
                      <p className="case-text">{ticket.escalation_reason}</p>
                      {policy && (
                        <div className="case-policy">
                          <div className="case-policy-head">
                            <span className="policy-id-tag">{policy.id}</span>
                            <strong>{policy.title}</strong>
                          </div>
                          <p className="case-text">{policy.guidance}</p>
                        </div>
                      )}
                      {ticket.internal_notes && ticket.internal_notes !== ticket.escalation_reason && (
                        <p className="case-notes">
                          <strong>AI investigation notes:</strong> {ticket.internal_notes}
                        </p>
                      )}
                    </section>

                    <div className="case-grid">
                      <section className="case-section">
                        <h4 className="case-section-title">Customer</h4>
                        {customer ? (
                          <dl className="case-dl">
                            <div><dt>Name</dt><dd>{customer.name} ({customer.id})</dd></div>
                            <div><dt>Tier</dt><dd>{customer.tier?.toUpperCase()}</dd></div>
                            <div><dt>Email</dt><dd>{customer.email}</dd></div>
                            <div><dt>Phone</dt><dd>{customer.phone || 'n/a'}</dd></div>
                          </dl>
                        ) : (
                          <p className="case-muted">Guest session: no customer account linked, so no inbox delivery is possible.</p>
                        )}
                        {other_cases?.length > 0 && (
                          <p className="case-muted">
                            Other cases: {other_cases.map((c) => `${c.ticket_id} (${c.status})`).join(', ')}
                          </p>
                        )}
                      </section>

                      <section className="case-section">
                        <h4 className="case-section-title">Order &amp; payment</h4>
                        {order ? (
                          <>
                            <dl className="case-dl">
                              <div><dt>Order</dt><dd>{order.id}</dd></div>
                              <div><dt>Status</dt><dd>{order.status?.replace('_', ' ')}</dd></div>
                              <div><dt>Total</dt><dd>${order.total_amount?.toFixed(2)}</dd></div>
                              <div>
                                <dt>Items</dt>
                                <dd>{order.items?.map((it) => `${it.quantity}x ${it.name}`).join(', ')}</dd>
                              </div>
                            </dl>
                            {payments?.length > 0 && (
                              <ul className="case-payments">
                                {payments.map((pay) => (
                                  <li key={pay.id}>
                                    <code>{pay.id}</code> {pay.status} &bull; ${pay.amount?.toFixed(2)} &bull;{' '}
                                    {pay.payment_method?.replace('_', ' ')} &bull; {pay.transaction_ref}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </>
                        ) : (
                          <p className="case-muted">No order is attached to this case.</p>
                        )}
                      </section>
                    </div>

                    {ticket.history?.length > 0 && (
                      <section className="case-section">
                        <h4 className="case-section-title">Case history</h4>
                        <ul className="case-history">
                          {ticket.history.map((h, idx) => (
                            <li key={idx}>
                              <span className="case-history-time">
                                {new Date(h.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span>{h.notes || h.event}</span>
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}

                    <section className="case-section case-response">
                      <h4 className="case-section-title">
                        {isFinished ? 'Response sent to the customer' : 'Your response to the customer'}
                      </h4>
                      {isFinished ? (
                        <blockquote className="case-quote">
                          {ticket.resolution_message || 'This case was closed without a written response.'}
                          {ticket.resolved_by && <div className="case-muted">Resolved by {ticket.resolved_by}</div>}
                        </blockquote>
                      ) : (
                        <>
                          <textarea
                            className="modal-textarea case-textarea"
                            rows={6}
                            value={resolutionText}
                            onChange={(e) => setResolutionText(e.target.value)}
                            placeholder="Write the final answer or decision for the customer. It will be delivered to their Inbox under My Orders."
                            disabled={resolving}
                            aria-label="Response to the customer"
                          />
                          <span className="modal-help-text">
                            {ticket.customer_id
                              ? `Delivered to ${customer?.name || ticket.customer_id}'s Inbox when you resolve.`
                              : 'Guest case: there is no inbox to deliver this to.'}
                          </span>
                        </>
                      )}
                    </section>
                  </>
                );
              })()}
            </div>

            <div className="case-modal-footer">
              <button type="button" className="btn-modal-cancel" onClick={closeCase} disabled={resolving}>
                {caseFile && (caseFile.ticket.status === 'resolved' || caseFile.ticket.status === 'closed') ? 'Close' : 'Keep working later'}
              </button>
              {caseFile && caseFile.ticket.status !== 'resolved' && caseFile.ticket.status !== 'closed' && (
                <button
                  type="button"
                  className="btn-modal-save"
                  onClick={handleResolveCase}
                  disabled={resolving || !resolutionText.trim()}
                >
                  {resolving ? 'Sending...' : 'Resolve & Send to Customer'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          POLICY EDIT MODAL / DRAWER
         ========================================================================= */}
      {isEditingPolicy && selectedPolicy && (
        <div className="modal-backdrop" onClick={() => !savingPolicy && setIsEditingPolicy(false)}>
          <div
            className="policy-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-policy-title"
          >
            <div className="modal-header">
              <div>
                <span className="modal-badge">SUPERVISOR OVERRIDE</span>
                <h3 id="modal-policy-title" className="modal-title">
                  Edit AI Policy Directive ({selectedPolicy.id})
                </h3>
              </div>
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setIsEditingPolicy(false)}
                disabled={savingPolicy}
                aria-label="Close modal"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSavePolicy} className="policy-modal-form">
              <div className="modal-form-group">
                <label className="modal-label" htmlFor="policy-form-title">
                  Policy Title
                </label>
                <input
                  id="policy-form-title"
                  type="text"
                  required
                  value={policyForm.title}
                  onChange={(e) => setPolicyForm({ ...policyForm, title: e.target.value })}
                  className="modal-input"
                  placeholder="e.g. Return and Replacement Standard Policy"
                />
              </div>

              <div className="modal-form-group">
                <label className="modal-label" htmlFor="policy-form-intent">
                  Intent Category Tag
                </label>
                <input
                  id="policy-form-intent"
                  type="text"
                  required
                  value={policyForm.intent}
                  onChange={(e) => setPolicyForm({ ...policyForm, intent: e.target.value })}
                  className="modal-input"
                  placeholder="e.g. return_or_replacement, warranty, cancellation"
                />
                <span className="modal-help-text">
                  Matches customer intent classifications in the Multi-Agent Router.
                </span>
              </div>

              <div className="modal-form-group">
                <label className="modal-label" htmlFor="policy-form-guidance">
                  AI Directive &amp; Operational Rule
                </label>
                <textarea
                  id="policy-form-guidance"
                  required
                  rows={5}
                  value={policyForm.guidance}
                  onChange={(e) => setPolicyForm({ ...policyForm, guidance: e.target.value })}
                  className="modal-textarea"
                  placeholder="Specify the exact instructions and SLA terms the AI assistant must cite and adhere to..."
                />
                <span className="modal-help-text">
                  The AI assistant will strictly respect this rule when customers ask about this topic.
                </span>
              </div>

              <div className="modal-form-group">
                <label className="modal-label" htmlFor="policy-form-keywords">
                  Keyword / Phrase Triggers (comma-separated)
                </label>
                <input
                  id="policy-form-keywords"
                  type="text"
                  value={policyForm.keywords}
                  onChange={(e) => setPolicyForm({ ...policyForm, keywords: e.target.value })}
                  className="modal-input"
                  placeholder="e.g. return, exchange, refund, replace, damaged item"
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setIsEditingPolicy(false)}
                  disabled={savingPolicy}
                  className="btn-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingPolicy}
                  className="btn-modal-save"
                >
                  {savingPolicy ? 'Saving & Updating Knowledge Base...' : 'Save & Publish to AI'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );

}
