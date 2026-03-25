/**
 * dar-components.js — shared UI primitives for DAR admin and dashboard.
 */

// ── Badges ────────────────────────────────────────────────────────────────────

export function stateBadge(state) {
  const map = { ACTIVE: 'badge-green', REVOKED: 'badge-red', EXPIRED: 'badge-amber', DISCOVERED: 'badge-grey' };
  return `<span class="badge ${map[state] || 'badge-grey'}">${state}</span>`;
}

export function roleBadge(role) {
  const map = { data_user: 'badge-blue', data_provider: 'badge-green', dcc: 'badge-amber', admin: 'badge-red' };
  return `<span class="badge ${map[role] || 'badge-grey'}">${role}</span>`;
}

export function statusBadge(status) {
  return `<span class="badge ${status === 'active' ? 'badge-green' : 'badge-red'}">${status || 'active'}</span>`;
}

export function basisBadge(basis) {
  return `<span class="badge badge-mono">${basis || '—'}</span>`;
}

export function eventTypeBadge(t) {
  const map = {
    'record.created': 'badge-green', 'record.updated': 'badge-blue',
    'record.revoked': 'badge-red',   'account.created': 'badge-blue',
    'account.suspended': 'badge-amber', 'account.reactivated': 'badge-green',
  };
  return `<span class="badge ${map[t] || 'badge-grey'} badge-mono">${t}</span>`;
}

// ── Toast ─────────────────────────────────────────────────────────────────────

export function toast(msg, type = '') {
  let container = document.getElementById('dar-toasts');
  if (!container) {
    container = document.createElement('div');
    container.id = 'dar-toasts';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Modal ─────────────────────────────────────────────────────────────────────

export function openModal(id)  { document.getElementById(id).style.display = 'block'; }
export function closeModal(id) { document.getElementById(id).style.display = 'none'; }

export function createModal({ id, title, body, footer }) {
  const existing = document.getElementById(id);
  if (existing) existing.remove();
  const el = document.createElement('div');
  el.id = id;
  el.style.display = 'none';
  el.innerHTML = `
    <div class="modal-backdrop" onclick="if(event.target===this)this.parentElement.style.display='none'">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">${title}</div>
          <button class="modal-close" onclick="document.getElementById('${id}').style.display='none'">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">${body}</div>
        <div class="modal-footer">${footer}</div>
      </div>
    </div>`;
  document.body.appendChild(el);
  return el;
}

// ── Drawer ────────────────────────────────────────────────────────────────────

export function openDrawer({ ak, sections, footer }) {
  let wrap = document.getElementById('dar-drawer-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'dar-drawer-wrap';
    wrap.innerHTML = `
      <div class="drawer-backdrop" onclick="closeDrawer()"></div>
      <div class="drawer">
        <div class="drawer-header">
          <div>
            <div class="drawer-title">Access Record</div>
            <div class="drawer-ak" id="dar-drawer-ak"></div>
          </div>
          <button class="modal-close" onclick="closeDrawer()">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="drawer-body" id="dar-drawer-body"></div>
        <div class="drawer-footer" id="dar-drawer-footer"></div>
      </div>`;
    document.body.appendChild(wrap);
  }
  document.getElementById('dar-drawer-ak').textContent = ak;
  document.getElementById('dar-drawer-body').innerHTML = sections.map(s => `
    <div class="drawer-section">
      <div class="drawer-section-title">${s.title}</div>
      ${s.rows.map(([label, value]) => `
        <div class="detail-row">
          <div class="detail-label">${label}</div>
          <div class="detail-value">${value || '—'}</div>
        </div>`).join('')}
    </div>`).join('');
  document.getElementById('dar-drawer-footer').innerHTML = footer;
  wrap.style.display = 'block';
}

export function closeDrawer() {
  const w = document.getElementById('dar-drawer-wrap');
  if (w) w.style.display = 'none';
}
// Make globally accessible for inline onclick handlers
window.closeDrawer = closeDrawer;

// ── Table helpers ─────────────────────────────────────────────────────────────

export function setTableLoading(tbodyId, cols) {
  document.getElementById(tbodyId).innerHTML =
    `<tr><td colspan="${cols}"><div class="loading-row"><div class="spinner"></div></div></td></tr>`;
}

export function setTableEmpty(tbodyId, cols, msg = 'No results found') {
  document.getElementById(tbodyId).innerHTML =
    `<tr class="empty-row"><td colspan="${cols}">${msg}</td></tr>`;
}

// ── Audit feed ────────────────────────────────────────────────────────────────

export function renderAuditList(events, containerId) {
  const el = document.getElementById(containerId);
  if (!events.length) {
    el.innerHTML = `<div class="empty-feed">No events</div>`;
    return;
  }
  el.innerHTML = events.map(e => `
    <div class="event-row">
      <div class="event-time">${fmtDatetime(e.timestamp)}</div>
      <div class="event-account">${e.account_id || '—'}</div>
      <div>${eventTypeBadge(e.event_type)}</div>
      <div class="event-detail">${fmtAuditDetail(e.detail)}</div>
    </div>`).join('');
}

function fmtAuditDetail(d) {
  if (!d) return '—';
  const parts = [];
  if (d.ak)         parts.push(d.ak);
  if (d.mpxn)       parts.push(`mpxn:${d.mpxn}`);
  if (d.account_id) parts.push(d.account_id);
  if (d.role)       parts.push(d.role);
  return parts.join(' · ') || JSON.stringify(d).substring(0, 80);
}

// ── Utilities ─────────────────────────────────────────────────────────────────

export function fmtDate(s) {
  if (!s) return '—';
  try { return new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); }
  catch { return s; }
}

export function fmtDatetime(s) {
  if (!s) return '—';
  try {
    const d = new Date(s);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + ' ' +
           d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return s; }
}

export function randHex(n) {
  return Array.from(crypto.getRandomValues(new Uint8Array(n / 2)))
    .map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text);
  toast('Copied to clipboard');
}
window.copyToClipboard = copyToClipboard;

export function debounce(fn, ms = 400) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── Login screen builder ──────────────────────────────────────────────────────

export function buildLoginScreen({ logoColor, title, subtitle, onLogin }) {
  return `
    <div id="login-screen">
      <div class="login-card">
        <div class="login-logo">
          <div class="login-mark" style="background:${logoColor}">
            <svg width="16" height="16" fill="none" stroke="white" stroke-width="2.5" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <div class="login-title">${title}</div>
            <div class="login-sub">${subtitle}</div>
          </div>
        </div>
        <label>Account ID</label>
        <input type="text" id="login-account" placeholder="account_id" autocomplete="username">
        <label>Secret Key</label>
        <input type="password" id="login-secret" placeholder="••••••••" autocomplete="current-password">
        <div id="login-error" style="display:none"></div>
        <button class="btn btn-primary btn-full" onclick="${onLogin}()">Sign in</button>
      </div>
    </div>`;
}
