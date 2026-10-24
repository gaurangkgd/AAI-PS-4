'use client';

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ChatPanel from '../../components/ChatPanel';
import {
  IconPackage,
  IconReturn,
  IconCreditCard,
  IconShield,
  IconUsers,
  IconBolt,
  IconMail,
  IconPhone,
  IconCheck,
} from '../../components/Icons';
import { CUSTOMER_PROFILES, getCustomerProfile } from '../../lib/customerContext';

function SupportContent() {
  const searchParams = useSearchParams();
  const queryParam = searchParams.get('query');

  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST001');
  const [activeFaq, setActiveFaq] = useState(null);
  const [queryTrigger, setQueryTrigger] = useState(queryParam || '');

  const activeCustomer = getCustomerProfile(selectedCustomerId);

  const toggleFaq = (index) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  const handleSelectCustomer = (newId) => {
    setSelectedCustomerId(newId);
  };

  const handleRunSamplePrompt = (text) => {
    setQueryTrigger(text);
  };

  const FAQS = [
    {
      q: 'How fast does the NextStore AI Concierge resolve inquiries?',
      a: 'Our AI Concierge provides instantaneous, sub-second responses for order tracking, inventory queries, return authorizations, and cancellation requests. If your case requires specialized human inspection, our autonomous system instantly logs a ticket for supervisor review.',
    },
    {
      q: 'What is NextStore’s standard return & refund policy?',
      a: 'We offer a 30-day risk-free return window for all unused items in their original packaging. Once your account is linked or order ID is provided, you receive an instant pre-paid return authorization.',
    },
    {
      q: 'Can the AI cancel or modify an order without typing an Order ID?',
      a: 'Yes. When your customer account is selected from the dropdown, the AI automatically retrieves your active orders. Simply asking "Where is my order?" or "Cancel my order" will identify and resolve the appropriate order automatically.',
    },
    {
      q: 'How does escalation to a human supervisor work?',
      a: 'If a payment anomaly, damaged delivery, or out-of-policy exception occurs, the AI system creates a priority ticket and escalates the conversation context directly to our operations dashboard for human review.',
    },
  ];

  return (
    <div className="support-expanded-container">
      {/* Compact Top Header Bar — Space Efficient */}
      <section className="support-compact-header">
        <div className="support-header-left">
          <div className="support-status-indicator">
            <span className="live-dot" />
            <span>24/7 Intelligent Concierge Active</span>
          </div>
          <h1 className="support-page-title">Customer Support &amp; Concierge</h1>
          <p className="support-page-desc">
            Direct autonomous assistance for shipment tracking, cancellations, return authorizations, and customer context awareness.
          </p>
        </div>

        {/* Quick Service Assurances */}
        <div className="support-header-assurances">
          <div className="assurance-chip">
            <IconPackage size={15} />
            <span>Live Order Tracking</span>
          </div>
          <div className="assurance-chip">
            <IconReturn size={15} />
            <span>Automated Returns</span>
          </div>
          <div className="assurance-chip">
            <IconShield size={15} />
            <span>2-Year Warranty</span>
          </div>
          <div className="assurance-chip">
            <IconUsers size={15} />
            <span>Supervisor Escalation</span>
          </div>
        </div>
      </section>

      {/* Main Expansive Support Grid */}
      <div className="support-workspace-grid">
        {/* Left / Primary Column: Maximized Chat Console with Customer Context */}
        <div className="support-chat-viewport">
          <ChatPanel
            initialQuery={queryTrigger || queryParam}
            isExpanded={true}
            selectedCustomerId={selectedCustomerId}
            onCustomerChange={handleSelectCustomer}
            showCustomerSelector={true}
          />
        </div>

        {/* Right Column: Sleek Support Information Rail */}
        <aside className="support-side-rail">
          {/* Active Customer Persona & Orders Context Card */}
          <div className="support-rail-card customer-profile-card">
            <div className="rail-card-header-row">
              <h3 className="rail-card-title">Customer Context</h3>
              <span className="customer-tier-badge">{activeCustomer?.badge}</span>
            </div>

            <p className="rail-card-desc">
              Context is actively synced with the chat console. Inquiries about order status, delivery, or returns automatically target this account:
            </p>

            {/* Profile Overview Details */}
            {activeCustomer && activeCustomer.id !== 'none' ? (
              <div className="customer-context-details">
                <div className="customer-detail-row">
                  <span className="detail-key">Account:</span>
                  <span className="detail-val">{activeCustomer.name}</span>
                </div>
                <div className="customer-detail-row">
                  <span className="detail-key">Email:</span>
                  <span className="detail-val mono">{activeCustomer.email}</span>
                </div>

                {/* Orders List */}
                <div className="customer-orders-section">
                  <span className="customer-orders-heading">
                    Linked Orders ({activeCustomer.orders.length}):
                  </span>
                  {activeCustomer.orders.length > 0 ? (
                    <div className="customer-orders-list">
                      {activeCustomer.orders.map((ord) => (
                        <div key={ord.id} className="customer-order-item">
                          <div className="order-item-top">
                            <span className="order-item-id">{ord.id}</span>
                            <span className={`chip-badge ${ord.status}`}>{ord.status}</span>
                          </div>
                          <div className="order-item-desc">{ord.item}</div>
                          <div className="order-item-total">${ord.total.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="customer-no-orders-msg">
                      No active orders found for this customer account.
                    </div>
                  )}
                </div>

                {/* Context-Aware Prompt Suggestions */}
                <div className="context-quick-actions">
                  <span className="quick-actions-title">One-Click Tests (No ID needed):</span>
                  <div className="quick-action-buttons">
                    {activeCustomer.starterPrompts.map((p, idx) => (
                      <button
                        key={`action-${idx}`}
                        type="button"
                        className="quick-action-btn"
                        onClick={() => handleRunSamplePrompt(p.text)}
                      >
                        <span className="quick-action-tag">{p.tag}</span>
                        <span className="quick-action-text">{p.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="customer-guest-notice">
                <p>
                  <strong>Guest Mode Active:</strong> You are simulating an anonymous visitor. You will need to type specific Order IDs (e.g. <code>ORD1001</code>) in your message for tracking or actions.
                </p>
              </div>
            )}
          </div>

          {/* Service Guarantees */}
          <div className="support-rail-card">
            <h3 className="rail-card-title">Service Guarantees</h3>
            <ul className="rail-guarantees-list">
              <li>
                <div className="rail-g-icon">
                  <IconBolt size={16} />
                </div>
                <div>
                  <strong>Autonomous Order Resolution</strong>
                  <p>Infers orders from active customer context with sub-second response times.</p>
                </div>
              </li>
              <li>
                <div className="rail-g-icon">
                  <IconShield size={16} />
                </div>
                <div>
                  <strong>Confirmation Guardrails</strong>
                  <p>Actions like cancellations always require customer consent before executing.</p>
                </div>
              </li>
              <li>
                <div className="rail-g-icon">
                  <IconUsers size={16} />
                </div>
                <div>
                  <strong>Operations Desk Fallback</strong>
                  <p>Payment failures or escalated issues automatically route to supervisors.</p>
                </div>
              </li>
            </ul>
          </div>

          {/* FAQs Accordion */}
          <div className="support-rail-card">
            <h3 className="rail-card-title">Frequently Asked Questions</h3>
            <div className="rail-faq-list">
              {FAQS.map((faq, index) => (
                <div
                  key={index}
                  className={`rail-faq-item ${activeFaq === index ? 'open' : ''}`}
                  onClick={() => toggleFaq(index)}
                >
                  <button type="button" className="rail-faq-btn">
                    <span>{faq.q}</span>
                    <span className="rail-faq-toggle">{activeFaq === index ? '−' : '+'}</span>
                  </button>
                  {activeFaq === index && (
                    <div className="rail-faq-content">
                      <p>{faq.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Direct Support Desk Contact */}
          <div className="support-rail-card contact-box">
            <h3 className="rail-card-title">Direct Enterprise Contact</h3>
            <p className="rail-card-desc">
              Customer support desk operating Monday through Friday, 8am &ndash; 8pm EST.
            </p>
            <div className="rail-contact-lines">
              <div className="rail-contact-row">
                <IconMail size={15} />
                <span>support@nextstore.luxury</span>
              </div>
              <div className="rail-contact-row">
                <IconPhone size={15} />
                <span>+1 (800) 555-0199</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default function SupportPage() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading support workspace...
        </div>
      }
    >
      <SupportContent />
    </Suspense>
  );
}
