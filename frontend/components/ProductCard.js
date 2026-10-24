'use client';

import { useState } from 'react';
import { getProductImageData } from '../lib/unsplash';

/**
 * Modern, high-conversion Product Card component.
 * Features crisp Unsplash product photography, rating badges, stock status,
 * and quick-view modal triggers.
 */
export default function ProductCard({ product, onSelect }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const imgData = getProductImageData(product);
  const isOutOfStock = product.stock === 0;

  return (
    <article
      className="product-card"
      role="button"
      tabIndex={0}
      onClick={() => onSelect?.(product.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect?.(product.id);
        }
      }}
      aria-label={`View specifications and details for ${product.name}`}
    >
      {/* Product Image Frame */}
      <div className="product-card-image-wrap">
        {imgData.badge && (
          <span
            className={`product-badge-pill ${
              isOutOfStock ? 'badge-out-of-stock' : 'badge-highlight'
            }`}
          >
            {imgData.badge}
          </span>
        )}

        {/* Skeleton image placeholder */}
        {!imageLoaded && !imageError && (
          <div className="product-image-skeleton" aria-hidden="true" />
        )}

        <img
          src={imageError ? imgData.thumbnail : imgData.url}
          alt={imgData.alt}
          loading="lazy"
          className={`product-card-img ${imageLoaded ? 'loaded' : 'loading'}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => {
            setImageError(true);
            setImageLoaded(true);
          }}
        />

        <div className="product-image-overlay">
          <span className="quick-view-badge">Quick View</span>
        </div>
      </div>

      {/* Meta Bar: Category & Star Rating */}
      <div className="product-meta">
        <span className="product-tag">{product.category}</span>
        <div className="product-rating-row" title={`${imgData.rating} out of 5 stars`}>
          <span className="star-icon">★</span>
          <span className="rating-value">{imgData.rating}</span>
          <span className="rating-count">({imgData.reviewsCount})</span>
        </div>
      </div>

      {/* Title */}
      <h3 className="product-title">{product.name}</h3>

      {/* Key Specs Pills */}
      {imgData.specs && imgData.specs.length > 0 && (
        <div className="product-specs-list">
          {imgData.specs.slice(0, 2).map((spec, idx) => (
            <span key={idx} className="product-spec-tag">
              ✓ {spec}
            </span>
          ))}
        </div>
      )}

      {/* Footer: Price & Stock Status */}
      <div className="product-card-footer">
        <div className="product-price-block">
          <span className="product-price">
            ${typeof product.price === 'number' ? product.price.toFixed(2) : product.price}
          </span>
          <span className="shipping-hint">Free Delivery</span>
        </div>

        <span className={`stock-badge ${isOutOfStock ? 'out-of-stock' : 'in-stock'}`}>
          ● {isOutOfStock ? 'Sold Out' : `${product.stock} in stock`}
        </span>
      </div>
    </article>
  );
}
