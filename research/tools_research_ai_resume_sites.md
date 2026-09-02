# Commercial AI resume/cover-letter tools: survey and verdict (2025-2026)

*Provenance: web research + hands-on check of Jobscan's live pricing page (jobscan.co, accessed 2026-08-05). All other tool claims are secondhand, sourced from 2025-2026 reviews/aggregators and Reddit-sentiment summaries as cited; marked (anecdotal) where evidence is Reddit/forum chatter rather than a formal study.*

## All-in-one builders (generate + tailor + templates)

**Teal** — Free tier is real (unlimited resumes/edits, job tracker, 11 ATS-styled templates, basic keyword match); Teal+ is $9/wk, $29/mo, or $79/qtr for unlimited AI generation and deeper keyword tools. Reviewers flag that Teal markets itself as "ATS-optimized" while still shipping two-column templates some ATS can't parse (Rezi Blog 2026; ResuFit 2026). Reddit consensus (anecdotal): best free organizer/tracker, AI content sometimes generic or wrong (r/resumes summaries via atsresumeai.com 2026).

**Kickresume** — Free version exists; paid €10-24/mo (student-verified users get it free via ISIC/UNiDAYS). Complaints cluster on billing: unused monthly credits vanish, cancellation/refunds are slow (resumejudge.com, FireBear 2026). Liked for template variety (35+) and fast AI drafts (Reddit, anecdotal).

**Rezi** — Free (1 resume), Pro $29/mo, Lifetime $149. Built around the "Rezi Score" (0-100 across 23 formatting/content criteria) and JD-paste keyword targeting. Reviewers (Scoutify 2026, ResumeGenius) say the score is "oversold" — it's mostly a keyword/format checklist, useful but not a hiring-outcome guarantee.

**Enhancv** — Free tier: all templates/design tools, no card, but capped at 12 section items plus Enhancv branding on exports; no .docx export as of mid-2026. Paid $19.99-24.99/mo with an auto-renewing 7-day trial. ATS parsing tests self-reported 92-99% on simple templates, worse on graphic/multi-column ones (loopcv.pro, PitchMeAI 2026).

**Zety** — Named repeatedly (Reddit, arXiv dark-pattern survey 2023 context, Trustpilot 2025-2026) as the canonical "paywall the download" builder: build for 30-60 min, hit a paywall, $1.95 trial silently converts to $25.95/4wk; cancel-button "glitches" and post-cancellation charges are recurring complaints. Treat as a cautionary example, not a recommendation.

**Wonsulting/ResumAI** — Free "Starter" (unlimited downloads, but only 5 AI bullet generations, 3 cover letters); Premium $19.99/mo unlimited; also sells $699-$2,299 "Ultimate Bundle" 1:1 coaching packages, a notably different (and pricier) business model than pure software.

## Job-search copilots

**Simplify.jobs** — Autofill/tracking is free forever (1M+ installs, 4.86/5 on Chrome Web Store) and works across 50+ boards including Workday/Greenhouse/Lever. AI resume *tailoring* is gated behind Simplify+ ($39.99/mo). Best-in-class for reducing application-form drudgery, not for writing quality.

**Careerflow.ai** — Free LinkedIn profile optimizer is genuinely useful (catches weak headlines/summaries); free resume builder capped at 1 resume, 10 tracked jobs. Pro $23.99-45/mo; reviewers say the paid tracker/AI rewriter feel "half-built" — use the free LinkedIn tool, skip the rest (Scoutify 2026).

## ATS-match checkers

**Jobscan** (hands-on, 2026-08-05) — Free: 5 scans/month + basic findings. Paid: $49.95/mo, or $29.98/mo billed quarterly ($89.95/3mo) after a 7-day free trial that auto-converts to the paid plan if not cancelled. Mechanism: extracts resume text, compares to JD keyword frequency/weighting, and claims to detect the specific ATS (Taleo, Greenhouse, etc.) to tailor advice; recommends an 80%+ match rate. Independent testing found Jobscan, Enhancv, and other checkers disagree by up to 18 points on the *same* resume/JD pair (getresumatch.com 2026) — scores are directionally useful for keyword gaps but not standardized or predictive of recruiter interest. Jobscan's own 2025 study: 97.8% of Fortune 500 use ATS, 76.4% of recruiters filter by skills pre-read — supports the *need* for keyword matching generally, not the precision of any one score.

## Cover-letter specialists

**Cover Letter Copilot** — Small (sub-10-person), founded 2023, upload-resume + paste-JD + pick-tone flow. 2026 head-to-head testing (Jobscan blog, Venngage) ranks it best for "personalized polish" but flags that intros/outros can read "hyperbolic and robotic" — exactly where a recruiter's attention is highest.

## Bolt-on features from non-resume-first players

**Grammarly** — Added a Resume Builder agent (Pro/Plus/Superhuman Go users; free users get a capped number of suggestions/day). ATS-templated output, but it's a feature bolted onto a writing tool, not a resume-first product.

**LinkedIn** — "Tailor my resume to this job" via the Sparkle AI popup (desktop, English-only) and an AI career-coach beta for Premium members; feels early/limited rollout as of 2026.

**Canva** — Magic Write (25 free prompts, then Pro-gated) is a generic short-form text generator dropped into a resume template; reviewers call quality "noticeably weaker than dedicated alternatives" for resume content specifically (VantageLabs 2026).

## Privacy note
None of Teal, Kickresume, or Rezi publish an explicit "we do/don't train models on your resume" statement in their public privacy policies as of this research; Kickresume acknowledges routing content through OpenAI/third-party AI providers and "service providers" broadly. Assume free-tier uploads may transit third-party model APIs; no tool reviewed here offers a clear no-train guarantee on the free tier.

## Synthesis

**Top picks by use case:** Tailoring/organizing → Teal (free tier is legitimately non-bait-and-switch). ATS keyword-gap checking → Jobscan (best-known, but cross-check scores manually — treat as a checklist, not a grade). Cover letters → Cover Letter Copilot for polish, but hand-edit the opening/closing lines. Application-form drudgery → Simplify's free autofill. Templates/design → Kickresume or Enhancv, budget for the billing friction. Avoid: Zety, unless you read every screen before entering a card.

**What these tools offer that a home-built keyword-scored/bullet-library pipeline does not:** (1) LinkedIn-profile-specific optimization (headline/summary scoring against recruiter search behavior — Careerflow); (2) cross-ATS parsing-format testing against real ATS engines (Enhancv/Jobscan claim to test actual Workday/Taleo/Greenhouse rendering, which a local pipeline can't easily replicate without those systems); (3) application-autofill across 50+ live job boards (Simplify) — pure time-saving, unrelated to content quality; (4) a large second-opinion keyword frequency/weighting model trained on aggregate recruiter/ATS behavior (Jobscan's "which ATS is this" detection) rather than a single JD's raw text.

**What they do worse:** (1) Genericness — AI-generated bullets/cover-letter intros are the most-cited weakness across every tool surveyed, precisely the failure mode a hand-curated bullet library avoids by construction. (2) Template-detectability — two-column/graphic templates that fail ATS parsing are a recurring, documented issue (Teal, Enhancv) — a plain single-column PDF renderer sidesteps this entirely. (3) Inconsistent, non-standardized scoring — the same resume scores in the low-60s to mid-80s across checkers (18-point spread documented), so a home ATS-keyword-match score is no less "real" than these commercial ones. (4) Billing dark patterns — Zety's trial-to-$25.95/4wk conversion, Kickresume's vanishing monthly credits, and Enhancv's auto-renewing 7-day trial are all documented complaint patterns a self-run pipeline has zero exposure to.
