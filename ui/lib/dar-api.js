/**
 * dar-api.js — shared API client for DAR admin and dashboard.
 * Handles auth, token storage, and all fetch calls.
 */

export const DarAPI = (() => {
  let _token = null;
  let _accountId = null;
  let _apiBase = '';
  let _onUnauthorised = () => {};

  function init({ apiBase, onUnauthorised }) {
    _apiBase = apiBase;
    _onUnauthorised = onUnauthorised || (() => {});
    _token = sessionStorage.getItem('dar_token');
    _accountId = sessionStorage.getItem('dar_account_id');
  }

  function isAuthenticated() {
    return !!_token;
  }

  function getAccountId() {
    return _accountId;
  }

  async function login(accountId, secretKey) {
    const creds = btoa(`${accountId}:${secretKey}`);
    const r = await fetch(`${_apiBase}/v1/auth/token`, {
      headers: { 'Authorization': `Basic ${creds}` }
    });
    if (!r.ok) return { ok: false, status: r.status };
    const data = await r.json();
    _token = data['bearer-token'];
    _accountId = accountId;
    sessionStorage.setItem('dar_token', _token);
    sessionStorage.setItem('dar_account_id', _accountId);
    return { ok: true, data };
  }

  function logout() {
    _token = null;
    _accountId = null;
    sessionStorage.removeItem('dar_token');
    sessionStorage.removeItem('dar_account_id');
  }

  async function request(path, opts = {}) {
    const r = await fetch(`${_apiBase}${path}`, {
      ...opts,
      headers: {
        'Authorization': `Bearer ${_token}`,
        'Content-Type': 'application/json',
        ...(opts.headers || {}),
      },
    });
    if (r.status === 401) { _onUnauthorised(); return null; }
    return r;
  }

  async function get(path)              { return request(path); }
  async function post(path, body)       { return request(path, { method: 'POST',   body: JSON.stringify(body) }); }
  async function put(path, body)        { return request(path, { method: 'PUT',    body: JSON.stringify(body) }); }
  async function patch(path, body)      { return request(path, { method: 'PATCH',  body: JSON.stringify(body) }); }
  async function del(path, body = null) { return request(path, { method: 'DELETE', ...(body ? { body: JSON.stringify(body) } : {}) }); }

  return { init, isAuthenticated, getAccountId, login, logout, get, post, put, patch, del };
})();
