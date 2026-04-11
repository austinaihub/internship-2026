/**
 * API client for Agent-9 backend.
 * All endpoints return JSON with { state, session_id?, has_next? }
 */

const BASE = '';

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Start a new campaign with optional keywords */
export function startCampaign(keywords = '') {
  return request('/api/campaign/start', {
    method: 'POST',
    body: JSON.stringify({ keywords: keywords || null }),
  });
}

/** Get current state of a campaign */
export function getState(sessionId) {
  return request(`/api/campaign/${sessionId}/state`);
}

/** Approve or re-search at the trend review checkpoint */
export function approveTrend(sessionId, { action, customTopic, selectedArticleTitle, guidance }) {
  return request(`/api/campaign/${sessionId}/approve-trend`, {
    method: 'POST',
    body: JSON.stringify({
      action,
      custom_topic: customTopic || null,
      selected_article_title: selectedArticleTitle || null,
      guidance: guidance || null,
    }),
  });
}

/** Approve or reject at the image review checkpoint */
export function approveImage(sessionId, { action, feedback }) {
  return request(`/api/campaign/${sessionId}/approve-image`, {
    method: 'POST',
    body: JSON.stringify({ action, feedback: feedback || null }),
  });
}

/** Refine the campaign (creates a new session) */
export function refineCampaign(sessionId, { target, feedback }) {
  return request(`/api/campaign/${sessionId}/refine`, {
    method: 'POST',
    body: JSON.stringify({ target, feedback }),
  });
}

/** Build the URL for a generated image */
export function getImageUrl(imagePath) {
  if (!imagePath || imagePath === 'REJECTED') return null;
  // Extract just the filename from the full path
  const filename = imagePath.replace(/\\/g, '/').split('/').pop();
  return `/api/campaign/image/${filename}`;
}
