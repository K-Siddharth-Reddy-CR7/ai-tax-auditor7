const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchProducts(query = '', limit = 20) {
  const res = await fetch(`${API_BASE}/products?query=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

export async function fetchCountries() {
  const res = await fetch(`${API_BASE}/countries`);
  if (!res.ok) throw new Error('Failed to fetch countries');
  return res.json();
}

export async function runAgenticAudit(payload) {
  const res = await fetch(`${API_BASE}/audit/agentic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Audit failed');
  return data.data;
}

export async function runNormalAudit(payload) {
  const res = await fetch(`${API_BASE}/audit/normal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Normal audit failed');
  return data.data;
}

export async function runCompareAudit(payload) {
  const res = await fetch(`${API_BASE}/audit/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Comparison failed');
  return data.data;
}

export async function fetchTransactions({ limit = 50, offset = 0, search = '', risk = '' } = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    search,
    risk
  });
  const res = await fetch(`${API_BASE}/transactions?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch transactions');
  return res.json();
}

export async function fetchPolicies({ query = '', country = '', category = '', limit = 50 } = {}) {
  const params = new URLSearchParams({
    query,
    country,
    category,
    limit: String(limit)
  });
  const res = await fetch(`${API_BASE}/policies?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch policies');
  return res.json();
}
