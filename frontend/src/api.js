const API_BASE = '/api';

export const fetchHealth = async () => {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const scanTrends = async (mock = false, maxResults = 15, sources = '') => {
  const res = await fetch(`${API_BASE}/scan?mock=${mock}&max_results=${maxResults}&sources=${sources}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const generateAngles = async (mock = false, maxTrends = 8, anglesPerTrend = 3, sources = '', provider = 'gemini') => {
  const res = await fetch(`${API_BASE}/angles/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mock, max_trends: maxTrends, angles_per_trend: anglesPerTrend, sources, provider }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const fetchSources = async () => {
  const res = await fetch(`${API_BASE}/sources`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const fetchSourceEntries = async (name) => {
  const res = await fetch(`${API_BASE}/sources/${name}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const addSourceEntry = async (name, entry) => {
  const res = await fetch(`${API_BASE}/sources/${name}/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const fetchSeedKeywords = async (name) => {
  const res = await fetch(`${API_BASE}/sources/${name}/seeds`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const fetchSettings = async () => {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const updateSettings = async (updates) => {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const fetchBrandProfile = async () => {
  const res = await fetch(`${API_BASE}/brands/profile`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const uploadBrandPdf = async (file, brandName) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('brand_name', brandName);
  const res = await fetch(`${API_BASE}/brands/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const clearBrandData = async () => {
  const res = await fetch(`${API_BASE}/brands`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};

export const updateAngleStatus = async (filenameStem, status) => {
  const res = await fetch(`${API_BASE}/angles/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename_stem: filenameStem, status }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
};
