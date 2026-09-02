/* Shared chrome: tabs, API helper, toasts, status metadata. Owned by orchestrator. */

const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
    return r.json();
  },
};

/* Keep in sync with backend/db.py JOB_STATUSES */
const STATUS_META = {
  new:        { label: "New",         color: "#6b7280" },
  interested: { label: "Interested",  color: "#2563eb" },
  skipped:    { label: "Skipped",     color: "#9ca3af" },
  tailoring:  { label: "Tailoring…",  color: "#d97706" },
  tailored:   { label: "Tailored",    color: "#7c3aed" },
  ready:      { label: "Ready",       color: "#0d9488" },
  submitting: { label: "Submitting…", color: "#d97706" },
  submitted:  { label: "Submitted",   color: "#16a34a" },
  interview:  { label: "Interview!",  color: "#15803d" },
  rejected:   { label: "Rejected",    color: "#dc2626" },
  archived:   { label: "Archived",    color: "#9ca3af" },
};

function statusBadge(status) {
  const m = STATUS_META[status] || { label: status, color: "#6b7280" };
  return `<span class="badge" style="background:${m.color}1a;color:${m.color};border:1px solid ${m.color}55">${m.label}</span>`;
}

function toast(msg, kind = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${kind}`;
  el.textContent = msg;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.classList.add("show"), 10);
  setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.remove(), 300); }, 4200);
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* Tab switching. Modules register an onShow callback to refresh when shown. */
const TabHooks = {};
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});
function activateTab(name) {
  document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `tab-${name}`));
  if (TabHooks[name]) TabHooks[name]();
}

/* Allow other modules to deep-link: switchToTab('review', {jobId: 5}) */
let pendingTabContext = null;
function switchToTab(name, context) {
  pendingTabContext = context || null;
  activateTab(name);
}
function consumeTabContext() {
  const c = pendingTabContext;
  pendingTabContext = null;
  return c;
}

async function refreshHealth() {
  try {
    const h = await API.get("/api/health");
    const el = document.getElementById("health-indicator");
    el.style.color = "#16a34a";
    el.title = `Backend OK · LLM tailoring: ${h.anthropic_key ? "on" : "off (add ANTHROPIC_API_KEY to .env)"} · Auto-fill: ${h.playwright ? "on" : "off"}`;
    window.HEALTH = h;
  } catch {
    document.getElementById("health-indicator").style.color = "#dc2626";
  }
}
refreshHealth();
