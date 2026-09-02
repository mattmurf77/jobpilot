/* review tab — Tailor & Review workspace (Agent B). Owns #tab-review.
   Left: job selector + JD + matched keywords. Right: materials workspace
   (tailor / render PDF / cover letter / save edits / approve). */
(() => {
  const PANEL = document.getElementById("tab-review");

  /* Profile keywords + target domains (from /api/settings) — used to
     chip-highlight JD matches before tailoring runs (after tailoring, the
     engine's notes are shown). A small generic set covers the first paint. */
  let KEYWORDS = ["roadmap", "prioritization", "stakeholder", "cross-functional",
    "experimentation", "discovery", "agile", "growth"];
  API.get("/api/settings").then((d) => {
    const p = (d && d.profile) || {};
    const fromProfile = [...(p.keywords || []), ...(p.target_domains || []), ...(p.target_titles || [])];
    if (fromProfile.length) KEYWORDS = Array.from(new Set(fromProfile));
  }).catch(() => {});

  const style = document.createElement("style");
  style.id = "style-review";
  style.textContent = `
    .rv-layout { display: grid; grid-template-columns: minmax(300px, 5fr) 7fr; gap: 16px; align-items: start; }
    @media (max-width: 900px) { .rv-layout { grid-template-columns: 1fr; } }
    .rv-jd-text { white-space: pre-wrap; max-height: 480px; overflow-y: auto; font-size: 13px;
      color: var(--text); margin-top: 8px; border-top: 1px solid var(--border); padding-top: 8px; }
    .rv-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
    .rv-chip { background: #e8efff; color: var(--accent-dark); border-radius: 999px;
      padding: 1px 9px; font-size: 11.5px; font-weight: 600; }
    .rv-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
    .rv-frame { width: 100%; height: 540px; border: 1px solid var(--border); border-radius: 8px;
      background: #fff; }
    .rv-meta { font-size: 12px; color: var(--text-dim); margin-top: 6px; }
    .rv-downloads a { margin-right: 14px; font-size: 12.5px; color: var(--accent); }
    .rv-cover-text { min-height: 200px; font-family: ui-monospace, Menlo, monospace; font-size: 12.5px; }
    .rv-html-edit { min-height: 220px; font-family: ui-monospace, Menlo, monospace; font-size: 11.5px;
      margin-top: 8px; }
    .rv-section-title { font-size: 13px; font-weight: 700; margin: 0 0 8px 0; display: flex;
      justify-content: space-between; align-items: center; gap: 8px; }
    #tab-review .btn:not(.btn-primary):not(.btn-success) .spinner {
      border-color: #2563eb55; border-top-color: var(--accent); }
    .rv-stack > .card { margin-bottom: 14px; }
    .rv-eval-summary { font-size: 13px; margin-bottom: 10px; }
    .rv-dims { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
    .rv-dim { display: grid; grid-template-columns: 130px 1fr 34px; gap: 4px 10px; align-items: center;
      font-size: 12.5px; }
    .rv-dim-label { font-weight: 600; color: var(--text-dim); }
    .rv-dim-bar { height: 8px; background: #e8ebf0; border-radius: 999px; overflow: hidden; }
    .rv-dim-fill { display: block; height: 100%; background: var(--accent); border-radius: 999px; }
    .rv-dim-score { font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }
    .rv-dim-notes { grid-column: 2 / 4; color: var(--text-dim); font-size: 12px; }
    .rv-eval-loc { display: flex; align-items: center; gap: 8px; font-size: 12.5px; margin-bottom: 12px;
      flex-wrap: wrap; }
    .rv-eval-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    @media (max-width: 700px) { .rv-eval-cols { grid-template-columns: 1fr; } }
    .rv-eval-head { font-weight: 700; font-size: 12.5px; color: var(--text-dim); margin-bottom: 4px; }
    .rv-gap-head { color: var(--amber); }
    .rv-eval-list { margin: 0; padding-left: 18px; font-size: 12.5px; }
    .rv-eval-list li { padding: 1px 0; }
    .rv-gaps li { color: var(--amber); }
    .rv-findings { display: flex; flex-direction: column; gap: 6px; margin: 10px 0; }
    .rv-finding { display: flex; align-items: baseline; gap: 8px; font-size: 12.5px; }
    .rv-finding-cat { font-weight: 600; color: var(--text-dim); white-space: nowrap; }
    .rv-finding-msg { flex: 1; }
  `;
  document.head.appendChild(style);

  PANEL.innerHTML = `
    <div class="rv-layout">
      <div class="rv-stack">
        <div class="card">
          <label class="field">Job
            <select id="rv-job-select"></select>
          </label>
          <div id="rv-job-info"></div>
          <div class="rv-chips" id="rv-keywords"></div>
          <div class="rv-jd-text" id="rv-jd"></div>
        </div>
      </div>
      <div class="rv-stack">
        <div class="card">
          <div class="rv-actions">
            <button class="btn" id="rv-btn-evaluate">🧭 Evaluate fit</button>
            <button class="btn btn-primary" id="rv-btn-tailor">✨ Tailor resume</button>
            <span id="rv-mode-badge"></span>
            <button class="btn" id="rv-btn-render">📄 Render PDF</button>
            <span id="rv-pages-badge"></span>
            <span id="rv-ats-badge"></span>
            <button class="btn" id="rv-btn-critique">🔍 Review draft</button>
            <button class="btn" id="rv-btn-cover">✉️ Generate cover letter</button>
            <button class="btn" id="rv-btn-save">💾 Save edits</button>
            <button class="btn btn-success" id="rv-btn-approve">✅ Approve for submission</button>
          </div>
          <div class="rv-meta" id="rv-notes"></div>
        </div>
        <div class="card">
          <div class="rv-section-title">💬 Feedback for re-tailoring</div>
          <textarea id="rv-feedback" rows="3" spellcheck="true"
            placeholder='What should change? e.g. "remove §17.4", "include §3.2", "subtitle 7", or freeform guidance like "lead with the PPP impact, less process talk"'></textarea>
          <div class="rv-meta">Directives (<code>include/remove §id</code> — ids shown under the resume — and <code>subtitle N</code>) apply in any mode. Freeform comments fully steer LLM-mode tailoring. Feedback persists for this job until you clear the box; click ✨ Tailor resume to apply.</div>
        </div>
        <div class="card" id="rv-eval-card" style="display:none"></div>
        <div class="card" id="rv-findings-card" style="display:none"></div>
        <div class="card">
          <div class="rv-section-title">Tailored resume
            <button class="btn" id="rv-edit-toggle" style="padding:3px 10px;font-size:12px;">✏️ Edit HTML</button>
          </div>
          <div id="rv-resume-area"><div class="empty-state">No tailored resume yet — pick a job and click ✨ Tailor resume.</div></div>
          <textarea id="rv-html-edit" class="rv-html-edit" style="display:none" spellcheck="false"
            placeholder="Resume HTML (saved as a new version)"></textarea>
          <div class="rv-meta" id="rv-provenance"></div>
          <div class="rv-meta rv-downloads" id="rv-downloads"></div>
        </div>
        <div class="card">
          <div class="rv-section-title">Cover letter (markdown — editable)</div>
          <textarea id="rv-cover-text" class="rv-cover-text" spellcheck="true"
            placeholder="No cover letter yet — click ✉️ Generate cover letter."></textarea>
          <div class="rv-meta" id="rv-cover-meta"></div>
        </div>
      </div>
    </div>`;

  const el = (id) => document.getElementById(id);
  const sel = el("rv-job-select");
  let jobs = [];
  let currentJobId = null;
  let loadedCover = "";
  const atsBadges = {}; // jobId(str) -> badge HTML, persists until next render for that job

  function setBusy(btn, on, busyLabel) {
    if (on) {
      btn.dataset.label = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span>${busyLabel || "Working…"}`;
    } else {
      btn.disabled = false;
      if (btn.dataset.label) btn.innerHTML = btn.dataset.label;
    }
  }

  function currentJob() {
    return jobs.find((j) => String(j.id) === String(currentJobId)) || null;
  }

  function renderJobPane() {
    const job = currentJob();
    if (!job) {
      el("rv-job-info").innerHTML = "";
      el("rv-jd").textContent = "";
      el("rv-keywords").innerHTML = "";
      return;
    }
    el("rv-job-info").innerHTML = `
      <div style="font-weight:700">${escapeHtml(job.title)}</div>
      <div style="color:var(--text-dim);font-size:12.5px">${escapeHtml(job.company || "")}
        ${job.location ? " · " + escapeHtml(job.location) : ""}
        ${job.salary ? " · " + escapeHtml(job.salary) : ""}</div>
      <div style="margin-top:4px">${statusBadge(job.status)}</div>`;
    const jd = (job.description || "").trim();
    el("rv-jd").textContent = jd || "(no job description text)";
    const lower = jd.toLowerCase();
    const hits = KEYWORDS.filter((k) => lower.includes(k.toLowerCase()));
    el("rv-keywords").innerHTML = hits.length
      ? `<span style="font-size:11px;color:var(--text-dim);align-self:center">Matched:</span>` +
        hits.map((k) => `<span class="rv-chip">${escapeHtml(k)}</span>`).join("")
      : "";
  }

  function modeBadge(mode) {
    if (!mode) return "";
    const llm = mode === "llm";
    const color = llm ? "#7c3aed" : "#6b7280";
    return `<span class="badge" style="background:${color}1a;color:${color};border:1px solid ${color}55">${llm ? "LLM" : "Basic"}</span>`;
  }

  /* ---------- evaluation panel (🧭 Evaluate fit) ---------- */

  function tintBadge(label, color) {
    return `<span class="badge" style="background:${color}1a;color:${color};border:1px solid ${color}55">${escapeHtml(label)}</span>`;
  }

  const REC_COLORS = { strong: "#16a34a", moderate: "#d97706", weak: "#dc2626" };
  const VERDICT_COLORS = { PASS: "#16a34a", FLAG: "#d97706", FAIL: "#dc2626" };

  function renderEvaluation(ev) {
    const card = el("rv-eval-card");
    if (!ev) { card.style.display = "none"; card.innerHTML = ""; return; }
    const rec = String(ev.recommendation || "");
    const recLabel = rec ? rec.charAt(0).toUpperCase() + rec.slice(1) + " fit" : "No recommendation";
    const dims = Object.entries(ev.dimensions || {}).map(([key, d]) => {
      d = d || {};
      const score = Math.max(0, Math.min(100, Number(d.score) || 0));
      return `<div class="rv-dim">
        <span class="rv-dim-label">${escapeHtml(d.label || key)}</span>
        <span class="rv-dim-bar"><span class="rv-dim-fill" style="width:${score}%"></span></span>
        <span class="rv-dim-score">${score}</span>
        ${d.notes ? `<span class="rv-dim-notes">${escapeHtml(d.notes)}</span>` : ""}
      </div>`;
    }).join("");
    const loc = ev.location;
    const locRow = loc ? `<div class="rv-eval-loc">
        <span class="rv-dim-label">Location</span>
        ${tintBadge(loc.verdict || "?", VERDICT_COLORS[loc.verdict] || "#6b7280")}
        <span class="rv-dim-notes" style="grid-column:auto">${escapeHtml(loc.notes || "")}</span>
      </div>` : "";
    const list = (arr, cls) => (Array.isArray(arr) && arr.length)
      ? `<ul class="rv-eval-list ${cls}">${arr.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>`
      : '<div class="rv-meta">None noted.</div>';
    card.innerHTML = `
      <div class="rv-section-title">🧭 Fit evaluation
        <span>${tintBadge(recLabel, REC_COLORS[rec] || "#6b7280")} ${modeBadge(ev.mode)}</span>
      </div>
      ${ev.summary ? `<div class="rv-eval-summary">${escapeHtml(ev.summary)}</div>` : ""}
      <div class="rv-dims">${dims}</div>
      ${locRow}
      <div class="rv-eval-cols">
        <div><div class="rv-eval-head">Strengths</div>${list(ev.strengths, "rv-good")}</div>
        <div><div class="rv-eval-head rv-gap-head">Honest gaps</div>${list(ev.gaps, "rv-gaps")}</div>
      </div>`;
    card.style.display = "";
  }

  /* ---------- findings panel (🔍 Review draft) ---------- */

  const SEV_META = {
    high:   { label: "High",   color: "#dc2626" },
    medium: { label: "Medium", color: "#d97706" },
    info:   { label: "Info",   color: "#2563eb" },
  };

  function renderFindings(res) {
    const card = el("rv-findings-card");
    if (!res) { card.style.display = "none"; card.innerHTML = ""; return; }
    const counts = res.counts || {};
    const countsLine = ["high", "medium", "info"]
      .map((k) => `${Number(counts[k]) || 0} ${k}`).join(" · ");
    const findings = Array.isArray(res.findings) ? res.findings : [];
    const known = ["high", "medium", "info"];
    const ordered = known.flatMap((sev) => findings.filter((f) => f && f.severity === sev))
      .concat(findings.filter((f) => f && !known.includes(f.severity)));
    const rows = ordered.map((f) => {
      const m = SEV_META[f.severity] || { label: f.severity || "?", color: "#6b7280" };
      return `<div class="rv-finding">
        ${tintBadge(m.label, m.color)}
        ${f.category ? `<span class="rv-finding-cat">${escapeHtml(f.category)}</span>` : ""}
        <span class="rv-finding-msg">${escapeHtml(f.message || "")}</span>
      </div>`;
    }).join("");
    card.innerHTML = `
      <div class="rv-section-title">🔍 Draft review</div>
      <div class="rv-meta">${escapeHtml(countsLine)}</div>
      <div class="rv-findings">${rows || '<div class="rv-meta">No issues found — draft looks clean.</div>'}</div>
      <div class="rv-meta">Fix via the feedback box (<code>include/remove §id</code>) or ✏️ Edit HTML, then re-run.</div>`;
    card.style.display = "";
  }

  /* ---------- ATS badge (from render response) ---------- */

  function renderAtsBadge(jobId, ats) {
    let html = "";
    if (ats) {
      const contact = ats.contact || {};
      const ok = !!(ats.ok && contact.name && contact.email);
      const kw = ats.keywords_found != null && ats.keywords_total != null
        ? ` ${ats.keywords_found}/${ats.keywords_total} keywords` : "";
      if (ok) {
        html = `<span class="badge" style="background:#16a34a1a;color:#16a34a;border:1px solid #16a34a55"
          title="ATS checks passed${escapeHtml(kw ? " —" + kw + " matched" : "")}">ATS ✓${escapeHtml(kw)}</span>`;
      } else {
        const missing = [];
        if (!contact.name) missing.push("contact name");
        if (!contact.email) missing.push("contact email");
        if (!contact.phone) missing.push("contact phone");
        (Array.isArray(ats.missing) ? ats.missing : []).forEach((m) => missing.push("keyword: " + m));
        html = `<span class="badge" style="background:#d977061a;color:#d97706;border:1px solid #d9770655"
          title="${escapeHtml("Missing: " + (missing.join(", ") || "details unavailable"))}">ATS ⚠${escapeHtml(kw)}</span>`;
      }
    }
    atsBadges[String(jobId)] = html;
    if (String(jobId) === String(currentJobId)) el("rv-ats-badge").innerHTML = html;
  }

  let findingsJobId = null; // job the findings panel currently shows

  async function refreshEvaluation() {
    if (String(findingsJobId) !== String(currentJobId)) renderFindings(null); // critique is per-run; clear on job switch
    if (!currentJobId) { renderEvaluation(null); return; }
    try {
      renderEvaluation(await API.get(`/api/review/${currentJobId}/evaluate`)); // restore stored evaluation
    } catch (e) {
      renderEvaluation(null); // 404 = never evaluated
    }
  }

  function renderMaterials(mats) {
    const docs = (mats && mats.documents) || {};
    const resume = docs.resume_html;
    const coverMd = docs.cover_letter_md;
    const resumePdf = docs.resume_pdf;
    const coverPdf = docs.cover_letter_pdf;

    // resume preview
    if (resume) {
      el("rv-resume-area").innerHTML =
        `<iframe class="rv-frame" id="rv-resume-frame" src="/api/documents/file/${resume.doc_id}"></iframe>`;
      el("rv-html-edit").value = resume.content || "";
      el("rv-mode-badge").innerHTML = modeBadge(resume.meta && resume.meta.mode);
      const notes = (resume.meta && resume.meta.notes) || "";
      el("rv-notes").textContent = notes;
      const structure = resume.meta && resume.meta.structure;
      if (structure) {
        const refs = []
          .concat(((structure.roles || [])[0] || {}).bullets || [], structure.earlier_impact || [])
          .map((b) => b.source_ref)
          .filter((r) => r && r !== "baseline");
        el("rv-provenance").textContent = refs.length
          ? "Provenance: bullets from line menu " + refs.join(", ")
          : "";
      } else {
        el("rv-provenance").textContent = resume.meta && resume.meta.edited ? "User-edited HTML version." : "";
      }
    } else {
      el("rv-resume-area").innerHTML =
        '<div class="empty-state">No tailored resume yet — click ✨ Tailor resume.</div>';
      el("rv-html-edit").value = "";
      el("rv-mode-badge").innerHTML = "";
      el("rv-notes").textContent = "";
      el("rv-provenance").textContent = "";
    }

    // pages badge + downloads
    const pages = resumePdf && resumePdf.meta ? resumePdf.meta.pages : null;
    el("rv-pages-badge").innerHTML = resumePdf
      ? `<span class="badge" style="background:#0d94881a;color:#0d9488;border:1px solid #0d948855">${pages != null ? pages + " page" + (pages === 1 ? "" : "s") : "PDF ready"}</span>`
      : "";
    const links = [];
    if (resumePdf)
      links.push(`<a href="/api/documents/file/${resumePdf.doc_id}" target="_blank" download>⬇ Resume PDF${resumePdf.meta && resumePdf.meta.filename ? " (" + escapeHtml(resumePdf.meta.filename) + ")" : ""}</a>`);
    if (coverPdf)
      links.push(`<a href="/api/documents/file/${coverPdf.doc_id}" target="_blank" download>⬇ Cover letter PDF</a>`);
    el("rv-downloads").innerHTML = links.join("");

    // cover letter
    if (coverMd) {
      el("rv-cover-text").value = coverMd.content || "";
      loadedCover = coverMd.content || "";
      const m = coverMd.meta || {};
      el("rv-cover-meta").innerHTML =
        modeBadge(m.mode) +
        (m.needs_editing ? ' <span style="color:var(--amber)">Template draft — personalize before sending.</span>' : "") +
        (m.edited ? " (edited)" : "");
    } else {
      el("rv-cover-text").value = "";
      loadedCover = "";
      el("rv-cover-meta").innerHTML = "";
    }
  }

  async function refreshMaterials() {
    el("rv-ats-badge").innerHTML = currentJobId ? atsBadges[String(currentJobId)] || "" : "";
    if (!currentJobId) {
      renderMaterials(null);
      el("rv-feedback").value = "";
      renderEvaluation(null);
      renderFindings(null);
      return;
    }
    try {
      const mats = await API.get(`/api/tailor/${currentJobId}/materials`);
      renderMaterials(mats);
      el("rv-feedback").value = mats.feedback || "";
    } catch (e) {
      renderMaterials(null);
      el("rv-feedback").value = "";
    }
    await refreshEvaluation();
  }

  async function loadJobs() {
    const ctx = consumeTabContext();
    try {
      jobs = await API.get("/api/jobs/?status=interested,tailoring,tailored,ready");
    } catch (e) {
      jobs = [];
    }
    if (!jobs.length) {
      sel.innerHTML = '<option value="">No jobs marked Interested yet — use the Find tab</option>';
      currentJobId = null;
      renderJobPane();
      renderMaterials(null);
      return;
    }
    const wanted = ctx && ctx.jobId != null ? String(ctx.jobId) : currentJobId != null ? String(currentJobId) : null;
    sel.innerHTML = jobs
      .map((j) => `<option value="${j.id}">${escapeHtml(j.company || "?")} — ${escapeHtml(j.title)} (${escapeHtml(j.status)})</option>`)
      .join("");
    const match = wanted && jobs.some((j) => String(j.id) === wanted) ? wanted : String(jobs[0].id);
    sel.value = match;
    currentJobId = match;
    renderJobPane();
    await refreshMaterials();
  }

  sel.addEventListener("change", async () => {
    currentJobId = sel.value || null;
    renderJobPane();
    await refreshMaterials();
  });

  el("rv-edit-toggle").addEventListener("click", () => {
    const ta = el("rv-html-edit");
    ta.style.display = ta.style.display === "none" ? "block" : "none";
  });

  function requireJob() {
    if (!currentJobId) {
      toast("Pick a job first (mark one Interested on the Find tab).", "error");
      return false;
    }
    return true;
  }

  el("rv-btn-evaluate").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-evaluate");
    setBusy(btn, true, "Evaluating…");
    try {
      const ev = await API.post(`/api/review/${currentJobId}/evaluate`);
      renderEvaluation(ev);
      toast("Fit evaluation complete.", "success");
    } catch (e) {
      toast(`Evaluate failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-critique").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-critique");
    setBusy(btn, true, "Reviewing…");
    try {
      // raw fetch (not API.post) so a 400 (no tailored resume yet) is distinguishable
      const r = await fetch(`/api/review/${currentJobId}/critique`, {
        method: "POST", headers: { "Content-Type": "application/json" },
      });
      if (r.status === 400) { toast("Tailor a resume first.", "error"); return; }
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
      findingsJobId = currentJobId;
      renderFindings(await r.json());
    } catch (e) {
      toast(`Review failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-tailor").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-tailor");
    setBusy(btn, true, "Tailoring… (~30s in LLM mode)");
    try {
      const feedback = el("rv-feedback").value.trim();
      const r = await API.post(`/api/tailor/${currentJobId}`, { feedback });
      toast(`Tailored in ${r.mode === "llm" ? "LLM" : "basic"} mode${feedback ? " with your feedback" : ""}.`, "success");
      await loadJobs(); // status changed -> refresh dropdown labels + materials
    } catch (e) {
      toast(`Tailoring failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-render").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-render");
    setBusy(btn, true, "Rendering…");
    try {
      const r = await API.post(`/api/tailor/${currentJobId}/render`);
      const trimmed = r.trimmed && r.trimmed.length ? ` (trimmed ${r.trimmed.length} bullet${r.trimmed.length > 1 ? "s" : ""} to fit)` : "";
      toast(`PDF rendered: ${r.pages != null ? r.pages + " page(s)" : "done"}${trimmed}`, "success");
      renderAtsBadge(currentJobId, r.ats);
      await refreshMaterials();
    } catch (e) {
      toast(`PDF render failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-cover").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-cover");
    setBusy(btn, true, "Writing…");
    try {
      const r = await API.post(`/api/tailor/${currentJobId}/cover-letter`);
      toast(`Cover letter generated (${r.mode === "llm" ? "LLM" : "basic template"} mode).`, "success");
      await refreshMaterials();
      // also render its PDF so the download link is ready
      try {
        await API.post(`/api/tailor/${currentJobId}/cover-letter/render`);
        await refreshMaterials();
      } catch (e) { /* PDF is optional here; markdown is saved */ }
    } catch (e) {
      toast(`Cover letter failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-save").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-save");
    setBusy(btn, true, "Saving…");
    let saved = 0;
    try {
      const cover = el("rv-cover-text").value;
      if (cover.trim() && cover !== loadedCover) {
        await API.post(`/api/tailor/${currentJobId}/save`, { kind: "cover_letter_md", content: cover });
        saved++;
      }
      const htmlTa = el("rv-html-edit");
      if (htmlTa.style.display !== "none" && htmlTa.value.trim()) {
        await API.post(`/api/tailor/${currentJobId}/save`, { kind: "resume_html", content: htmlTa.value });
        saved++;
      }
      toast(saved ? `Saved ${saved} edit${saved > 1 ? "s" : ""} as new version${saved > 1 ? "s" : ""}.` : "No changes to save.", saved ? "success" : "info");
      if (saved) await refreshMaterials();
    } catch (e) {
      toast(`Save failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  el("rv-btn-approve").addEventListener("click", async () => {
    if (!requireJob()) return;
    const btn = el("rv-btn-approve");
    setBusy(btn, true, "Approving…");
    try {
      await API.post(`/api/tailor/${currentJobId}/approve`);
      toast("Materials approved — job is Ready. Off to the Pipeline tab to submit.", "success");
      const jobId = Number(currentJobId);
      switchToTab("pipeline", { jobId });
    } catch (e) {
      toast(`Approve failed: ${e.message}`, "error");
    } finally {
      setBusy(btn, false);
    }
  });

  TabHooks["review"] = loadJobs;
  loadJobs();
})();
