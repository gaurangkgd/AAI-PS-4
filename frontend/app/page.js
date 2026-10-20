'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../lib/api';
import ChatPanel from '../components/ChatPanel';

/**
 * Returns a contextual icon for category displays.
 */
function getCategoryIcon(category = '') {
  const cat = category.toLowerCase();
  if (cat.includes('elect')) return '⚡';
  if (cat.includes('apparel') || cat.includes('cloth')) return '👕';
  if (cat.includes('kitchen') || cat.includes('home')) return '🏠';
  return '📦';
}

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected product detail modal state
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // Initial products fetch with component mount safety
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
    let isMounted = true;

    async function initialFetch() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch('/products');
        if (isMounted) {
          setProducts(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Unable to connect to the backend product service.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    initialFetch();

    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch individual product details from GET /products/{product_id}
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

  // Close modal when pressing Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && selectedProductId) {
        handleCloseDetail();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedProductId, handleCloseDetail]);

  return (
    <div className="container" id="home">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-pill">
          <span>✨</span>
          <span>Agentic AI Support Enabled</span>
        </div>
        <h1 className="hero-title">
          Modern Electronics &amp; Apparel with{' '}
          <span className="hero-highlight">Intelligent Support</span>
        </h1>
        <p className="hero-subtitle">
          Explore curated products with automated order tracking, instant policy resolution,
          and seamless support escalation powered by LangGraph.
        </p>
      </section>

      {/* Main Content Grid */}
      <div className="content-grid">
        {/* Products Section */}
        <section id="products">
          <div className="section-header">
            <h2 className="section-title">Featured Products</h2>
            <p className="section-desc">
              Browse our catalog of premium gadgets and lifestyle essentials.
            </p>
          </div>

          {/* Loading State: Skeletons */}
          {loading && (
            <div className="product-grid" aria-label="Loading products">
              {[1, 2, 3, 4].map((n) => (
                <div key={`skeleton-${n}`} className="skeleton-card">
                  <div className="skeleton-box image" />
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

          {/* Error State with Retry */}
          {!loading && error && (
            <div className="state-container" role="alert">
              <div className="state-icon">⚠️</div>
              <h3 className="state-title">Unable to Load Products</h3>
              <p className="state-message">
                Could not connect to the product service ({error}). Please ensure the FastAPI backend is running on{' '}
                <code>http://127.0.0.1:8000</code>.
              </p>
              <button
                type="button"
                className="state-btn"
                onClick={loadProducts}
              >
                Try Again
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && products.length === 0 && (
            <div className="state-container">
              <div className="state-icon">📦</div>
              <h3 className="state-title">No Products Found</h3>
              <p className="state-message">
                There are currently no products available in the catalog. Please check back later.
              </p>
              <button
                type="button"
                className="state-btn"
                onClick={loadProducts}
              >
                Refresh
              </button>
            </div>
          )}

          {/* Dynamic Product Grid */}
          {!loading && !error && products.length > 0 && (
            <div className="product-grid">
              {products.map((product) => {
                const isOutOfStock = product.stock === 0;
                return (
                  <div
                    key={product.id}
                    className="product-card"
                    role="button"
                    tabIndex={0}
                    onClick={() => handleOpenDetail(product.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleOpenDetail(product.id);
                      }
                    }}
                    aria-label={`View details for ${product.name}`}
                  >
                    <div className="product-card-image">
                      <span className="product-image-icon">
                        {getCategoryIcon(product.category)}
                      </span>
                      <span>{product.category}</span>
                    </div>

                    <div className="product-meta">
                      <span className="product-tag">{product.category}</span>
                      <span className="product-price">
                        ${typeof product.price === 'number' ? product.price.toFixed(2) : product.price}
                      </span>
                    </div>

                    <h3 className="product-title">{product.name}</h3>

                    {product.description && (
                      <p className="product-desc">{product.description}</p>
                    )}

                    <div className="product-card-footer">
                      <span
                        className={`stock-badge ${isOutOfStock ? 'out-of-stock' : 'in-stock'}`}
                      >
                        ● {isOutOfStock ? 'Out of stock' : `In Stock (${product.stock})`}
                      </span>
                      <span className="view-detail-hint">Details →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Customer Support Section */}
        <section id="support">
          <div className="section-header">
            <h2 className="section-title">AI Customer Support</h2>
            <p className="section-desc">
              Instant assistance for order tracking, cancellations, and policy queries.
            </p>
          </div>

          <ChatPanel />
        </section>
      </div>

      {/* Product Detail Modal */}
      {selectedProductId && (
        <div
          className="modal-overlay"
          onClick={handleCloseDetail}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div
            className="modal-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="modal-header-info">
                <span className="modal-category-tag">
                  {selectedProduct?.category || 'Product'}
                </span>
                <span className="modal-product-id">ID: {selectedProductId}</span>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={handleCloseDetail}
                aria-label="Close product details"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              {detailLoading && (
                <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
                  <div className="state-icon">⏳</div>
                  <h3 className="state-title">Loading Product Details</h3>
                  <p className="state-message">Fetching real-time inventory from backend...</p>
                </div>
              )}

              {detailError && !detailLoading && (
                <div className="state-container" style={{ border: 'none', background: 'transparent' }}>
                  <div className="state-icon">⚠️</div>
                  <h3 className="state-title">Failed to Load Details</h3>
                  <p className="state-message">{detailError}</p>
                  <button
                    type="button"
                    className="state-btn"
                    onClick={() => handleOpenDetail(selectedProductId)}
                  >
                    Retry
                  </button>
                </div>
              )}

              {selectedProduct && !detailLoading && (
                <>
                  <div className="modal-hero-preview">
                    <span className="modal-hero-icon">
                      {getCategoryIcon(selectedProduct.category)}
                    </span>
                    <span className="modal-product-id">Product Reference #{selectedProduct.id}</span>
                  </div>

                  <h3 id="modal-title" className="modal-title">
                    {selectedProduct.name}
                  </h3>

                  <div className="modal-price-row">
                    <span className="modal-price">
                      ${typeof selectedProduct.price === 'number'
                        ? selectedProduct.price.toFixed(2)
                        : selectedProduct.price}
                    </span>
                  </div>

                  {selectedProduct.description && (
                    <p className="product-desc">{selectedProduct.description}</p>
                  )}

                  <div className="modal-details-grid">
                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Category</span>
                      <span className="modal-grid-val">{selectedProduct.category}</span>
                    </div>

                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Availability</span>
                      <span
                        className={`modal-grid-val stock-badge ${
                          selectedProduct.stock === 0 ? 'out-of-stock' : 'in-stock'
                        }`}
                      >
                        ● {selectedProduct.stock === 0 ? 'Out of Stock' : `${selectedProduct.stock} units available`}
                      </span>
                    </div>

                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Product ID</span>
                      <span className="modal-grid-val" style={{ fontFamily: 'monospace' }}>
                        {selectedProduct.id}
                      </span>
                    </div>

                    <div className="modal-grid-item">
                      <span className="modal-grid-label">Price</span>
                      <span className="modal-grid-val">
                        ${typeof selectedProduct.price === 'number'
                          ? selectedProduct.price.toFixed(2)
                          : selectedProduct.price}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="modal-btn-dismiss"
                onClick={handleCloseDetail}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
