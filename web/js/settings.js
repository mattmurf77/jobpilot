/* Settings tab — search config, watchlist, profile, screeners, AI key, materials. Agent C. */
(function () {
  const panel = document.getElementById("tab-settings");

  const PROFILE_FIELDS = [
    ["name", "Full name"], ["first_name", "First name"], ["last_name", "Last name"],
    ["preferred_name", "Preferred name"], ["email", "Email"], ["phone", "Phone"],
    ["location", "Location"], ["city", "City"], ["state", "State"], ["country", "Country"],
    ["linkedin", "LinkedIn URL"], ["website", "Website"],
    ["current_title", "Current title"], ["current_company", "Current company"],
  ];
  const MATERIAL_LABELS = {
    resume_template_html: "Resume template (HTML)",
    line_menu: "Resume line menu",
    generalization_guide: "Generalization guide",
    resume_best_practices: "Resume best practices",
    cover_letter_best_practices: "Cover letter best practices",
    html_to_pdf_script: "HTML→PDF renderer",
  };

  let data = null; // last GET /api/settings payload
  let dreamResultHtml = ""; // last dream test result, survives the post-save re-render

  async function refresh() {
    try {
      data = await API.get("/api/settings");
      render();
    } catch (e) {
      panel.innerHTML = `<div class="empty-state">Failed to load settings: ${escapeHtml(e.message)}</div>`;
    }
  }

  /* ---------- rendering ---------- */

  const csv = (arr) => (arr || []).join(", ");

  function render() {
    const cfg = data.config || {};
    const search = cfg.search || {};
    const watch = cfg.watchlist || {};
    const profile = data.profile || {};
    const screeners = profile.screener_answers || {};

    panel.innerHTML = `<div class="st-grid">

      <div class="card st-card">
        <h3>Search</h3>
        <label class="field">Keywords (comma-separated)
          <input type="text" id="st-keywords" value="${escapeHtml(csv(search.keywords))}"></label>
        <label class="field">Domain terms (comma-separated)
          <input type="text" id="st-domain-terms" value="${escapeHtml(csv(search.domain_terms))}"></label>
        <label class="field">Locations (comma-separated)
          <input type="text" id="st-locations" value="${escapeHtml(csv(search.locations))}"></label>
        <div class="st-inline">
          <label class="st-check"><input type="checkbox" id="st-remote-only" ${search.remote_only ? "checked" : ""}> Remote only</label>
          <label class="field st-minscore">Min score
            <input type="number" id="st-min-score" min="0" max="100" value="${Number(search.min_score) || 0}"></label>
        </div>
        <button class="btn btn-primary" data-act="save-search">Save search settings</button>
      </div>

      <div class="card st-card">
        <h3>Company watchlist</h3>
        <label class="field">Greenhouse board slugs (comma-separated)
          <input type="text" id="st-gh-slugs" value="${escapeHtml(csv(watch.greenhouse))}"></label>
        <label class="field">Lever board slugs (comma-separated)
          <input type="text" id="st-lever-slugs" value="${escapeHtml(csv(watch.lever))}"></label>
        <p class="st-hint">The slug is the company segment of the board URL, e.g.
          <code>boards.greenhouse.io/<b>stripe</b></code> or <code>jobs.lever.co/<b>highnote</b></code>.</p>
        <button class="btn btn-primary" data-act="save-watchlist">Save watchlist</button>
      </div>

      <div class="card st-card">
        <h3>💜 Dream companies</h3>
        <p class="st-hint">Monitored on every refresh regardless of keyword filters; postings get a
          score boost and a 💜 badge. Works best with Greenhouse / Lever / Ashby / Workable /
          SmartRecruiters boards; custom career pages are monitored by page-change detection.</p>
        <div id="st-dream-rows">
          ${(cfg.dream_companies || []).map((c, i) => `
            <div class="st-dream-row">
              <span class="st-dream-name">${escapeHtml(c.name || "")}</span>
              <span class="st-dream-url" title="${escapeHtml(c.url || "")}">${escapeHtml(c.url || "")}</span>
              <span class="st-dream-ats">${escapeHtml(c.ats || "auto")}</span>
              ${Number.isFinite(c.postings_found) ? `<span class="st-dream-count">${c.postings_found} postings</span>` : ""}
              <button class="btn st-del" data-act="del-dream" data-idx="${i}" title="Remove">✕</button>
            </div>`).join("") || `<p class="st-hint">No dream companies yet — add one below.</p>`}
        </div>
        <div class="st-dream-new">
          <input type="text" id="st-dream-name" placeholder="Company name">
          <input type="text" id="st-dream-url" placeholder="https://… careers page or board URL">
          <button class="btn" data-act="test-dream" id="st-dream-test">Test &amp; add</button>
        </div>
        <div id="st-dream-result">${dreamResultHtml}</div>
      </div>

      <div class="card st-card">
        <h3>Profile</h3>
        <div class="st-two-col">
          ${PROFILE_FIELDS.map(([key, label]) => `
            <label class="field">${escapeHtml(label)}
              <input type="text" id="st-p-${key}" value="${escapeHtml(profile[key] ?? "")}"></label>`).join("")}
        </div>
        <button class="btn btn-primary" data-act="save-profile">Save profile</button>
      </div>

      <div class="card st-card">
        <h3>Screener answers</h3>
        <p class="st-hint">Default answers used for application screener questions (auto-fill and copy-paste assist).</p>
        <div id="st-screeners">
          ${Object.entries(screeners).map(([k, v]) => `
            <div class="st-screener-row" data-key="${escapeHtml(k)}">
              <span class="st-screener-key" title="${escapeHtml(k)}">${escapeHtml(k.replace(/_/g, " "))}</span>
              <input type="text" class="st-screener-val" value="${escapeHtml(v)}">
              <button class="btn st-del" data-act="del-screener" title="Remove">✕</button>
            </div>`).join("")}
        </div>
        <div class="st-screener-row st-screener-new">
          <input type="text" id="st-new-key" placeholder="new_question_key">
          <input type="text" id="st-new-val" placeholder="Answer">
          <button class="btn" data-act="add-screener">Add</button>
        </div>
        <button class="btn btn-primary" data-act="save-profile">Save answers</button>
      </div>

      <div class="card st-card">
        <h3>AI &amp; automation</h3>
        <p class="st-status">LLM tailoring:
          ${data.anthropic_key_set ? '<span class="st-on">on</span>' : '<span class="st-off">off</span> — add your Anthropic API key below'}</p>
        <p class="st-status">Auto-fill (Playwright):
          ${data.playwright ? '<span class="st-on">on</span>' : '<span class="st-off">off</span> — assisted submission only'}</p>
        <label class="field">Anthropic API key (stored in .env, never displayed)
          <input type="password" id="st-apikey" placeholder="sk-ant-…" autocomplete="off"></label>
        <button class="btn btn-primary" data-act="save-apikey">Save key</button>
      </div>

      <div class="card st-card">
        <h3>Source materials</h3>
        <p class="st-hint">Ground-truth files the tailoring engine may draw from (read-only — edit config.json to change paths).</p>
        <ul class="st-materials">
          ${Object.entries(data.materials_status || {}).map(([k, m]) => `
            <li><span class="${m.exists ? "st-on" : "st-off"}">${m.exists ? "✓" : "✗"}</span>
              <b>${escapeHtml(MATERIAL_LABELS[k] || k)}</b>
              <span class="st-path" title="${escapeHtml(m.path)}">${escapeHtml(m.path)}</span></li>`).join("")}
        </ul>
      </div>

    </div>`;
  }

  /* ---------- collect + save ---------- */

  const parseCsv = (id) => (document.getElementById(id).value || "")
    .split(",").map(s => s.trim()).filter(Boolean);

  async function saveConfig(mutate) {
    const cfg = JSON.parse(JSON.stringify(data.config)); // full config; mutate one section
    mutate(cfg);
    try {
      await API.post("/api/settings/config", cfg);
      toast("Settings saved.", "success");
      await refresh();
    } catch (e) { toast(e.message, "error"); }
  }

  function collectProfile() {
    const profile = JSON.parse(JSON.stringify(data.profile));
    for (const [key] of PROFILE_FIELDS) {
      const el = document.getElementById(`st-p-${key}`);
      if (el) profile[key] = el.value.trim();
    }
    const answers = {};
    document.querySelectorAll("#st-screeners .st-screener-row").forEach(row => {
      const key = row.dataset.key;
      const val = row.querySelector(".st-screener-val").value.trim();
      if (key) answers[key] = val;
    });
    profile.screener_answers = answers;
    return profile;
  }

  async function saveProfile() {
    try {
      await API.post("/api/settings/profile", collectProfile());
      toast("Profile saved.", "success");
      await refresh();
    } catch (e) { toast(e.message, "error"); }
  }

  async function saveApiKey() {
    const el = document.getElementById("st-apikey");
    const key = el.value.trim();
    if (!key) { toast("Enter a key first.", "error"); return; }
    try {
      await API.post("/api/settings/apikey", { key });
      el.value = "";
      toast("API key saved — LLM tailoring is now on.", "success");
      refreshHealth();
      await refresh();
    } catch (e) { toast(e.message, "error"); }
  }

  async function testAndAddDream() {
    const name = document.getElementById("st-dream-name").value.trim();
    const url = document.getElementById("st-dream-url").value.trim();
    if (!name || !url) { toast("Enter a company name and a careers URL.", "error"); return; }
    if (((data.config || {}).dream_companies || []).some(c => (c.name || "").toLowerCase() === name.toLowerCase())) {
      toast("That company is already on the list.", "error"); return;
    }
    const btn = document.getElementById("st-dream-test");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span>Testing…`;
    document.getElementById("st-dream-result").innerHTML =
      `<p class="st-hint">Probing ${escapeHtml(url)} — this can take a few seconds…</p>`;
    try {
      const r = await API.post("/api/jobs/dream/resolve", { name, url });
      const titles = (r.sample_titles || []).map(t => `<li>${escapeHtml(t)}</li>`).join("");
      dreamResultHtml = `<p class="st-status"><span class="st-on">✓</span> ${escapeHtml(name)}: detected
        <b>${escapeHtml(r.ats)}</b>${r.slug ? ` (slug <code>${escapeHtml(r.slug)}</code>)` : ""}
        — ${r.postings_found} posting${r.postings_found === 1 ? "" : "s"} found.</p>
        ${titles ? `<ul class="st-dream-titles">${titles}</ul>` : ""}`;
      // Show the result now — saveConfig re-renders only on success.
      document.getElementById("st-dream-result").innerHTML = dreamResultHtml;
      await saveConfig(cfg => {
        cfg.dream_companies = cfg.dream_companies || [];
        const entry = { name, url, ats: r.ats, postings_found: r.postings_found };
        if (r.slug) entry.slug = r.slug;
        cfg.dream_companies.push(entry);
      }); // saveConfig re-renders; dreamResultHtml keeps the result visible
    } catch (e) {
      dreamResultHtml = `<p class="st-status"><span class="st-off">✗</span> ${escapeHtml(e.message)}</p>`;
      document.getElementById("st-dream-result").innerHTML = dreamResultHtml;
      toast(e.message, "error");
    } finally {
      const b = document.getElementById("st-dream-test");
      if (b) { b.disabled = false; b.textContent = "Test & add"; }
    }
  }

  function addScreenerRow() {
    const key = document.getElementById("st-new-key").value.trim()
      .toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
    const val = document.getElementById("st-new-val").value.trim();
    if (!key) { toast("Enter a question key first.", "error"); return; }
    const wrap = document.getElementById("st-screeners");
    if (wrap.querySelector(`.st-screener-row[data-key="${key}"]`)) {
      toast("That key already exists.", "error"); return;
    }
    const row = document.createElement("div");
    row.className = "st-screener-row";
    row.dataset.key = key;
    row.innerHTML = `<span class="st-screener-key">${escapeHtml(key.replace(/_/g, " "))}</span>
      <input type="text" class="st-screener-val">
      <button class="btn st-del" data-act="del-screener" title="Remove">✕</button>`;
    row.querySelector(".st-screener-val").value = val;
    wrap.appendChild(row);
    document.getElementById("st-new-key").value = "";
    document.getElementById("st-new-val").value = "";
    toast("Added — click “Save answers” to persist.");
  }

  panel.addEventListener("click", (e) => {
    const el = e.target.closest("[data-act]");
    if (!el) return;
    const act = el.dataset.act;
    if (act === "save-search") {
      saveConfig(cfg => {
        cfg.search = cfg.search || {};
        cfg.search.keywords = parseCsv("st-keywords");
        cfg.search.domain_terms = parseCsv("st-domain-terms");
        cfg.search.locations = parseCsv("st-locations");
        cfg.search.remote_only = document.getElementById("st-remote-only").checked;
        cfg.search.min_score = Number(document.getElementById("st-min-score").value) || 0;
      });
    } else if (act === "save-watchlist") {
      saveConfig(cfg => {
        cfg.watchlist = cfg.watchlist || {};
        cfg.watchlist.greenhouse = parseCsv("st-gh-slugs");
        cfg.watchlist.lever = parseCsv("st-lever-slugs");
      });
    } else if (act === "test-dream") testAndAddDream();
    else if (act === "del-dream") {
      const idx = Number(el.dataset.idx);
      saveConfig(cfg => { (cfg.dream_companies || []).splice(idx, 1); });
    } else if (act === "save-profile") saveProfile();
    else if (act === "save-apikey") saveApiKey();
    else if (act === "add-screener") addScreenerRow();
    else if (act === "del-screener") { el.closest(".st-screener-row").remove(); }
  });

  /* ---------- styles ---------- */

  if (!document.getElementById("style-settings")) {
    const st = document.createElement("style");
    st.id = "style-settings";
    st.textContent = `
      .st-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(420px, 1fr)); gap:16px; align-items:start; }
      .st-card h3 { margin:0 0 12px; font-size:15px; }
      .st-inline { display:flex; align-items:center; gap:18px; margin-bottom:10px; }
      .st-check { display:flex; align-items:center; gap:6px; font-size:13.5px; }
      .st-check input { width:auto; }
      .st-minscore { margin-bottom:0; width:110px; }
      .st-two-col { display:grid; grid-template-columns:1fr 1fr; column-gap:14px; }
      .st-hint { color:var(--text-dim); font-size:12.5px; margin:4px 0 10px; }
      .st-hint code { background:#f0f3f7; padding:1px 5px; border-radius:4px; }
      .st-status { font-size:13.5px; margin:4px 0; }
      .st-on { color:var(--green); font-weight:700; }
      .st-off { color:var(--red); font-weight:700; }
      .st-screener-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
      .st-screener-key { min-width:185px; font-size:12.5px; color:var(--text-dim); font-weight:600; text-transform:capitalize; }
      .st-screener-new { margin:10px 0; padding-top:10px; border-top:1px dashed var(--border); }
      .st-del { padding:4px 9px; font-size:12px; color:var(--text-dim); }
      .st-materials { list-style:none; margin:0; padding:0; font-size:13px; }
      .st-materials li { display:flex; align-items:baseline; gap:8px; padding:4px 0; border-bottom:1px dashed var(--border); }
      .st-path { color:var(--text-dim); font-size:11.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; direction:rtl; flex:1; text-align:left; }
      .st-card > .btn-primary { margin-top:6px; }
      .st-dream-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:12.5px; }
      .st-dream-name { font-weight:700; min-width:90px; }
      .st-dream-url { color:var(--text-dim); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .st-dream-ats { background:#f5f3ff; color:#7c3aed; border-radius:5px; padding:1px 7px; font-size:11px; font-weight:700; text-transform:capitalize; }
      .st-dream-count { color:var(--text-dim); font-size:11.5px; white-space:nowrap; }
      .st-dream-new { display:flex; gap:8px; margin:10px 0 4px; padding-top:10px; border-top:1px dashed var(--border); }
      .st-dream-new input { flex:1; }
      .st-dream-titles { margin:4px 0 0 18px; padding:0; font-size:12px; color:var(--text-dim); }
    `;
    document.head.appendChild(st);
  }

  TabHooks["settings"] = refresh;
  refresh();
})();
