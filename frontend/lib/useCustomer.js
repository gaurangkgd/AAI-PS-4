'use client';

import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'ns_customer_id';
const CHANGE_EVENT = 'ns:customer-changed';

/**
 * Shared "who am I shopping as" state so the chat, orders, inbox, cart and checkout
 * all follow the same demo customer (persisted in localStorage, synced across components).
 */
export function useCustomer(defaultId = 'CUST001') {
  const [customerId, setCustomerIdState] = useState(defaultId);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) setCustomerIdState(saved);
    } catch {
      /* storage unavailable: keep default */
    }

    const onChange = (e) => setCustomerIdState(e.detail);
    window.addEventListener(CHANGE_EVENT, onChange);
    return () => window.removeEventListener(CHANGE_EVENT, onChange);
  }, []);

  const setCustomerId = useCallback((id) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* ignore */
    }
    setCustomerIdState(id);
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: id }));
  }, []);

  return [customerId, setCustomerId];
}

/** Ask every live-data widget (orders, inbox badge) to refetch right now. */
export const DATA_REFRESH_EVENT = 'ns:data-refresh';

export function requestDataRefresh() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(DATA_REFRESH_EVENT));
  }
}
