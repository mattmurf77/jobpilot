# Resume Line Menu — YOUR NAME (v1)

> **What this file is.** Your complete inventory of resume content: every bullet you could ever put on a resume, plus summary and subtitle variants, a skills library, and a translation table for company-internal terms. JobPilot's tailoring engine selects and reorders lines from this menu per job description. It never invents content, so anything not in this file cannot appear on a tailored resume.
>
> **Format rules JobPilot depends on** (keep the section numbers; rename the titles freely):
> - `## N. Title` for sections, `### N.N — Title` for subsections.
> - Numbered items (`1. ...`) are the selectable lines. Prose, blockquotes, and tables are ignored (except the §0.5.2 table and the §8 skills lines).
> - Section numbers map to resume slots: **§3, §4, §5** = your current employer (main bullet list), **§6** = "earlier impact" bullets at that same employer, **§7** = your previous employer, **§17** = optional side projects. Change the mapping in `config.json` under `tailoring.menu_slots` if your history is shaped differently.
> - Items containing `✅` or `~~strikethrough~~` are skipped (use them to park retired lines).
> - Bold **inline metrics**; the engine uses numbers to rank bullets and to reject any rephrasing that introduces a number not in the source line.
>
> `scripts/onboard.py` drafts this file from your existing resume. Review every line: the engine trusts this file completely.

**How to use:**
1. Pick the 4-6 strongest bullets per role for the JD you're targeting, strongest first.
2. Run selected bullets through §0.5 (audience translation) so every company-internal term is legible to a stranger.
3. Mirror the JD's exact phrases in your Skills line and at least one bullet.
4. Keep your brand subtitle constant across applications; swap summary variants and bullet selection per role.

---

## 0. Brand Building Blocks — pick one of each, then stay consistent

### 0.1. Value Proposition (your 1-sentence pitch — internal, drives bullet selection)

1. *"I help [type of company] [outcome] by combining [strength A] with [strength B]."*
2. *"I [what you repeatedly do] so that [who benefits] can [result]."*

### 0.2. Personal Brand Subtitle (1-line under your name)

1. **Senior Product Manager — [Domain A], [Domain B] & [Domain C]** *(the safe default; the tailoring engine picks from this list verbatim)*
2. Senior Product Manager — 0:1 Platforms & AI-Accelerated Product Development *(domain-neutral variant)*
3. Senior Product Manager — Growth, Payments & Platform Products *(for payments-titled roles)*

### 0.3. Red-Thread one-liners (the recurring theme across every win)

> *"[Name] is the person who [the thing every one of your wins has in common]."*

### 0.4. Counterfactual stems (the "without me" framing that sharpens any bullet)

- *Without me, [team] would still [status quo], costing [cost].*

## 0.5. Audience Translation — internal language vs. external-ready

### 0.5.1 — The 4-tier framework

See `materials/guides/resume_generalization_guide.md`. Tier 4 terms must be translated every time.

### 0.5.2 — Translation lookup (Tier 4 — translate every time)

> One row per company-internal term. JobPilot applies the **quoted phrase in the last column** to every selected bullet automatically. Keep the internal term under 30 characters; separate aliases with ` / `.

| Internal term | What it is | Recommended generalized form |
|---|---|---|
| **ACME-Pro** | Flagship subscription product (example row, replace) | "the flagship subscription product" |
| **Growth Pod** | Cross-functional squad name (example row, replace) | "the growth team" |

### 0.5.3 — Tier 3 vendors (define inline on first use)

- *Vendor name* — one-phrase description.

### 0.5.4 — Tier 2 industry-standard (spell out once)

- KYC, SDLC, RICE, OKRs ... (list the acronyms you use)

---

## 1. Professional Summary — drop-in variants

> Each variant front-loads brand promise, signature scope, and differentiator, in 3 sentences max. Format: `1. **(Label)** text`. The engine offers every variant to the LLM and falls back to the baseline resume's summary in basic mode.

1. **(General)** [Title] at [Company] who [core strength]. [Tenure]+ years across [product areas], most recently [flagship result with **bolded metric**]. [Trajectory or differentiator sentence].
2. **(Growth focus)** [Variant emphasizing growth, acquisition, experimentation.]
3. **(0:1 / platform focus)** [Variant emphasizing greenfield launches.]
4. **(Compressed, 2 lines)** [Short variant for tight templates.]

---

## 2. Role Context Lines — sit between title progression and bullets

> A 1-line scope statement that establishes the size of the system you operated on. Goes directly under the title progression block in the resume template.

### 2.1 — [Current employer]

1. *[Scope line: portfolio size, team size, promotions, what you own.]*

### 2.2 — [Previous employer]

1. *[Scope line.]*

---

## 3. [Current title] — [Team] ([Start month year] — Present)

> Your current role. Group bullets by theme in `###` subsections; the engine picks across all of them. 4-8 bullets per subsection is plenty.

### 3.1 — Strategy & vision

1. [Action verb] [what] resulting in **[metric]**; [why it mattered].
2. [Action verb] [what] ... **[metric]**.

### 3.2 — Execution & delivery

1. Launched [product] [when/how fast], driving **[metric]**.
2. Shipped [feature]; lifted [KPI] by **[X%]**.

### 3.3 — Process / org-building

1. Migrated [process] from [old] to [new], saving each [role] **[hours/week]**.

### 3.4 — Cross-functional leadership

1. Led [cross-functional partners] through [initiative]; [outcome].

### 3.5 — Customer-back impact

1. Removed a **[N]-year-old** customer friction point by [what]; [metric].

---

## 4. [Previous title at the same employer] ([dates])

### 4.1 — Highlights

1. [Bullet with **metric**.]
2. [Bullet with **metric**.]

---

## 5. [Earlier title at the same employer] ([dates])

### 5.1 — Highlights

1. [Bullet with **metric**.]

---

## 6. Earlier impact at [current employer] ([dates])

> Rendered under the "Earlier impact" subhead inside the current-employer block (1-2 bullets). Leave empty (no numbered items) if you have a single title at your current employer.

### 6.1 — Flagship earlier wins

1. [Your single biggest early win, with **metric**.]

---

## 7. [Previous employer] — [Title] ([dates])

> The second role block on the resume. The engine selects exactly 1 bullet here in basic mode (more in LLM mode when space allows).

### 7.1 — Compressed (recommended for most resumes)

1. [One bullet that captures the role, with **metric** or promotion signal.]

### 7.2 — Full set (for roles where this experience matters)

1. [Bullet.]
2. [Bullet.]

---

## 8. Skills & Tools — modular keyword library

> Pick **15-20** per application to mirror the JD. Lines of `·`-separated tokens; the engine reads every `·` line in this section as the skills library.

### Product management

Product Strategy · Product Vision · Roadmap Management · Discovery · Prioritization Frameworks (RICE, ICE) · OKRs · A/B Testing · Experimentation Frameworks · Stakeholder Management · Cross-Functional Leadership

### Domain

[Domain term] · [Domain term] · [Domain term]

### Tools & platforms

Jira · Confluence · Figma · SQL · Amplitude / Mixpanel · Tableau / Looker

### Methodologies

Agile / Scrum · Kanban · Design Thinking · Customer Interviews · Jobs-to-Be-Done

### Soft / leadership

Mentoring & Onboarding · Executive Communication · Negotiation · Coaching

---

## 9. Education & Training

1. **[University]**, [Degree] ([years]). [Honors, activities.]
2. **[Course or certification]** ([date]). [One-line description.]

---

## 10. Selected Achievements / Awards

1. **[Award or promotion record]** ([dates]).

---

## 11. Quick Reference — top quantified hits

| Metric | Period | Source |
|---|---|---|
| **[$X]** [what] | [year] | [where the number comes from] |

---

## 17. Projects / Independent Work (optional)

> Rendered as its own role-block-styled section between Experience and Skills when the JD triggers it (set `tailoring.projects` in `config.json`: heading, dates, scope line, and trigger terms). Delete this section if you have nothing to put here.

1. Built and shipped **[N]** [products] solo, incl. [notable project] ([platforms]).
2. [Second project bullet with **metric**.]
