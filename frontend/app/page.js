'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { apiFetch } from '../lib/api';
import ProductCard from '../components/ProductCard';
import ProductDetailModal from '../components/ProductDetailModal';
import { CATEGORY_HEROES } from '../lib/unsplash';
import {
  IconTruck,
  IconReturn,
  IconShield,
  IconChat,
  IconAlertTriangle,
  IconCheck,
} from '../components/Icons';

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected product modal state
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // Newsletter email state
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  // Initial products fetch
  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch('/products');
      setProducts(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Unable to connect to the backend product service.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Open product detail modal
  const handleOpenDetail = useCallback(async (productId) => {
    setSelectedProductId(productId);
    setSelectedProduct(null);
    setDetailError(null);
    setDetailLoading(true);

    try {
      const data = await apiFetch(`/products/${productId}`);
      setSelectedProduct(data);
    } catch (err) {
      setDetailError(err.message || `Failed to retrieve product details for ${productId}.`);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedProductId(null);
    setSelectedProduct(null);
    setDetailError(null);
    setDetailLoading(false);
  }, []);

  const handleNewsletterSubmit = (e) => {
    e.preventDefault();
    if (newsletterEmail.trim()) {
      setSubscribed(true);
      setNewsletterEmail('');
    }
  };

  return (
    <div className="homepage-wrapper">
      {/* Editorial Hero Section */}
      <section className="store-hero-section">
        <div className="container hero-container">
          <div className="hero-content-column">
            <div className="hero-season-tag">
              <span>Autumn / Winter 2026 Collection</span>
            </div>

            <h1 className="store-hero-heading">
              Thoughtfully Designed Essentials for Modern Living.
            </h1>

            <p className="store-hero-subheading">
              Explore precision acoustics, tactile mechanical workspace tools, and sustainable
              apparel — engineered for peak performance and backed by instant 24/7 intelligent customer care.
            </p>

            <div className="hero-cta-group">
              <a href="#featured-products" className="btn-hero-primary">
                Explore Featured Gear
              </a>
              <Link href="/support" className="btn-hero-secondary">
                <IconChat size={16} />
                <span>Consult AI Concierge</span>
              </Link>
            </div>

            {/* Micro Social Proof */}
            <div className="hero-proof-row">
              <div className="proof-avatars">
                <span className="proof-avatar" style={{ background: '#7A6855' }}>JD</span>
                <span className="proof-avatar" style={{ background: '#5B4029' }}>AL</span>
                <span className="proof-avatar" style={{ background: '#8A5832' }}>MK</span>
                <span className="proof-avatar" style={{ background: '#3D2F24' }}>+4k</span>
              </div>
              <div className="proof-text">
                <div className="proof-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
                <span>Over <strong>45,000+</strong> satisfied customers worldwide</span>
              </div>
            </div>
          </div>

          <div className="hero-image-column">
            <div className="hero-featured-card">
              <img
                src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&auto=format&fit=crop&q=85"
                alt="NextStore Signature Wireless Acoustic Headphones"
                className="hero-card-img"
              />
              <div className="hero-image-overlay">
                <div className="hero-overlay-tag">Signature Series</div>
                <h3 className="hero-overlay-title">Acoustic Over-Ear Headphones</h3>
                <p className="hero-overlay-price">From $129.99 &bull; Hybrid Active Noise Cancellation</p>
                <button
                  type="button"
                  className="hero-overlay-btn"
                  onClick={() => handleOpenDetail('PROD001')}
                >
                  Inspect Specifications &rarr;
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Brand Value Propositions Bar */}
      <section className="perks-bar-section">
        <div className="container perks-grid">
          <div className="perk-item">
            <div className="perk-svg-wrap">
              <IconTruck size={20} />
            </div>
            <div>
              <h4 className="perk-title">Free Express Shipping</h4>
              <p className="perk-desc">Complimentary carbon-neutral dispatch on all orders over $50.</p>
            </div>
          </div>

          <div className="perk-item">
            <div className="perk-svg-wrap">
              <IconReturn size={20} />
            </div>
            <div>
              <h4 className="perk-title">30-Day Risk-Free Trial</h4>
              <p className="perk-desc">Love your gear or return it with automated instant shipping labels.</p>
            </div>
          </div>

          <div className="perk-item">
            <div className="perk-svg-wrap">
              <IconShield size={20} />
            </div>
            <div>
              <h4 className="perk-title">2-Year Official Warranty</h4>
              <p className="perk-desc">Engineered for durability with complete coverage on all electronics.</p>
            </div>
          </div>

          <div className="perk-item">
            <div className="perk-svg-wrap">
              <IconChat size={20} />
            </div>
            <div>
              <h4 className="perk-title">24/7 AI Support Concierge</h4>
              <p className="perk-desc">Real-time order tracking, cancellation processing, and guidance.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Curated Category Grid */}
      <section className="categories-section">
        <div className="container">
          <div className="section-intro">
            <span className="section-eyebrow">Curated Collections</span>
            <h2 className="section-heading">Built for Everyday Excellence</h2>
            <p className="section-subtext">
              Every piece in our catalog is handpicked for tactile beauty, functional utility, and longevity.
            </p>
          </div>

          <div className="categories-grid">
            {Object.entries(CATEGORY_HEROES).map(([categoryName, data]) => (
              <Link
                key={categoryName}
                href="/products"
                className="category-card"
              >
                <div className="category-img-wrap">
                  <img
                    src={data.image}
                    alt={data.title}
                    className="category-card-img"
                    loading="lazy"
                  />
                  <div className="category-img-overlay" />
                </div>
                <div className="category-card-content">
                  <span className="category-item-count">{data.count}</span>
                  <h3 className="category-card-title">{data.title}</h3>
                  <p className="category-card-tagline">{data.tagline}</p>
                  <span className="category-cta-link">Shop Collection &rarr;</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products Showcase Section */}
      <section id="featured-products" className="featured-section">
        <div className="container">
          <div className="featured-header-row">
            <div>
              <span className="section-eyebrow">Spotlight Catalog</span>
              <h2 className="section-heading">Featured Products</h2>
              <p className="section-subtext">
                Browse our highest-rated gadgets, apparel, and workspace essentials.
              </p>
            </div>

            <Link href="/products" className="btn-view-all-products">
              View All Products ({products.length}) &rarr;
            </Link>
          </div>

          {/* Loading Skeletons */}
          {loading && (
            <div className="product-grid" aria-label="Loading featured products">
              {[1, 2, 3, 4].map((n) => (
                <div key={`skeleton-${n}`} className="skeleton-card">
                  <div className="skeleton-box image" style={{ height: '220px' }} />
                  <div className="product-meta">
                    <div className="skeleton-box tag" />
                    <div className="skeleton-box price" />
                  </div>
                  <div className="skeleton-box title" />
                  <div className="skeleton-box desc" />
                  <div className="skeleton-box footer" />
                </div>
              ))}
            </div>
          )}

          {/* Error Message with Retry */}
          {!loading && error && (
            <div className="state-container" role="alert">
              <div className="state-icon">
                <IconAlertTriangle size={32} />
              </div>
              <h3 className="state-title">Unable to Load Catalog</h3>
              <p className="state-message">
                Could not connect to the inventory service ({error}). Please ensure the backend is running.
              </p>
              <button type="button" className="state-btn" onClick={loadProducts}>
                Try Again
              </button>
            </div>
          )}

          {/* Dynamic Product Grid with Unsplash Images */}
          {!loading && !error && products.length > 0 && (
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onSelect={handleOpenDetail}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Dedicated AI Customer Support Feature Banner */}
      <section className="support-banner-section">
        <div className="container">
          <div className="support-banner-card">
            <div className="support-banner-info">
              <div className="support-status-indicator">
                <span className="live-dot" />
                <span>NextStore AI Concierge &bull; Online 24/7</span>
              </div>
              <h2 className="support-banner-title">
                Autonomous Customer Care with Zero Waiting Time.
              </h2>
              <p className="support-banner-text">
                Need to track an incoming package, modify an active order, or request a seamless return?
                Our autonomous concierge resolves requests in seconds &mdash; or immediately routes your file
                to our senior supervisor desk.
              </p>

              <div className="support-banner-actions">
                <Link href="/support" className="btn-banner-chat">
                  Open AI Customer Support &rarr;
                </Link>
                <Link href="/orders" className="btn-banner-orders">
                  Track My Orders
                </Link>
              </div>
            </div>

            <div className="support-banner-preview">
              <div className="chat-preview-card">
                <div className="preview-bubble user">
                  Where is my order ORD1001?
                </div>
                <div className="preview-bubble assistant">
                  <div className="preview-agent-tag">NextStore Concierge</div>
                  Order <strong>ORD1001</strong> was successfully delivered on October 10. Contains:
                  Wireless Noise-Canceling Headphones ($129.99). Would you like help with warranty registration?
                </div>
                <div className="preview-action-row">
                  <span className="preview-chip">Cancel Order</span>
                  <span className="preview-chip">Return Policy</span>
                  <span className="preview-chip">Supervisor Help</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Customer Reviews / Testimonials */}
      <section className="testimonials-section">
        <div className="container">
          <div className="section-intro">
            <span className="section-eyebrow">Customer Voices</span>
            <h2 className="section-heading">Loved by Thoughtful Creators</h2>
            <p className="section-subtext">Real experiences from customers who prioritize design, quality, and fast support.</p>
          </div>

          <div className="testimonials-grid">
            <div className="testimonial-card">
              <div className="testimonial-rating">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
              <p className="testimonial-text">
                "The Wireless Noise-Canceling Headphones are stunning. The sound profile is balanced and rich, and when I needed to update my delivery address, the AI Concierge resolved it in 10 seconds flat."
              </p>
              <div className="testimonial-author">
                <strong>Elena Rostova</strong>
                <span>Verified Buyer &bull; Sound Designer, Seattle</span>
              </div>
            </div>

            <div className="testimonial-card">
              <div className="testimonial-rating">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
              <p className="testimonial-text">
                "The Ergonomic Mechanical Keyboard completely transformed my workday. Solid aluminum body, incredible tactile feedback. Best packaging and customer care experience I've had in years."
              </p>
              <div className="testimonial-author">
                <strong>Marcus Thorne</strong>
                <span>Verified Buyer &bull; Software Architect, Austin</span>
              </div>
            </div>

            <div className="testimonial-card">
              <div className="testimonial-rating">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
              <p className="testimonial-text">
                "The organic cotton hoodie is heavyweight and impeccably stitched. No branding overload, just pure quality. Will definitely be ordering the rest of the apparel line."
              </p>
              <div className="testimonial-author">
                <strong>Sarah Lin</strong>
                <span>Verified Buyer &bull; Creative Director, Brooklyn</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Newsletter / VIP Club */}
      <section className="newsletter-section">
        <div className="container">
          <div className="newsletter-box">
            <div className="newsletter-text">
              <span className="newsletter-eyebrow">Stay in the Loop</span>
              <h2 className="newsletter-title">Receive Private Release Access &amp; 15% Off</h2>
              <p className="newsletter-subtitle">
                Join our private newsletter for early product drops, curated design essays, and subscriber perks.
              </p>
            </div>

            <form className="newsletter-form" onSubmit={handleNewsletterSubmit}>
              {subscribed ? (
                <div className="newsletter-success">
                  <IconCheck size={16} />
                  <span>Thank you for subscribing. Your 15% voucher has been dispatched to your inbox.</span>
                </div>
              ) : (
                <div className="newsletter-input-group">
                  <input
                    type="email"
                    required
                    placeholder="Enter your email address..."
                    value={newsletterEmail}
                    onChange={(e) => setNewsletterEmail(e.target.value)}
                    className="newsletter-input"
                    aria-label="Email address for newsletter"
                  />
                  <button type="submit" className="newsletter-btn">
                    Subscribe
                  </button>
                </div>
              )}
            </form>
          </div>
        </div>
      </section>

      {/* Product Detail Modal */}
      <ProductDetailModal
        productId={selectedProductId}
        product={selectedProduct}
        loading={detailLoading}
        error={detailError}
        onClose={handleCloseDetail}
        onRetry={handleOpenDetail}
      />
    </div>
  );
}
