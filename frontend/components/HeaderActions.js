'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { apiFetch } from '../lib/api';
import { useCart } from '../lib/cart';
import { useCustomer, DATA_REFRESH_EVENT } from '../lib/useCustomer';

/**
 * Cart and Inbox entries for the navbar. The inbox badge shows unread messages
 * for the active demo customer and refreshes every 10 seconds.
 */
export default function HeaderActions() {
  const { count } = useCart();
  const [customerId] = useCustomer();
  const [unread, setUnread] = useState(0);

  const loadUnread = useCallback(async () => {
    if (!customerId || customerId === 'none') {
      setUnread(0);
      return;
    }
    try {
      const data = await apiFetch(`/customers/${customerId}/notifications`);
      setUnread(data?.unread_count || 0);
    } catch {
      /* backend offline: keep last value */
    }
  }, [customerId]);

  useEffect(() => {
    loadUnread();
    const timer = setInterval(loadUnread, 10000);
    window.addEventListener(DATA_REFRESH_EVENT, loadUnread);
    return () => {
      clearInterval(timer);
      window.removeEventListener(DATA_REFRESH_EVENT, loadUnread);
    };
  }, [loadUnread]);

  return (
    <>
      <li>
        <Link href="/orders?tab=inbox" className="nav-link nav-badge-link">
          <span>Inbox</span>
          {unread > 0 && <span className="nav-badge" aria-label={`${unread} unread messages`}>{unread}</span>}
        </Link>
      </li>
      <li>
        <Link href="/cart" className="nav-link nav-badge-link">
          <span>Cart</span>
          {count > 0 && <span className="nav-badge" aria-label={`${count} items in cart`}>{count}</span>}
        </Link>
      </li>
    </>
  );
}
