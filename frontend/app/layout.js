import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'NextStore — AI Customer Support Demo',
  description: 'Group mini-project for Artificial Intelligence and Applications (AAI).',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <header className="navbar">
          <div className="container nav-container">
            <Link href="/" className="brand-logo">
              <span>NextStore</span>
              <span className="brand-badge">AAI Demo</span>
            </Link>
            <nav>
              <ul className="nav-links">
                <li>
                  <Link href="/" className="nav-link">Home</Link>
                </li>
                <li>
                  <Link href="/orders" className="nav-link">My Orders</Link>
                </li>
                <li>
                  <Link href="/#support" className="nav-link">Support</Link>
                </li>
              </ul>
            </nav>
          </div>
        </header>

        <main className="main-content">
          {children}
        </main>

        <footer className="footer">
          <div className="container">
            <p>
              &copy; {new Date().getFullYear()} NextStore — Agentic Customer Support System (AAI Mini-Project).
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
