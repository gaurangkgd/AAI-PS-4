'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getProductImageData } from '../lib/unsplash';
import {
  IconShield,
  IconReturn,
  IconChat,
  IconAlertTriangle,
  IconCheck,
} from './Icons';

export default function ProductDetailModal({
  productId,
  product,
  loading,
  error,
  onClose,
  onRetry,
}) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [addedNotice, setAddedNotice] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose?.();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!productId) return null;

  const imgData = product ? getProductImageData(product) : null;
  const isOutOfStock = product?.stock === 0;

  const handleAddToCart = () => {
    setAddedNotice(true);
    setTimeout(() => setAddedNotice(false), 2400);
  };

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-dialog modal-dialog-lg" onClick={(e) => e.stopPropagation()}>
        {/* Modal Top Header */}
        <div className="modal-header">
          <div className="modal-header-info">
            <span className="modal-category-tag">
              {product?.category || 'Curated Product'}
            </span>
            <span className="modal-product-id">SKU: {productId}</span>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close product details"
          >
            Close
          </button>
        </div>

        {/* Modal Content */}
        <div className="modal-body">
          {/* Loading State */}
          {loading && (
            <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
              <div className="state-icon">
                <span className="state-spinner" />
              </div>
              <h3 className="state-title">Loading Product Details</h3>
              <p className="state-message">Fetching real-time inventory and specifications...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
              <div className="state-icon">
                <IconAlertTriangle size={32} />
              </div>
              <h3 className="state-title">Failed to Load Details</h3>
              <p className="state-message">{error}</p>
              <button
                type="button"
                className="state-btn"
                onClick={() => onRetry?.(productId)}
              >
                Retry
              </button>
            </div>
          )}

          {/* Loaded Product Content */}
          {product && !loading && imgData && (
            <div className="modal-product-layout">
              {/* Product Gallery View with Unsplash Image */}
              <div className="modal-gallery">
                <div className="modal-main-image-wrap">
                  {!imageLoaded && (
                    <div className="product-image-skeleton modal-skeleton" aria-hidden="true" />
                  )}
                  <img
                    src={imgData.url}
                    alt={imgData.alt}
                    className={`modal-main-image ${imageLoaded ? 'loaded' : 'loading'}`}
                    onLoad={() => setImageLoaded(true)}
                  />
                  {imgData.badge && (
                    <span className="modal-image-badge">{imgData.badge}</span>
                  )}
                </div>

                <div className="modal-guarantee-box">
                  <div className="guarantee-item">
                    <div className="guarantee-icon-wrap">
                      <IconShield size={16} />
                    </div>
                    <div>
                      <strong>2-Year Official Warranty</strong>
                      <p>Full hardware protection included.</p>
                    </div>
                  </div>
                  <div className="guarantee-item">
                    <div className="guarantee-icon-wrap">
                      <IconReturn size={16} />
                    </div>
                    <div>
                      <strong>30-Day Risk-Free Returns</strong>
                      <p>Instant pre-paid shipping label.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Product Info & Specifications */}
              <div className="modal-details-column">
                <div className="modal-rating-header">
                  <div className="product-rating-row">
                    <span className="star-icon">&#9733;</span>
                    <span className="rating-value">{imgData.rating}</span>
                    <span className="rating-count">({imgData.reviewsCount} customer reviews)</span>
                  </div>
                  <span className="verified-buyer-pill">Verified Authentic</span>
                </div>

                <h3 id="modal-title" className="modal-product-title">
                  {product.name}
                </h3>

                <div className="modal-price-row">
                  <span className="modal-hero-price">
                    ${typeof product.price === 'number' ? product.price.toFixed(2) : product.price}
                  </span>
                  <span className="modal-tax-tag">Taxes calculated at checkout</span>
                </div>

                <p className="modal-description">
                  {product.description ||
                    'Engineered to exacting standards for precision, durability, and daily comfort. Every unit undergoes rigorous quality testing before dispatch.'}
                </p>

                {/* Technical Specifications */}
                <div className="modal-specs-block">
                  <h4 className="modal-specs-title">Product Highlights</h4>
                  <ul className="modal-specs-checklist">
                    {imgData.specs.map((spec, idx) => (
                      <li key={idx}>
                        <span className="spec-check-icon">
                          <IconCheck size={13} />
                        </span>
                        <span>{spec}</span>
                      </li>
                    ))}
                    <li>
                      <span className="spec-check-icon">
                        <IconCheck size={13} />
                      </span>
                      <span>Complimentary carbon-neutral express packaging</span>
                    </li>
                  </ul>
                </div>

                {/* Stock Indicator */}
                <div className="modal-stock-status">
                  <span
                    className={`stock-badge ${isOutOfStock ? 'out-of-stock' : 'in-stock'}`}
                    style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem' }}
                  >
                    &bull; {isOutOfStock ? 'Currently Out of Stock' : `In Stock &mdash; ${product.stock} units ready to ship`}
                  </span>
                </div>

                {/* Add to Bag and AI Support Actions */}
                <div className="modal-actions-group">
                  <button
                    type="button"
                    className="modal-btn-buy"
                    disabled={isOutOfStock}
                    onClick={handleAddToCart}
                  >
                    {isOutOfStock ? 'Join Waitlist' : addedNotice ? 'Added to Cart' : 'Add to Bag'}
                  </button>

                  <Link
                    href={`/support?query=${encodeURIComponent(
                      `Do you have more details or promotions for ${product.name} (${product.id})?`
                    )}`}
                    className="modal-btn-ask-ai"
                    onClick={onClose}
                  >
                    <IconChat size={15} />
                    <span>Ask AI Concierge</span>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button type="button" className="modal-btn-dismiss" onClick={onClose}>
            Back to Catalog
          </button>
        </div>
      </div>
    </div>
  );
}
