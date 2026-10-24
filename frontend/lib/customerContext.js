export const CUSTOMER_PROFILES = [
  {
    id: 'CUST001',
    name: 'Alice Johnson',
    email: 'alice.johnson@example.com',
    tier: 'Premium Gold',
    badge: 'Gold Tier',
    description: 'Active shopper with 1 processing order & 1 delivered item',
    orders: [
      { id: 'ORD1002', status: 'processing', total: 49.90, item: 'Stainless Steel Thermal Water Bottle (x2)' },
      { id: 'ORD1001', status: 'delivered', total: 129.99, item: 'Wireless Noise-Canceling Headphones' },
    ],
    starterPrompts: [
      { tag: 'Auto Track', text: 'Where is my order?' },
      { tag: 'Auto Cancel', text: 'Can you cancel my order?' },
      { tag: 'Auto Return', text: 'How do I return my delivered headphones?' },
      { tag: 'Policy', text: 'What is your refund policy?' },
    ],
  },
  {
    id: 'CUST002',
    name: 'Bob Smith',
    email: 'bob.smith@example.com',
    tier: 'Standard Member',
    badge: 'Standard',
    description: 'Awaiting delivery for mechanical keyboard',
    orders: [
      { id: 'ORD1003', status: 'shipped', total: 89.50, item: 'Ergonomic Mechanical Keyboard' },
    ],
    starterPrompts: [
      { tag: 'Auto Track', text: 'What is the tracking status of my order?' },
      { tag: 'Delivery ETA', text: 'When will my package arrive?' },
      { tag: 'Courier', text: 'Can I reschedule the courier delivery?' },
    ],
  },
  {
    id: 'CUST003',
    name: 'Charlie Davis',
    email: 'charlie.davis@example.com',
    tier: 'Standard Member',
    badge: 'Standard',
    description: 'Encountered payment deduction issue on checkout',
    orders: [
      { id: 'ORD1004', status: 'payment_failed', total: 39.99, item: 'USB-C Multi-Port Hub' },
    ],
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
    orders: [
      { id: 'ORD1005', status: 'pending_payment', total: 74.99, item: 'Ultra-Light Running Shoes' },
    ],
    starterPrompts: [
      { tag: 'Payment Link', text: 'How can I complete payment for my order?' },
      { tag: 'Auto Cancel', text: 'Please cancel my pending order' },
    ],
  },
  {
    id: 'CUST999',
    name: 'Evan Wright',
    email: 'evan.wright@example.com',
    tier: 'New Member',
    badge: 'New Account',
    description: 'Fresh account with no order history',
    orders: [],
    starterPrompts: [
      { tag: 'Check Orders', text: 'Do I have any pending orders?' },
      { tag: 'Catalog', text: 'What products are currently in stock?' },
      { tag: 'Warranty', text: 'What warranty comes with electronics?' },
    ],
  },
  {
    id: 'none',
    name: 'Guest / Manual Entry',
    email: 'No customer context linked',
    tier: 'Guest Session',
    badge: 'Guest',
    description: 'Type specific Order IDs directly in conversation',
    orders: [],
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
