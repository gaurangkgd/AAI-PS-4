/**
 * Reusable API client utility for communicating with the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Fetch helper for backend JSON endpoints.
 *
 * @param {string} endpoint - The API path, e.g. '/health' or '/products'
 * @param {RequestInit} [options={}] - Fetch configuration options
 * @returns {Promise<any>} Parsed JSON response
 * @throws {Error} When the HTTP response status is not 2xx
 */
export async function apiFetch(endpoint, options = {}) {
  const normalizedPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${normalizedPath}`;

  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  };

  const response = await fetch(url, config);

  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    if (data) {
      if (typeof data.detail === 'string') {
        errorDetail = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorDetail = data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      } else if (typeof data.message === 'string') {
        errorDetail = data.message;
      }
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export { API_BASE_URL };
