'use client';

import { useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '../../lib/api';
import { useCart } from '../../lib/cart';
import { useCustomer, requestDataRefresh } from '../../lib/useCustomer';
import { CUSTOMER_PROFILES, getCustomerProfile } from '../../lib/customerContext';

const PAYMENT_METHODS = [
  { id: 'credit_card', label: 'Credit / Debit Card' },
  { id: 'upi', label: 'UPI' },
  { id: 'net_banking', label: 'Net Banking' },
];

export default function CheckoutPage() {
  const { items, loaded, subtotal, clearCart } = useCart();
  const [customerId, setCustomerId] = useCustomer();
  const [address, setAddress] = useState('221B Demo Street, Sample City, 560001');
  const [method, setMethod] = useState('credit_card');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const customer = getCustomerProfile(customerId);
  const isGuest = !customerId || customerId === 'none';

  const handlePay = async () => {
    setPaying(true);
    setError('');
    try {
      const data = await apiFetch('/checkout', {
        method: 'POST',
        body: JSON.stringify({
          customer_id: customerId,
          items: items.map((line) => ({ product_id: line.id, quantity: line.quantity })),
          payment_method: method,
          shipping_address: address,
          simulate_failure: simulateFailure,
        }),
      });
      if (data.success) clearCart();
      setResult(data);
      requestDataRefresh();
    } catch (err) {
      setError(err.message || 'Checkout failed. Please try again.');
    } finally {
      setPaying(false);
    }
  };

  if (result) {
    const { order, payment, success, message } = result;
    return (
      <div className="container checkout-page">
        <div className={`checkout-result ${success ? 'success' : 'failed'}`}>
          <h1 className="checkout-result-title">{success ? 'Payment successful' : 'Payment failed'}</h1>
          <p className="checkout-result-msg">{message}</p>
          <dl className="checkout-result-grid">
            <div><dt>Order</dt><dd>{order.id}</dd></div>
            <div><dt>Amount</dt><dd>${payment.amount.toFixed(2)}</dd></div>
            <div><dt>Method</dt><dd>{payment.payment_method.replace('_', ' ')}</dd></div>
            <div><dt>Transaction</dt><dd>{payment.transaction_ref}</dd></div>
            <div><dt>Order status</dt><dd>{order.status.replace('_', ' ')}</dd></div>
          </dl>
          <p className="checkout-demo-note">
            Demo only: no real payment was made.
            {!success && ' This order is now a payment-failure case you can raise with the AI Concierge.'}
          </p>
          <div className="checkout-result-actions">
            <Link href="/orders" className="cart-checkout-btn">View My Orders</Link>
            {!success && (
              <Link
                href={`/support?query=${encodeURIComponent(`My card was charged $${payment.amount.toFixed(2)} for order ${order.id} but the order failed`)}`}
                className="cart-continue-link"
              >
                Ask AI Concierge about this &rarr;
              </Link>
            )}
            <Link href="/products" className="cart-continue-link">Continue shopping</Link>
          </div>
        </div>
      </div>
    );
  }

  if (!loaded) {
    return (
      <div className="container checkout-page">
        <p className="section-desc">Loading checkout...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="container checkout-page">
        <h1 className="section-title" style={{ fontSize: '2rem' }}>Checkout</h1>
        <div className="state-container">
          <h2 className="state-title">Nothing to check out</h2>
          <p className="state-message">Your cart is empty.</p>
          <Link href="/products" className="state-btn">Browse Products</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container checkout-page">
      <h1 className="section-title" style={{ fontSize: '2rem' }}>Checkout</h1>
      <p className="section-desc">Review your order and pay with the demo gateway.</p>

      <div className="cart-layout">
        <div className="checkout-form">
          <section className="checkout-card">
            <h2 className="checkout-card-title">1. Ordering as</h2>
            <select
              className="customer-select-control checkout-select"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              aria-label="Customer account"
            >
              {CUSTOMER_PROFILES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id === 'none' ? 'Guest (cannot check out)' : `${c.name} (${c.id})`}
                </option>
              ))}
            </select>
            {isGuest ? (
              <p className="checkout-warning">Pick a customer account so the order and its updates can be linked to you.</p>
            ) : (
              <p className="checkout-hint">{customer.email}</p>
            )}
          </section>

          <section className="checkout-card">
            <h2 className="checkout-card-title">2. Delivery address</h2>
            <textarea
              className="checkout-textarea"
              rows={3}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              aria-label="Delivery address"
            />
          </section>

          <section className="checkout-card">
            <h2 className="checkout-card-title">3. Payment (demo)</h2>
            <div className="checkout-demo-banner">
              Demo mode: nothing is charged and no card details are collected.
            </div>
            <div className="checkout-methods" role="radiogroup" aria-label="Payment method">
              {PAYMENT_METHODS.map((m) => (
                <label key={m.id} className={`checkout-method ${method === m.id ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="payment-method"
                    value={m.id}
                    checked={method === m.id}
                    onChange={() => setMethod(m.id)}
                  />
                  <span>{m.label}</span>
                </label>
              ))}
            </div>
            <label className="checkout-failure-toggle">
              <input
                type="checkbox"
                checked={simulateFailure}
                onChange={(e) => setSimulateFailure(e.target.checked)}
              />
              <span>Simulate a payment failure (to demo the human-review flow)</span>
            </label>
          </section>
        </div>

        <aside className="cart-summary">
          <h2 className="cart-summary-title">Order Summary</h2>
          {items.map((line) => (
            <div key={line.id} className="cart-summary-row">
              <span>{line.quantity}x {line.name}</span>
              <span>${(line.price * line.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="cart-summary-row">
            <span>Shipping</span>
            <span>Free</span>
          </div>
          <div className="cart-summary-row cart-summary-total">
            <span>Total</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          {error && <div className="cart-inline-error" role="alert">{error}</div>}
          <button
            type="button"
            className="cart-checkout-btn"
            onClick={handlePay}
            disabled={paying || isGuest || !address.trim()}
          >
            {paying ? 'Processing payment...' : `Pay $${subtotal.toFixed(2)}`}
          </button>
          <Link href="/cart" className="cart-continue-link">Back to cart</Link>
        </aside>
      </div>
    </div>
  );
}
