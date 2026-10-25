/**
 * Demo customer personas. Orders are NOT stored here any more: the UI fetches them live
 * from the backend (GET /customers/{id}/orders) so statuses are never stale.
 * Prompts tagged "Human Review" are designed to hand the case to a human specialist.
 */
export const CUSTOMER_PROFILES = [
  {
    id: 'CUST001',
    name: 'Alice Johnson',
    email: 'alice.johnson@example.com',
    tier: 'Premium Gold',
    badge: 'Gold Tier',
    description: 'Active shopper with a processing order and a delivered item',
    starterPrompts: [
      { tag: 'Auto Track', text: 'Where is my order?' },
      { tag: 'Auto Cancel', text: 'Can you cancel my order?' },
      { tag: 'Auto Return', text: 'How do I return my delivered headphones?' },
      { tag: 'Policy', text: 'What is your refund policy?' },
      { tag: 'Human Review', text: 'I was charged twice for order ORD1001' },
      { tag: 'Human Review', text: 'My headphones from ORD1001 are overheating and smoking' },
    ],
  },
  {
    id: 'CUST002',
    name: 'Bob Smith',
    email: 'bob.smith@example.com',
    tier: 'Standard Member',
    badge: 'Standard',
    description: 'Awaiting a keyboard; also has an old delivered hoodie order',
    starterPrompts: [
      { tag: 'Auto Track', text: 'What is the tracking status of my order?' },
      { tag: 'Delivery ETA', text: 'When will my package arrive?' },
      { tag: 'Courier', text: 'Can I reschedule the courier delivery?' },
      { tag: 'Human Review', text: 'I want to return my hoodie from order ORD1006' },
      { tag: 'Human Review', text: 'Order ORD1003 never arrived and the tracking is stuck' },
    ],
  },
  {
    id: 'CUST003',
    name: 'Charlie Davis',
    email: 'charlie.davis@example.com',
    tier: 'Standard Member',
    badge: 'Standard',
    description: 'Encountered a payment deduction issue on checkout',
    starterPrompts: [
      { tag: 'Payment Dispute', text: 'My payment failed but money was deducted' },
      { tag: 'Order Status', text: 'Did my order go through?' },
      { tag: 'Human Support', text: 'I want to speak with a billing specialist' },
    ],
  },
  {
    id: 'CUST004',
    name: 'Diana Lee',
    email: 'diana.lee@example.com',
    tier: 'VIP Platinum',
    badge: 'VIP Platinum',
    description: 'Pending payment verification for running shoes',
    starterPrompts: [
      { tag: 'Payment Link', text: 'How can I complete payment for my order?' },
      { tag: 'Auto Cancel', text: 'Please cancel my pending order' },
      { tag: 'Human Review', text: 'I did not authorize this charge, it looks like fraud' },
    ],
  },
  {
    id: 'CUST999',
    name: 'Evan Wright',
    email: 'evan.wright@example.com',
    tier: 'New Member',
    badge: 'New Account',
    description: 'Fresh account with no order history. Great for the cart demo',
    starterPrompts: [
      { tag: 'Check Orders', text: 'Do I have any pending orders?' },
      { tag: 'Catalog', text: 'What products are currently in stock?' },
      { tag: 'Warranty', text: 'What warranty comes with electronics?' },
      { tag: 'Human Review', text: 'Can you gift wrap my purchase and add a handwritten note?' },
    ],
  },
  {
    id: 'none',
    name: 'Guest / Manual Entry',
    email: 'No customer context linked',
    tier: 'Guest Session',
    badge: 'Guest',
    description: 'Type specific Order IDs directly in conversation',
    starterPrompts: [
      { tag: 'Tracking', text: 'Where is my order ORD1001?' },
      { tag: 'Cancel', text: 'Please cancel order ORD1002' },
      { tag: 'Payment', text: 'Payment failed for order ORD1004' },
      { tag: 'Policy', text: 'What is your return policy?' },
    ],
  },
];

export function getCustomerProfile(id) {
  if (!id) return CUSTOMER_PROFILES[0];
  return CUSTOMER_PROFILES.find((c) => c.id.toUpperCase() === id.toUpperCase()) || CUSTOMER_PROFILES[0];
}
