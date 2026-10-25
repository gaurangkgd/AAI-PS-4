'use client';

import Link from 'next/link';
import { useCart } from '../../lib/cart';
import { getProductImageData } from '../../lib/unsplash';

export default function CartPage() {
  const { items, loaded, count, subtotal, setQuantity, removeItem, clearCart } = useCart();

  if (!loaded) {
    return (
      <div className="container cart-page">
        <p className="section-desc">Loading your cart...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="container cart-page">
        <h1 className="section-title" style={{ fontSize: '2rem' }}>Your Cart</h1>
        <div className="state-container">
          <h2 className="state-title">Your cart is empty</h2>
          <p className="state-message">Add something from the catalog and it will show up here.</p>
          <Link href="/products" className="state-btn">Browse Products</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container cart-page">
      <div className="cart-header-row">
        <div>
          <h1 className="section-title" style={{ fontSize: '2rem' }}>Your Cart</h1>
          <p className="section-desc">{count} {count === 1 ? 'item' : 'items'} ready for checkout.</p>
        </div>
        <button type="button" className="cart-clear-btn" onClick={clearCart}>Clear cart</button>
      </div>

      <div className="cart-layout">
        <div className="cart-lines">
          {items.map((line) => {
            const img = getProductImageData({ id: line.id, name: line.name, category: line.category });
            const maxQty = Math.min(line.stock, 10);
            return (
              <div key={line.id} className="cart-line">
                <img src={img.thumbnail} alt={line.name} className="cart-line-img" />
                <div className="cart-line-info">
                  <div className="cart-line-name">{line.name}</div>
                  <div className="cart-line-meta">{line.category} &bull; ${line.price.toFixed(2)} each</div>
                  <div className="cart-qty-row">
                    <button
                      type="button"
                      className="cart-qty-btn"
                      onClick={() => setQuantity(line.id, line.quantity - 1)}
                      disabled={line.quantity <= 1}
                      aria-label={`Decrease quantity of ${line.name}`}
                    >
                      &minus;
                    </button>
                    <span className="cart-qty-value">{line.quantity}</span>
                    <button
                      type="button"
                      className="cart-qty-btn"
                      onClick={() => setQuantity(line.id, line.quantity + 1)}
                      disabled={line.quantity >= maxQty}
                      aria-label={`Increase quantity of ${line.name}`}
                    >
                      +
                    </button>
                    <button type="button" className="cart-remove-btn" onClick={() => removeItem(line.id)}>
                      Remove
                    </button>
                  </div>
                </div>
                <div className="cart-line-total">${(line.price * line.quantity).toFixed(2)}</div>
              </div>
            );
          })}
        </div>

        <aside className="cart-summary">
          <h2 className="cart-summary-title">Order Summary</h2>
          <div className="cart-summary-row">
            <span>Subtotal</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <div className="cart-summary-row">
            <span>Shipping</span>
            <span>Free</span>
          </div>
          <div className="cart-summary-row cart-summary-total">
            <span>Total</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <Link href="/checkout" className="cart-checkout-btn">Proceed to Checkout</Link>
          <Link href="/products" className="cart-continue-link">Continue shopping</Link>
        </aside>
      </div>
    </div>
  );
}
