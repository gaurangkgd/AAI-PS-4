import Link from 'next/link';
import './globals.css';
import { IconLock, IconTruck } from '../components/Icons';
import HeaderActions from '../components/HeaderActions';

export const metadata = {
  title: 'NextStore — Curated Electronics, Apparel & 24/7 AI Concierge',
  description: 'Premium curated electronics, mechanical tools, and sustainable apparel backed by instant 24/7 intelligent customer care.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <header className="navbar">
          <div className="container nav-container">
            <Link href="/" className="brand-logo">
              <span>NextStore</span>
              <span className="brand-badge">Est. 2026</span>
            </Link>

            <nav aria-label="Main Navigation">
              <ul className="nav-links">
                <li>
                  <Link href="/" className="nav-link">Home</Link>
                </li>
                <li>
                  <Link href="/products" className="nav-link">Products</Link>
                </li>
                <li>
                  <Link href="/orders" className="nav-link">My Orders</Link>
                </li>
                <li>
                  <Link href="/support" className="nav-link nav-support-link">
                    <span className="nav-live-dot" aria-hidden="true" />
                    <span>AI Support</span>
                  </Link>
                </li>
                <HeaderActions />
                <li>
                  <Link href="/admin" className="nav-link nav-admin-link">
                    Supervisor Desk
                  </Link>
                </li>
              </ul>
            </nav>
          </div>
        </header>

        <main className="main-content">
          {children}
        </main>

        <footer className="footer">
          <div className="container footer-content-wrapper">
            <div className="footer-brand-column">
              <div className="footer-brand-title">NextStore</div>
              <p className="footer-brand-desc">
                Crafted for focus, movement, and everyday living. Thoughtfully engineered acoustic gear, tactile tools, and sustainable lifestyle essentials.
              </p>
              <div className="footer-badges">
                <span className="footer-badge">
                  <IconLock size={13} />
                  <span>256-Bit SSL Checkout</span>
                </span>
                <span className="footer-badge">
                  <IconTruck size={13} />
                  <span>Carbon-Neutral Shipping</span>
                </span>
              </div>
            </div>

            <div className="footer-links-grid">
              <div className="footer-col">
                <h4 className="footer-col-title">Shop Collection</h4>
                <ul className="footer-links-list">
                  <li><Link href="/products">All Products</Link></li>
                  <li><Link href="/products?category=Electronics">Precision Electronics</Link></li>
                  <li><Link href="/products?category=Apparel">Organic Apparel</Link></li>
                  <li><Link href="/products?category=Home+%26+Kitchen">Home &amp; Kitchen</Link></li>
                </ul>
              </div>

              <div className="footer-col">
                <h4 className="footer-col-title">Customer Care</h4>
                <ul className="footer-links-list">
                  <li><Link href="/support">AI Concierge &amp; Live Chat</Link></li>
                  <li><Link href="/orders">Track Active Order</Link></li>
                  <li><Link href="/support">Return &amp; Refund Policy</Link></li>
                  <li><Link href="/support">Warranty Claims</Link></li>
                </ul>
              </div>

              <div className="footer-col">
                <h4 className="footer-col-title">Administration</h4>
                <ul className="footer-links-list">
                  <li><Link href="/admin">Supervisor Dashboard</Link></li>
                  <li><Link href="/admin">Ticket Resolution</Link></li>
                  <li><Link href="/admin">System Analytics</Link></li>
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-bottom-bar">
            <div className="container footer-bottom-inner">
              <p>&copy; {new Date().getFullYear()} NextStore Inc. All rights reserved. Authentic products &amp; autonomous customer support.</p>
              <div className="footer-bottom-links">
                <span>Privacy Policy</span>
                <span>&bull;</span>
                <span>Terms of Service</span>
                <span>&bull;</span>
                <span>Security</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
