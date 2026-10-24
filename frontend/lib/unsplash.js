/**
 * Unsplash Image Provider & Product Photography Engine.
 * Provides curated, ultra-high-definition product imagery from Unsplash,
 * with real-time Unsplash API integration support when an access key is supplied.
 */

// Curated high-res Unsplash photography for store catalog products
export const PRODUCT_IMAGE_MAP = {
  PROD001: {
    url: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&auto=format&fit=crop&q=75',
    alt: 'Matte black wireless noise-canceling headphones with premium cushion padding',
    badge: 'Bestseller',
    rating: 4.9,
    reviewsCount: 142,
    specs: ['Active Hybrid ANC', '40-Hour Battery Life', 'Bluetooth 5.3 Multipoint'],
  },
  PROD002: {
    url: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&auto=format&fit=crop&q=75',
    alt: 'Ergonomic custom mechanical keyboard with tactile switches and backlighting',
    badge: 'Staff Pick',
    rating: 4.8,
    reviewsCount: 89,
    specs: ['Gateron Brown Switches', 'Hot-Swappable PCB', 'Anodized Aluminum Frame'],
  },
  PROD003: {
    url: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&auto=format&fit=crop&q=75',
    alt: 'Lightweight performance running shoes in vibrant crimson red',
    badge: 'Trending',
    rating: 4.7,
    reviewsCount: 104,
    specs: ['Breathable Mesh Upper', 'Responsive Foam Sole', 'Carbon Energy Plate'],
  },
  PROD004: {
    url: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400&auto=format&fit=crop&q=75',
    alt: 'Insulated stainless steel thermal water bottle with matte earth-tone powder coat',
    badge: 'Eco-Choice',
    rating: 4.9,
    reviewsCount: 215,
    specs: ['24h Cold / 12h Hot', '18/8 Pro-Grade Steel', 'BPA-Free Leakproof Cap'],
  },
  PROD005: {
    url: 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1625842268584-8f3296236761?w=400&auto=format&fit=crop&q=75',
    alt: 'Sleek aluminum space gray USB-C multi-port adapter hub',
    badge: 'Restocking Soon',
    rating: 4.6,
    reviewsCount: 68,
    specs: ['4K HDMI @ 60Hz', '100W Power Delivery', 'SD & MicroSD Card Readers'],
  },
  PROD006: {
    url: 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=85',
    thumbnail: 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=400&auto=format&fit=crop&q=75',
    alt: 'Relaxed fit heavyweight organic cotton hoodie in heather grey',
    badge: 'Popular',
    rating: 4.8,
    reviewsCount: 119,
    specs: ['100% GOTS Organic Cotton', '400 GSM Heavyweight Fleece', 'Pre-Shrunk Finish'],
  },
};

// Category fallback hero images from Unsplash
export const CATEGORY_HEROES = {
  Electronics: {
    title: 'Precision Electronics',
    tagline: 'High-performance audio, tactile keyboards, and workspace connectivity.',
    image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&auto=format&fit=crop&q=80',
    count: '3 Products',
  },
  Apparel: {
    title: 'Everyday Apparel',
    tagline: 'Sustainably sourced fabrics, tailored silhouettes, and enduring comfort.',
    image: 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=800&auto=format&fit=crop&q=80',
    count: '2 Products',
  },
  'Home & Kitchen': {
    title: 'Home & Living',
    tagline: 'Mindfully crafted thermal gear and daily essentials for home or travel.',
    image: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&auto=format&fit=crop&q=80',
    count: '1 Product',
  },
};

// Generic category fallback images
const CATEGORY_FALLBACKS = {
  electronics: 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=800&auto=format&fit=crop&q=80',
  apparel: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&auto=format&fit=crop&q=80',
  clothing: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&auto=format&fit=crop&q=80',
  'home & kitchen': 'https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&auto=format&fit=crop&q=80',
  home: 'https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&auto=format&fit=crop&q=80',
  kitchen: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&auto=format&fit=crop&q=80',
};

const DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop&q=80';

// In-memory cache for any live Unsplash API fetches
const unsplashApiCache = new Map();

/**
 * Returns complete product photography and metadata for a given product item.
 *
 * @param {Object} product
 * @returns {{ url: string, thumbnail: string, alt: string, badge?: string, rating: number, reviewsCount: number, specs: string[] }}
 */
export function getProductImageData(product) {
  if (!product) {
    return {
      url: DEFAULT_IMAGE,
      thumbnail: DEFAULT_IMAGE,
      alt: 'NextStore product item',
      badge: null,
      rating: 4.8,
      reviewsCount: 50,
      specs: ['Premium Quality', 'Designed for Durability'],
    };
  }

  const id = (product.id || '').toUpperCase();
  if (PRODUCT_IMAGE_MAP[id]) {
    return PRODUCT_IMAGE_MAP[id];
  }

  // Lookup by category match
  const catKey = (product.category || '').toLowerCase();
  let matchedFallback = DEFAULT_IMAGE;
  for (const [key, url] of Object.entries(CATEGORY_FALLBACKS)) {
    if (catKey.includes(key)) {
      matchedFallback = url;
      break;
    }
  }

  return {
    url: matchedFallback,
    thumbnail: matchedFallback,
    alt: product.name || 'NextStore Product',
    badge: product.stock === 0 ? 'Out of Stock' : null,
    rating: 4.8,
    reviewsCount: 38,
    specs: ['Authentic Materials', 'Quality Tested'],
  };
}

/**
 * Optional live fetch from Unsplash API if NEXT_PUBLIC_UNSPLASH_ACCESS_KEY is available.
 * Gracefully falls back to curated static Unsplash imagery.
 *
 * @param {string} query
 * @returns {Promise<string>} Image URL
 */
export async function searchUnsplashImage(query) {
  const accessKey = process.env.NEXT_PUBLIC_UNSPLASH_ACCESS_KEY;
  if (!accessKey || !query) {
    return null;
  }

  const cacheKey = query.trim().toLowerCase();
  if (unsplashApiCache.has(cacheKey)) {
    return unsplashApiCache.get(cacheKey);
  }

  try {
    const res = await fetch(
      `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&per_page=1&orientation=landscape`,
      {
        headers: {
          Authorization: `Client-ID ${accessKey}`,
        },
      }
    );

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    if (data.results && data.results.length > 0) {
      const photoUrl = data.results[0].urls.regular;
      unsplashApiCache.set(cacheKey, photoUrl);
      return photoUrl;
    }
  } catch (err) {
    console.warn('Unsplash API search failed, falling back to curated imagery:', err.message);
  }

  return null;
}
