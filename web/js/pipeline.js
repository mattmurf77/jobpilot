/* Pipeline tab — grouped board of jobs by lifecycle stage + submission flow. Agent C. */
(function () {
  const panel = document.getElementById("tab-pipeline");

  const SECTIONS = [
    { key: "interested", label: "Interested",         statuses: ["interested"] },
    { key: "tailored",   label: "Tailored",           statuses: ["tailoring", "tailored"] },
    { key: "ready",      label: "Ready",              statuses: ["ready"] },
    { key: "submitting", label: "Submitting",         statuses: ["submitting"] },
    { key: "submitted",  label: "Submitted",          statuses: ["submitted"] },
    { key: "interview",  label: "Interview",          statuses: ["interview"] },
    { key: "rejected",   label: "Rejected",           statuses: ["rejected"] },
    { key: "parked",     label: "Skipped / Archived", statuses: ["skipped", "archived"], collapsed: true },
  ];
  const ALL_STATUSES = SECTIONS.flatMap(s => s.statuses);
  const DOC_CHIP_LABELS = {
    resume_pdf: "Resume PDF", resume_html: "Resume HTML",
    cover_letter_pdf: "Cover letter PDF", cover_letter_md: "Cover letter",
    form_screenshot: "Form screenshot",
    interview_prep_md: "Interview prep", posting_txt: "Posting snapshot",
  };

  const state = {
    jobs: [],
    docs: {},                 // job_id(str) -> [documents] newest first
    events: [],               // global event list
    expanded: new Set(),      // job ids with detail open
    collapsedSections: new Set(SECTIONS.filter(s => s.collapsed).map(s => s.key)),
    panels: {},               // job_id -> {mode: "auto"|"assist", data}
    busy: new Set(),          // job ids with an in-flight request
    insights: null,           // GET /api/review/insights payload (null -> card hidden)
    insightsOpen: false,      // collapsed by default
  };

  async function refresh() {
    try {
      const [jobs, docs, events, insights] = await Promise.all([
        API.get("/api/jobs/?status=" + ALL_STATUSES.join(",")).catch(() => []),
        API.get("/api/submit/documents").catch(() => ({})),
        API.get("/api/events").catch(() => []),
        API.get("/api/review/insights").catch(() => null),
      ]);
      state.jobs = Array.isArray(jobs) ? jobs : (jobs.jobs || []);
      state.docs = docs || {};
      state.events = Array.isArray(events) ? events : [];
      state.insights = insights;
      render();
    } catch (e) {
      panel.innerHTML = `<div class="empty-state">Failed to load pipeline: ${escapeHtml(e.message)}</div>`;
    }
  }

  /* ---------- rendering ---------- */

  function render() {
    const sections = SECTIONS.map(sec => {
      const jobs = state.jobs.filter(j => sec.statuses.includes(j.status));
      const collapsed = state.collapsedSections.has(sec.key);
      return `<div class="pl-section">
        <button class="pl-section-head" data-act="toggle-section" data-sec="${sec.key}">
          <span class="pl-caret">${collapsed ? "▸" : "▾"}</span>
          <span class="pl-section-title">${escapeHtml(sec.label)}</span>
          <span class="pl-count">${jobs.length}</span>
        </button>
        ${collapsed ? "" : `<div class="pl-rows">${
          jobs.length ? jobs.map(rowHtml).join("") : `<div class="pl-empty">Nothing here yet.</div>`
        }</div>`}
      </div>`;
    }).join("");
    panel.innerHTML = `<div class="pl-board">
      <div class="pl-toolbar">
        <h2 class="pl-h2">Pipeline</h2>
        <button class="btn" data-act="refresh">↻ Refresh</button>
      </div>
      ${insightsHtml()}
      ${sections}
    </div>`;
  }

  function insightsHtml() {
    const ins = state.insights;
    if (!ins) return "";
    const open = state.insightsOpen;
    let body = "";
    if (open) {
      const cell = (v) => escapeHtml(v == null ? "–" : String(v));
      const bands = Array.isArray(ins.bands) ? ins.bands : [];
      const rows = bands.map(b => `<tr><td>${cell(b.band)}</td><td>${cell(b.active)}</td>
        <td>${cell(b.submitted)}</td><td>${cell(b.interview)}</td><td>${cell(b.rejected)}</td></tr>`).join("");
      const table = rows
        ? `<table class="pl-ins-table"><thead><tr><th>Score band</th><th>Active</th><th>Submitted</th>
            <th>Interview</th><th>Rejected</th></tr></thead><tbody>${rows}</tbody></table>`
        : `<div class="pl-empty">No funnel data yet.</div>`;
      const grp = (g) => g ? `${g.active ?? 0} active · ${g.submitted ?? 0} submitted · ${g.interview ?? 0} interview` : "–";
      const dream = ins.dream || {};
      const dreamLine = (dream.dream || dream.other)
        ? `<div class="pl-ins-line"><strong>Dream companies:</strong> ${escapeHtml(grp(dream.dream))}
           &nbsp;·&nbsp; <strong>Others:</strong> ${escapeHtml(grp(dream.other))}</div>`
        : "";
      const rate = Number(ins.interview_rate);
      const rateLine = ins.interview_rate != null && !Number.isNaN(rate)
        ? `<div class="pl-ins-line"><strong>Interview rate:</strong> ${escapeHtml((rate <= 1 ? rate * 100 : rate).toFixed(1))}%</div>`
        : "";
      body = `<div class="pl-ins-body">${table}${dreamLine}${rateLine}</div>`;
    }
    return `<div class="pl-section pl-insights card">
      <button class="pl-section-head" data-act="toggle-insights">
        <span class="pl-caret">${open ? "▾" : "▸"}</span>
        <span class="pl-section-title">📊 Insights</span>
      </button>
      ${body}
    </div>`;
  }

  function rowHtml(job) {
    const busy = state.busy.has(job.id);
    const expanded = state.expanded.has(job.id);
    const updated = String(job.updated_at || "").slice(0, 10);
    const sub = state.panels[job.id];
    return `<div class="pl-row card" data-jobrow="${job.id}">
      <div class="pl-row-main">
        <button class="pl-expand" data-act="toggle-job" data-job="${job.id}" title="Details">${expanded ? "▾" : "▸"}</button>
        <div class="pl-title">
          <span class="pl-company">${escapeHtml(job.company || "—")}</span>
          <span class="pl-dash">—</span>
          <span class="pl-jobtitle">${escapeHtml(job.title || "")}</span>
        </div>
        ${statusBadge(job.status)}
        <span class="pl-updated" title="Last updated">${escapeHtml(updated)}</span>
        <span class="pl-spacer"></span>
        ${actionButtons(job, busy)}
        <select data-act="set-status" data-job="${job.id}" class="pl-status-select" title="Set status manually">
          ${Object.keys(STATUS_META).map(s =>
            `<option value="${s}" ${s === job.status ? "selected" : ""}>${escapeHtml(STATUS_META[s].label)}</option>`).join("")}
        </select>
      </div>
      ${docChipsHtml(job)}
      ${sub ? (sub.mode === "auto" ? autoPanelHtml(job, sub.data) : assistPanelHtml(job, sub.data)) : ""}
      ${expanded ? detailHtml(job) : ""}
    </div>`;
  }

  function actionButtons(job, busy) {
    if (busy) return `<button class="btn btn-primary" disabled><span class="spinner"></span>Working…</button>`;
    if (job.status === "ready" && !state.panels[job.id]) {
      return `<button class="btn btn-primary" data-act="prepare" data-job="${job.id}">🚀 Auto-fill application</button>`;
    }
    if (job.status === "submitting" && !state.panels[job.id]) {
      return `<button class="btn btn-success" data-act="confirm" data-job="${job.id}">Confirm submit</button>
              <button class="btn" data-act="cancel" data-job="${job.id}">Cancel</button>`;
    }
    if (job.status === "submitted" || job.status === "interview") {
      return `<button class="btn" data-act="interview-prep" data-job="${job.id}">🎤 Interview prep</button>`;
    }
    return "";
  }

  function docChipsHtml(job) {
    const docs = state.docs[String(job.id)] || [];
    const seen = new Set();
    const chips = [];
    for (const d of docs) {
      if (seen.has(d.kind)) continue;
      seen.add(d.kind);
      chips.push(`<a class="pl-chip" href="/api/documents/file/${d.id}" target="_blank" rel="noopener">📎 ${escapeHtml(DOC_CHIP_LABELS[d.kind] || d.kind)}</a>`);
    }
    return chips.length ? `<div class="pl-chips">${chips.join("")}</div>` : "";
  }

  function detailHtml(job) {
    const events = state.events.filter(ev => ev.job_id === job.id);
    const timeline = events.length
      ? events.map(ev => `<li><span class="pl-ev-when">${escapeHtml(String(ev.created_at || "").replace("T", " ").slice(0, 16))}</span>
          <span class="pl-ev-type">${escapeHtml(ev.type)}</span>
          <span class="pl-ev-detail">${escapeHtml(ev.detail || "")}</span></li>`).join("")
      : "<li class='pl-ev-detail'>No events recorded yet.</li>";
    return `<div class="pl-detail">
      <div class="pl-detail-col">
        <label class="field">Notes
          <textarea rows="3" id="pl-notes-${job.id}" placeholder="Notes for this application…">${escapeHtml(job.notes || "")}</textarea>
        </label>
        <button class="btn" data-act="save-notes" data-job="${job.id}">Save notes</button>
      </div>
      <div class="pl-detail-col">
        <div class="pl-detail-head">Timeline</div>
        <ul class="pl-timeline">${timeline}</ul>
        ${job.url ? `<a href="${escapeHtml(job.url)}" target="_blank" rel="noopener">View job posting ↗</a>` : ""}
      </div>
    </div>`;
  }

  function autoPanelHtml(job, data) {
    const r = data.report || {};
    const shot = data.screenshot_doc_id
      ? `<a href="/api/documents/file/${data.screenshot_doc_id}" target="_blank" rel="noopener">
           <img class="pl-shot" src="/api/documents/file/${data.screenshot_doc_id}" alt="Filled form screenshot"></a>`
      : "";
    const li = (arr, cls, mark) => (arr || []).map(x => `<li class="${cls}">${mark} ${escapeHtml(x)}</li>`).join("");
    const notes = (r.notes || []).map(n => `<div class="pl-warn">⚠️ ${escapeHtml(n)}</div>`).join("");
    return `<div class="pl-subpanel pl-confirmpanel">
      <div class="pl-subpanel-head">Form filled — review, then confirm. <strong>Nothing has been submitted yet.</strong></div>
      ${notes}
      <div class="pl-confirm-body">
        ${shot}
        <div class="pl-report">
          <div class="pl-detail-head">Filled</div><ul>${li(r.filled, "pl-ok", "✓") || "<li>none</li>"}</ul>
          <div class="pl-detail-head">Skipped</div><ul>${li(r.skipped, "pl-skip", "–") || "<li>none</li>"}</ul>
        </div>
      </div>
      <div class="pl-subpanel-actions">
        <button class="btn btn-success" data-act="confirm" data-job="${job.id}">Confirm submit</button>
        <button class="btn" data-act="cancel" data-job="${job.id}">Cancel</button>
        <span class="pl-hint">The browser window stays open so you can review or finish fields there. Session expires in 30 min.</span>
      </div>
    </div>`;
  }

  function assistPanelHtml(job, data) {
    const p = data.packet || {};
    const rows = (p.fields || []).map((f, i) => `<div class="pl-field-row">
        <span class="pl-field-label">${escapeHtml(f.label)}</span>
        <span class="pl-field-value">${escapeHtml(f.value)}</span>
        <button class="btn pl-copy" data-act="copy" data-job="${job.id}" data-idx="${i}">Copy</button>
      </div>`).join("");
    const docs = (p.documents || []).map(d =>
      `<a class="pl-chip" href="/api/documents/file/${d.doc_id}" target="_blank" rel="noopener">📎 ${escapeHtml(d.label)}</a>`).join("");
    return `<div class="pl-subpanel">
      <div class="pl-subpanel-head">Assisted submission${data.note ? ` <span class="pl-warn-inline">(${escapeHtml(data.note)})</span>` : ""}</div>
      <div class="pl-subpanel-actions">
        ${p.apply_url ? `<a class="btn btn-primary" href="${escapeHtml(p.apply_url)}" target="_blank" rel="noopener">Open apply page ↗</a>` : ""}
        <button class="btn btn-success" data-act="manual-confirm" data-job="${job.id}">I submitted it</button>
        <button class="btn" data-act="close-panel" data-job="${job.id}">Close</button>
      </div>
      ${docs ? `<div class="pl-chips">${docs}</div>` : ""}
      <div class="pl-fields">${rows || "<div class='pl-empty'>No profile fields found.</div>"}</div>
    </div>`;
  }

  /* ---------- actions ---------- */

  async function doPrepare(jobId) {
    state.busy.add(jobId); render();
    try {
      const res = await API.post(`/api/submit/${jobId}/prepare`);
      state.panels[jobId] = { mode: res.mode, data: res };
      if (res.mode === "auto") toast("Form filled — review and confirm. Nothing submitted yet.", "success");
      else toast(res.note || "Assist mode: copy fields into the form yourself.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      state.busy.delete(jobId);
      await refresh();
    }
  }

  async function doConfirm(jobId) {
    if (!window.confirm("Really submit this application? This clicks the final Submit button on the form.")) return;
    state.busy.add(jobId); render();
    try {
      await API.post(`/api/submit/${jobId}/confirm`);
      delete state.panels[jobId];
      toast("Application submitted 🎉", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      state.busy.delete(jobId);
      await refresh();
    }
  }

  async function doCancel(jobId) {
    state.busy.add(jobId); render();
    try {
      await API.post(`/api/submit/${jobId}/cancel`);
      delete state.panels[jobId];
      toast("Submission cancelled — nothing was sent.");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      state.busy.delete(jobId);
      await refresh();
    }
  }

  async function doInterviewPrep(jobId) {
    state.busy.add(jobId); render();
    try {
      const res = await API.post(`/api/review/${jobId}/interview-prep`);
      toast("Interview prep sheet generated.", "success");
      if (res && res.doc_id != null) window.open(`/api/documents/file/${res.doc_id}`, "_blank");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      state.busy.delete(jobId);
      await refresh(); // reloads docs -> "Interview prep" chip appears on the row
    }
  }

  async function doManualConfirm(jobId) {
    try {
      await API.post(`/api/submit/${jobId}/manual-confirm`);
      delete state.panels[jobId];
      toast("Marked as submitted (manual).", "success");
      await refresh();
    } catch (e) { toast(e.message, "error"); }
  }

  async function doSetStatus(jobId, status) {
    try {
      await API.post(`/api/jobs/${jobId}/status`, { status });
      toast(`Status → ${STATUS_META[status] ? STATUS_META[status].label : status}`);
      await refresh();
    } catch (e) { toast(e.message, "error"); await refresh(); }
  }

  async function doSaveNotes(jobId) {
    const job = state.jobs.find(j => j.id === jobId);
    const ta = document.getElementById(`pl-notes-${jobId}`);
    if (!job || !ta) return;
    try {
      await API.post(`/api/jobs/${jobId}/status`, { status: job.status, notes: ta.value });
      toast("Notes saved.", "success");
      await refresh();
    } catch (e) { toast(e.message, "error"); }
  }

  function doCopy(jobId, idx) {
    const sub = state.panels[jobId];
    const f = sub && sub.data.packet && sub.data.packet.fields[idx];
    if (!f) return;
    navigator.clipboard.writeText(f.value).then(
      () => toast(`Copied ${f.label}`),
      () => toast("Copy failed — select the text manually.", "error"),
    );
  }

  panel.addEventListener("click", (e) => {
    const el = e.target.closest("[data-act]");
    if (!el || el.tagName === "SELECT") return;
    const act = el.dataset.act;
    const jobId = el.dataset.job ? Number(el.dataset.job) : null;
    if (act === "refresh") refresh();
    else if (act === "toggle-insights") {
      state.insightsOpen = !state.insightsOpen;
      render();
    } else if (act === "toggle-section") {
      const k = el.dataset.sec;
      state.collapsedSections.has(k) ? state.collapsedSections.delete(k) : state.collapsedSections.add(k);
      render();
    } else if (act === "toggle-job") {
      state.expanded.has(jobId) ? state.expanded.delete(jobId) : state.expanded.add(jobId);
      render();
    } else if (act === "prepare") doPrepare(jobId);
    else if (act === "confirm") doConfirm(jobId);
    else if (act === "cancel") doCancel(jobId);
    else if (act === "manual-confirm") doManualConfirm(jobId);
    else if (act === "interview-prep") doInterviewPrep(jobId);
    else if (act === "close-panel") { delete state.panels[jobId]; render(); }
    else if (act === "save-notes") doSaveNotes(jobId);
    else if (act === "copy") doCopy(jobId, Number(el.dataset.idx));
  });

  panel.addEventListener("change", (e) => {
    const el = e.target.closest("select[data-act='set-status']");
    if (el) doSetStatus(Number(el.dataset.job), el.value);
  });

  /* ---------- styles ---------- */

  if (!document.getElementById("style-pipeline")) {
    const st = document.createElement("style");
    st.id = "style-pipeline";
    st.textContent = `
      .pl-toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
      .pl-h2 { margin:0; font-size:18px; }
      .pl-section { margin-bottom: 14px; }
      .pl-section-head { display:flex; align-items:center; gap:8px; width:100%; border:none; background:transparent;
        font-size:13px; font-weight:700; color:var(--text-dim); text-transform:uppercase; letter-spacing:.04em;
        padding:6px 2px; cursor:pointer; }
      .pl-count { background:#e8ebf0; border-radius:999px; padding:0 8px; font-size:11.5px; color:var(--text-dim); }
      .pl-rows { display:flex; flex-direction:column; gap:8px; }
      .pl-empty { color:var(--text-dim); font-size:13px; padding:4px 10px; }
      .pl-row { padding:10px 14px; }
      .pl-row-main { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
      .pl-expand { border:none; background:transparent; cursor:pointer; color:var(--text-dim); font-size:13px; padding:2px; }
      .pl-title { display:flex; gap:6px; align-items:baseline; min-width:0; }
      .pl-company { font-weight:700; }
      .pl-dash { color:var(--text-dim); }
      .pl-updated { color:var(--text-dim); font-size:12px; }
      .pl-spacer { flex:1; }
      .pl-status-select { width:auto; padding:5px 8px; font-size:12.5px; }
      .pl-chips { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
      .pl-chip { font-size:12px; border:1px solid var(--border); border-radius:999px; padding:2px 10px;
        text-decoration:none; color:var(--text); background:#f8fafc; }
      .pl-chip:hover { border-color: var(--accent); color: var(--accent); }
      .pl-detail { display:flex; gap:24px; margin-top:12px; padding-top:12px; border-top:1px solid var(--border); flex-wrap:wrap; }
      .pl-detail-col { flex:1; min-width:260px; }
      .pl-detail-head { font-weight:700; font-size:12.5px; color:var(--text-dim); margin-bottom:6px; }
      .pl-timeline { list-style:none; margin:0 0 8px; padding:0; font-size:12.5px; max-height:180px; overflow:auto; }
      .pl-timeline li { padding:3px 0; border-bottom:1px dashed var(--border); }
      .pl-ev-when { color:var(--text-dim); margin-right:8px; font-variant-numeric:tabular-nums; }
      .pl-ev-type { font-weight:600; margin-right:8px; }
      .pl-ev-detail { color:var(--text-dim); }
      .pl-subpanel { margin-top:12px; padding:12px; border:1px solid var(--border); border-radius:8px; background:#fafbfd; }
      .pl-subpanel-head { font-weight:600; margin-bottom:8px; }
      .pl-subpanel-actions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:10px 0 6px; }
      .pl-confirmpanel { border-color:#99e0d2; background:#f3fbf9; }
      .pl-confirm-body { display:flex; gap:16px; flex-wrap:wrap; }
      .pl-shot { max-width:380px; max-height:300px; object-fit:contain; object-position:top;
        border:1px solid var(--border); border-radius:6px; background:#fff; }
      .pl-report ul { margin:0 0 10px; padding-left:16px; font-size:12.5px; }
      .pl-ok { color:var(--green); }
      .pl-skip { color:var(--text-dim); }
      .pl-warn { color:var(--amber); font-weight:600; margin-bottom:8px; }
      .pl-warn-inline { color:var(--amber); font-weight:500; font-size:12.5px; }
      .pl-hint { color:var(--text-dim); font-size:12px; }
      .pl-fields { margin-top:8px; display:flex; flex-direction:column; gap:4px; }
      .pl-field-row { display:flex; align-items:center; gap:10px; padding:5px 8px; background:#fff;
        border:1px solid var(--border); border-radius:6px; font-size:13px; }
      .pl-field-label { font-weight:600; min-width:200px; color:var(--text-dim); }
      .pl-field-value { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .pl-copy { padding:3px 10px; font-size:12px; }
      .pl-insights { padding:6px 14px 10px; }
      .pl-insights .pl-section-head { padding:6px 0; }
      .pl-ins-body { padding:2px 0 4px; }
      .pl-ins-table { border-collapse:collapse; font-size:12.5px; margin-bottom:8px; }
      .pl-ins-table th, .pl-ins-table td { padding:4px 18px 4px 0; text-align:left;
        border-bottom:1px solid var(--border); }
      .pl-ins-table th { color:var(--text-dim); font-weight:600; font-size:11px;
        text-transform:uppercase; letter-spacing:.04em; }
      .pl-ins-table td { font-variant-numeric:tabular-nums; }
      .pl-ins-line { font-size:12.5px; margin-top:4px; }
    `;
    document.head.appendChild(st);
  }

  TabHooks["pipeline"] = refresh;
  refresh();
})();
