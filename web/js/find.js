/* Find tab — job discovery & scoring (Agent A). Owns #tab-find. */
(() => {
  "use strict";

  // ---------- scoped styles ----------
  const style = document.createElement("style");
  style.id = "style-find";
  style.textContent = `
#tab-find .find-toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:10px; }
#tab-find .find-toolbar input[type="search"] { width:230px; }
#tab-find .find-toolbar input[type="number"] { width:100px; }
#tab-find .find-chips { display:flex; gap:6px; }
#tab-find .chip { border:1px solid var(--border); background:var(--surface); color:var(--text-dim); padding:5px 13px; border-radius:999px; font-size:12.5px; font-weight:600; cursor:pointer; }
#tab-find .chip:hover { background:#f0f3f7; }
#tab-find .chip.active { background:#e8efff; border-color:var(--accent); color:var(--accent-dark); }
#tab-find .find-summary { color:var(--text-dim); font-size:12.5px; margin:2px 2px 12px; }
#tab-find .find-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:12px; }
#tab-find .job-card { display:flex; flex-direction:column; gap:8px; }
#tab-find .job-head { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }
#tab-find .job-title { font-weight:700; font-size:14.5px; line-height:1.3; }
#tab-find .job-company { color:var(--text-dim); font-size:13px; margin-top:2px; }
#tab-find .job-meta { display:flex; flex-wrap:wrap; gap:6px; align-items:center; font-size:12px; color:var(--text-dim); }
#tab-find .score-badge { font-size:12.5px; font-weight:700; padding:2px 10px; border-radius:999px; white-space:nowrap; }
#tab-find .score-high { background:#dcfce7; color:#15803d; }
#tab-find .score-mid  { background:#fef3c7; color:#b45309; }
#tab-find .score-low  { background:#f3f4f6; color:#6b7280; }
#tab-find .source-tag { background:#eef1f5; border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; color:var(--text-dim); text-transform:capitalize; }
#tab-find .remote-badge { background:#ecfdf5; color:#0d9488; border:1px solid #0d948855; }
#tab-find .dream-badge { background:#f5f3ff; color:#7c3aed; border:1px solid #7c3aed55; }
#tab-find .job-actions { display:flex; gap:6px; margin-top:auto; flex-wrap:wrap; }
#tab-find .job-actions .btn { padding:5px 11px; font-size:12.5px; }
#tab-find #find-manual-form { margin-bottom:14px; max-width:760px; }
#tab-find #find-manual-form .form-row { display:flex; gap:10px; }
#tab-find #find-manual-form .form-row label.field { flex:1; }
#tab-find #find-manual-form .form-actions { display:flex; gap:8px; }
#find-drawer-backdrop { position:fixed; inset:0; background:rgba(15,23,42,.35); z-index:90; }
#find-drawer { position:fixed; top:0; right:0; bottom:0; width:min(680px, 94vw); background:var(--surface); border-left:1px solid var(--border); z-index:95; box-shadow:-8px 0 24px rgba(0,0,0,.14); display:flex; flex-direction:column; }
#find-drawer .drawer-head { padding:16px 20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
#find-drawer .drawer-body { padding:16px 20px; overflow-y:auto; flex:1; }
#find-drawer .drawer-actions { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 14px; }
#find-drawer .jd-text { white-space:pre-wrap; font-size:13px; line-height:1.55; }
#find-drawer .kw-chips { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 4px; }
#find-drawer .kw-chip { background:#e8efff; color:var(--accent-dark); border-radius:999px; padding:2px 10px; font-size:11.5px; font-weight:600; }
#find-drawer .drawer-section-label { font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:var(--text-dim); margin-top:14px; }
.toast-action { background:#1f2937; color:#fff; padding:10px 16px; border-radius:8px; font-size:13.5px; opacity:0; transform:translateY(8px); transition:all .25s ease; box-shadow:0 4px 14px rgba(0,0,0,.25); display:flex; align-items:center; gap:10px; }
.toast-action.show { opacity:1; transform:translateY(0); }
.toast-action button { background:var(--accent); color:#fff; border:none; border-radius:6px; padding:4px 12px; font-size:12.5px; font-weight:600; cursor:pointer; }
`;
  document.head.appendChild(style);

  // ---------- state ----------
  const state = { status: "new", dream: false, q: "", minScore: "", jobs: [], drawerJobId: null };

  // ---------- skeleton ----------
  const panel = document.getElementById("tab-find");
  panel.innerHTML = `
    <div class="find-toolbar">
      <button class="btn btn-primary" id="find-refresh">Refresh</button>
      <input type="search" id="find-q" placeholder="Search title, company, JD…">
      <input type="number" id="find-min-score" min="0" max="100" placeholder="Min score">
      <div class="find-chips" id="find-chips">
        <button class="chip active" data-status="new">New</button>
        <button class="chip" data-status="interested">Interested</button>
        <button class="chip" data-status="skipped">Skipped</button>
        <button class="chip" data-status="" data-dream="1">💜 Dream</button>
        <button class="chip" data-status="">All</button>
      </div>
      <button class="btn" id="find-add-manual">+ Add job manually</button>
    </div>
    <form id="find-manual-form" class="card" hidden>
      <label class="field">Job posting URL
        <input type="text" id="manual-url" placeholder="https://… (LinkedIn/Indeed links welcome — we fetch the page, never automate it)">
      </label>
      <div class="form-row">
        <label class="field">Title (optional)<input type="text" id="manual-title" placeholder="Senior Product Manager"></label>
        <label class="field">Company (optional)<input type="text" id="manual-company" placeholder="Acme"></label>
      </div>
      <label class="field">Job description (optional — paste if you have it)
        <textarea id="manual-description" rows="5" placeholder="Paste the JD text here…"></textarea>
      </label>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary" id="manual-submit">Add job</button>
        <button type="button" class="btn" id="manual-cancel">Cancel</button>
      </div>
    </form>
    <div class="find-summary" id="find-summary"></div>
    <div class="find-grid" id="find-grid"></div>
    <div id="find-drawer-wrap"></div>
  `;

  const $ = (id) => document.getElementById(id);

  // ---------- helpers ----------
  function scoreBadge(score) {
    const s = Number(score) || 0;
    const band = s >= 70 ? "score-high" : s >= 40 ? "score-mid" : "score-low";
    return `<span class="score-badge ${band}" title="Match score">${s}</span>`;
  }

  function fmtDate(iso) {
    return iso ? escapeHtml(String(iso).slice(0, 10)) : "";
  }

  function toastWithAction(msg, btnLabel, onClick) {
    const el = document.createElement("div");
    el.className = "toast-action";
    const span = document.createElement("span");
    span.textContent = msg;
    const btn = document.createElement("button");
    btn.textContent = btnLabel;
    btn.addEventListener("click", () => { el.remove(); onClick(); });
    el.append(span, btn);
    document.getElementById("toast-container").appendChild(el);
    setTimeout(() => el.classList.add("show"), 10);
    setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.remove(), 300); }, 8000);
  }

  // ---------- data ----------
  async function loadJobs() {
    const params = new URLSearchParams();
    if (state.status) params.set("status", state.status);
    if (state.dream) params.set("dream", "1");
    if (state.minScore !== "" && state.minScore !== null) params.set("min_score", state.minScore);
    if (state.q) params.set("q", state.q);
    try {
      state.jobs = await API.get(`/api/jobs/?${params.toString()}`);
      renderList();
    } catch (e) {
      $("find-grid").innerHTML = `<div class="empty-state">Could not load jobs: ${escapeHtml(e.message)}</div>`;
      $("find-summary").textContent = "";
    }
  }

  // ---------- rendering ----------
  function renderList() {
    const jobs = state.jobs;
    const newCount = jobs.filter(j => j.status === "new").length;
    $("find-summary").textContent = jobs.length
      ? `${jobs.length} job${jobs.length === 1 ? "" : "s"} · ${newCount} new`
      : "";
    if (!jobs.length) {
      $("find-grid").innerHTML = `<div class="empty-state" style="grid-column:1/-1">No jobs here yet. Hit <b>Refresh</b> to pull fresh postings, or add one manually.</div>`;
      return;
    }
    $("find-grid").innerHTML = jobs.map(cardHtml).join("");
  }

  function cardHtml(j) {
    const dream = j.dream ? `<span class="badge dream-badge">💜 Dream</span>` : "";
    const remote = j.remote ? `<span class="badge remote-badge">Remote</span>` : "";
    const salary = j.salary ? `<span title="Salary">💰 ${escapeHtml(j.salary)}</span>` : "";
    const posted = j.posted_at ? `<span title="Posted">${fmtDate(j.posted_at)}</span>` : "";
    const location = j.location ? `<span>${escapeHtml(j.location)}</span>` : "";
    const interestedBtn = j.status === "interested"
      ? `<button class="btn btn-primary" data-action="tailor" data-id="${j.id}">Tailor now →</button>`
      : `<button class="btn" data-action="interested" data-id="${j.id}">👍 Interested</button>`;
    const skipBtn = j.status === "skipped" ? "" : `<button class="btn" data-action="skip" data-id="${j.id}">👎 Skip</button>`;
    return `
      <div class="card job-card">
        <div class="job-head">
          <div>
            <div class="job-title">${escapeHtml(j.title)}</div>
            <div class="job-company">${escapeHtml(j.company || "Unknown company")}</div>
          </div>
          ${scoreBadge(j.score)}
        </div>
        <div class="job-meta">
          <span class="source-tag">${escapeHtml(j.source)}</span>
          ${dream} ${location} ${remote} ${salary} ${posted} ${statusBadge(j.status)}
        </div>
        <div class="job-actions">
          ${interestedBtn}
          ${skipBtn}
          <button class="btn" data-action="details" data-id="${j.id}">Details</button>
        </div>
      </div>`;
  }

  // ---------- drawer ----------
  async function openDrawer(jobId) {
    let j;
    try {
      j = await API.get(`/api/jobs/${jobId}`);
    } catch (e) {
      toast(`Could not load job: ${e.message}`, "error");
      return;
    }
    state.drawerJobId = j.id;
    const reasons = (j.score_reasons || []);
    const kwChips = reasons.length
      ? reasons.map(k => `<span class="kw-chip">${escapeHtml(k)}</span>`).join("")
      : `<span style="color:var(--text-dim);font-size:12.5px">No profile terms matched.</span>`;
    const link = j.url
      ? `<a href="${escapeHtml(j.url)}" target="_blank" rel="noopener noreferrer">Open original posting ↗</a>`
      : "";
    $("find-drawer-wrap").innerHTML = `
      <div id="find-drawer-backdrop"></div>
      <div id="find-drawer" role="dialog" aria-label="Job details">
        <div class="drawer-head">
          <div>
            <div class="job-title" style="font-size:16px">${escapeHtml(j.title)}</div>
            <div class="job-company">${escapeHtml(j.company || "Unknown company")} ${j.location ? "· " + escapeHtml(j.location) : ""}</div>
            <div class="job-meta" style="margin-top:6px">
              <span class="source-tag">${escapeHtml(j.source)}</span>
              ${j.dream ? `<span class="badge dream-badge">💜 Dream</span>` : ""}
              ${scoreBadge(j.score)} ${statusBadge(j.status)}
              ${j.salary ? `<span>💰 ${escapeHtml(j.salary)}</span>` : ""}
              ${j.posted_at ? `<span>${fmtDate(j.posted_at)}</span>` : ""}
            </div>
          </div>
          <button class="btn" id="drawer-close">✕</button>
        </div>
        <div class="drawer-body">
          <div class="drawer-actions">
            ${j.status === "interested"
              ? `<button class="btn btn-primary" data-action="tailor" data-id="${j.id}">Tailor now →</button>`
              : `<button class="btn btn-primary" data-action="interested" data-id="${j.id}">👍 Interested</button>`}
            ${j.status === "skipped" ? "" : `<button class="btn" data-action="skip" data-id="${j.id}">👎 Skip</button>`}
            ${link}
          </div>
          <div class="drawer-section-label">Why this scored ${Number(j.score) || 0}</div>
          <div class="kw-chips">${kwChips}</div>
          <div class="drawer-section-label">Job description</div>
          <div class="jd-text">${escapeHtml(j.description || "No description available.")}</div>
        </div>
      </div>`;
    $("drawer-close").addEventListener("click", closeDrawer);
    $("find-drawer-backdrop").addEventListener("click", closeDrawer);
  }

  function closeDrawer() {
    state.drawerJobId = null;
    $("find-drawer-wrap").innerHTML = "";
  }

  // ---------- actions ----------
  async function setStatus(jobId, status) {
    try {
      await API.post(`/api/jobs/${jobId}/status`, { status });
    } catch (e) {
      toast(`Update failed: ${e.message}`, "error");
      return;
    }
    if (status === "interested") {
      toastWithAction("Marked interested.", "Tailor now →", () => switchToTab("review", { jobId }));
    } else {
      toast(status === "skipped" ? "Skipped." : `Status: ${status}`, "success");
    }
    if (state.drawerJobId === jobId) closeDrawer();
    loadJobs();
  }

  async function doRefresh() {
    const btn = $("find-refresh");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span>Refreshing…`;
    try {
      const r = await API.post("/api/jobs/refresh");
      const per = Object.entries(r.per_source || {}).map(([k, v]) => `${k} ${v}`).join(" · ");
      const dreamNote = r.new_dream > 0 ? `, ${r.new_dream} from dream companies` : "";
      toast(`Fetched ${r.fetched} (${per}) — ${r.new} new${dreamNote}`, "success");
      if (r.errors && r.errors.length) {
        toast(`${r.errors.length} source error${r.errors.length === 1 ? "" : "s"}: ${r.errors[0]}`, "error");
        console.warn("refresh errors:", r.errors);
      }
      await loadJobs();
    } catch (e) {
      toast(`Refresh failed: ${e.message}`, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Refresh";
    }
  }

  async function submitManual(ev) {
    ev.preventDefault();
    const body = {};
    const url = $("manual-url").value.trim();
    const title = $("manual-title").value.trim();
    const company = $("manual-company").value.trim();
    const description = $("manual-description").value.trim();
    if (url) body.url = url;
    if (title) body.title = title;
    if (company) body.company = company;
    if (description) body.description = description;
    if (!url && !title && !description) {
      toast("Give me at least a URL or a title/description.", "error");
      return;
    }
    const btn = $("manual-submit");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span>Adding…`;
    try {
      const j = await API.post("/api/jobs/manual", body);
      toast(`Added "${j.title}" (score ${j.score})`, "success");
      $("find-manual-form").reset();
      $("find-manual-form").hidden = true;
      await loadJobs();
    } catch (e) {
      toast(`Could not add job: ${e.message}`, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Add job";
    }
  }

  // ---------- wiring ----------
  $("find-refresh").addEventListener("click", doRefresh);

  $("find-q").addEventListener("input", () => {
    state.q = $("find-q").value.trim();
    clearTimeout(state._qTimer);
    state._qTimer = setTimeout(loadJobs, 300);
  });

  $("find-min-score").addEventListener("change", () => {
    state.minScore = $("find-min-score").value;
    loadJobs();
  });

  $("find-chips").addEventListener("click", (ev) => {
    const chip = ev.target.closest(".chip");
    if (!chip) return;
    state.status = chip.dataset.status;
    state.dream = chip.dataset.dream === "1";
    document.querySelectorAll("#find-chips .chip").forEach(c => c.classList.toggle("active", c === chip));
    loadJobs();
  });

  $("find-add-manual").addEventListener("click", () => {
    const f = $("find-manual-form");
    f.hidden = !f.hidden;
    if (!f.hidden) $("manual-url").focus();
  });
  $("manual-cancel").addEventListener("click", () => { $("find-manual-form").hidden = true; });
  $("find-manual-form").addEventListener("submit", submitManual);

  // Card + drawer button actions (delegated; drawer buttons live in the wrap).
  panel.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-action]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (!id) return;
    if (btn.dataset.action === "interested") setStatus(id, "interested");
    else if (btn.dataset.action === "skip") setStatus(id, "skipped");
    else if (btn.dataset.action === "details") openDrawer(id);
    else if (btn.dataset.action === "tailor") switchToTab("review", { jobId: id });
  });

  TabHooks["find"] = loadJobs;
  loadJobs(); // render once at script load
})();
