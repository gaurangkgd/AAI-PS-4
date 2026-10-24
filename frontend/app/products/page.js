'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { apiFetch } from '../../lib/api';
import ProductCard from '../../components/ProductCard';
import ProductDetailModal from '../../components/ProductDetailModal';
import { IconSearch, IconSparkles, IconAlertTriangle } from '../../components/Icons';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('featured');

  // Detail Modal state
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  // Load products from backend
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

  // Load individual product detail for modal
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

  // Compute category list
  const categories = useMemo(() => {
    const set = new Set(['All']);
    products.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set);
  }, [products]);

  // Filtered & Sorted products
  const filteredProducts = useMemo(() => {
    let result = [...products];

    // Category filter
    if (selectedCategory !== 'All') {
      result = result.filter(
        (p) => p.category?.toLowerCase() === selectedCategory.toLowerCase()
      );
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.category?.toLowerCase().includes(q) ||
          p.id?.toLowerCase().includes(q)
      );
    }

    // Sorting
    if (sortBy === 'price-low') {
      result.sort((a, b) => (a.price || 0) - (b.price || 0));
    } else if (sortBy === 'price-high') {
      result.sort((a, b) => (b.price || 0) - (a.price || 0));
    } else if (sortBy === 'name') {
      result.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    }

    return result;
  }, [products, selectedCategory, searchQuery, sortBy]);

  return (
    <div className="container products-page-container">
      {/* Page Header */}
      <section className="catalog-header">
        <div className="catalog-header-text">
          <span className="catalog-eyebrow">The 2026 Collection</span>
          <h1 className="catalog-title">Curated Products &amp; Daily Essentials</h1>
          <p className="catalog-subtitle">
            Explore our complete catalog of precision electronics, acoustic gear, and sustainable
            lifestyle apparel &mdash; each verified for performance and craftsmanship.
          </p>
        </div>

        {/* AI Support Teaser Banner */}
        <div className="catalog-ai-banner">
          <div className="ai-banner-content">
            <div className="ai-banner-icon">
              <IconSparkles size={18} />
            </div>
            <div>
              <strong>Unsure which product fits your workflow?</strong>
              <p>Our 24/7 AI Concierge can suggest gear, check compatibility, and track shipments.</p>
            </div>
          </div>
          <Link href="/support" className="btn-ai-consult">
            Ask AI Concierge &rarr;
          </Link>
        </div>
      </section>

      {/* Control Bar: Categories, Search, and Sort */}
      <div className="catalog-controls-bar">
        {/* Category Pills */}
        <div className="category-filter-pills" role="tablist" aria-label="Product Categories">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              role="tab"
              aria-selected={selectedCategory === cat}
              className={`cat-pill ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search & Sort Group */}
        <div className="catalog-search-sort">
          <div className="search-input-wrap">
            <span className="search-icon">
              <IconSearch size={15} />
            </span>
            <input
              type="text"
              placeholder="Search products, categories, SKU..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="catalog-search-input"
              aria-label="Search products"
            />
            {searchQuery && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search query"
              >
                Clear
              </button>
            )}
          </div>

          <div className="sort-dropdown-wrap">
            <label htmlFor="sort-select" className="sort-label">Sort by:</label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="catalog-sort-select"
            >
              <option value="featured">Featured Collection</option>
              <option value="price-low">Price: Low to High</option>
              <option value="price-high">Price: High to Low</option>
              <option value="name">Product Name (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Count & Active Filters */}
      <div className="catalog-status-bar">
        <span>
          Showing <strong>{filteredProducts.length}</strong> {filteredProducts.length === 1 ? 'item' : 'items'}
          {selectedCategory !== 'All' ? ` in ${selectedCategory}` : ''}
          {searchQuery ? ` matching "${searchQuery}"` : ''}
        </span>

        {(selectedCategory !== 'All' || searchQuery) && (
          <button
            type="button"
            className="btn-reset-filters"
            onClick={() => {
              setSelectedCategory('All');
              setSearchQuery('');
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Products Grid / State Views */}
      {loading && (
        <div className="product-grid" aria-label="Loading catalog">
          {[1, 2, 3, 4, 5, 6].map((n) => (
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

      {!loading && error && (
        <div className="state-container" role="alert">
          <div className="state-icon">
            <IconAlertTriangle size={32} />
          </div>
          <h3 className="state-title">Unable to Load Catalog</h3>
          <p className="state-message">
            Could not connect to the inventory service ({error}). Please ensure the backend is active.
          </p>
          <button type="button" className="state-btn" onClick={loadProducts}>
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && filteredProducts.length === 0 && (
        <div className="state-container">
          <div className="state-icon">
            <IconSearch size={32} />
          </div>
          <h3 className="state-title">No Matching Products Found</h3>
          <p className="state-message">
            We could not find any products matching your current filters. Try searching for "Headphones", "Keyboard", or resetting your filters.
          </p>
          <button
            type="button"
            className="state-btn"
            onClick={() => {
              setSelectedCategory('All');
              setSearchQuery('');
            }}
          >
            Show All Products
          </button>
        </div>
      )}

      {!loading && !error && filteredProducts.length > 0 && (
        <div className="product-grid">
          {filteredProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onSelect={handleOpenDetail}
            />
          ))}
        </div>
      )}

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
