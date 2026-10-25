'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';

const STORAGE_KEY = 'ns_cart_v1';
const CHANGE_EVENT = 'ns:cart-changed';
const MAX_PER_LINE = 10;

function readCart() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeCart(items) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    /* storage unavailable: cart lives only for this render */
  }
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: items }));
}

/**
 * Browser-side shopping cart (demo). Lines hold what the UI needs to render;
 * the backend re-validates price and stock at checkout.
 */
export function useCart() {
  const [items, setItems] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setItems(readCart());
    setLoaded(true);
    const onChange = (e) => setItems(e.detail || []);
    window.addEventListener(CHANGE_EVENT, onChange);
    return () => window.removeEventListener(CHANGE_EVENT, onChange);
  }, []);

  const addItem = useCallback((product, quantity = 1) => {
    if (!product || product.stock <= 0) {
      return { ok: false, message: 'This item is out of stock.' };
    }
    const current = readCart();
    const existing = current.find((line) => line.id === product.id);
    const limit = Math.min(product.stock, MAX_PER_LINE);
    const nextQty = (existing ? existing.quantity : 0) + quantity;

    if (nextQty > limit) {
      return { ok: false, message: `You can buy at most ${limit} of this item.` };
    }

    const next = existing
      ? current.map((line) => (line.id === product.id ? { ...line, quantity: nextQty, stock: product.stock } : line))
      : [
          ...current,
          {
            id: product.id,
            name: product.name,
            category: product.category,
            price: product.price,
            stock: product.stock,
            quantity,
          },
        ];
    writeCart(next);
    return { ok: true, message: `${product.name} added to your cart.` };
  }, []);

  const setQuantity = useCallback((productId, quantity) => {
    const current = readCart();
    const next = current
      .map((line) => {
        if (line.id !== productId) return line;
        const limit = Math.min(line.stock, MAX_PER_LINE);
        return { ...line, quantity: Math.max(1, Math.min(quantity, limit)) };
      })
      .filter((line) => line.quantity > 0);
    writeCart(next);
  }, []);

  const removeItem = useCallback((productId) => {
    writeCart(readCart().filter((line) => line.id !== productId));
  }, []);

  const clearCart = useCallback(() => writeCart([]), []);

  const count = useMemo(() => items.reduce((sum, line) => sum + line.quantity, 0), [items]);
  const subtotal = useMemo(
    () => Math.round(items.reduce((sum, line) => sum + line.price * line.quantity, 0) * 100) / 100,
    [items]
  );

  return { items, loaded, count, subtotal, addItem, setQuantity, removeItem, clearCart };
}
