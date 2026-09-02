# MANIFEST E — Big-4 Pro Sports Dream-Company Monitoring (2026-06-11)

## Files changed

- `backend/sources/dream.py` — added ATS type `teamworkonline` (URL pattern in
  `ATS_URL_PATTERNS`, `_fetch_teamworkonline`, `_two_fill_descriptions`, wiring in
  `fetch_postings` / `fetch_company`). For TWO league feeds the per-card team/org is
  kept as the job's `company` (the config entry name would otherwise mask which team
  posted). Per-company error isolation unchanged.
- `config.json` — appended 8 `dream_companies` entries (all existing entries preserved
  exactly). Note: config.json is listed as shared in CONTRACTS.md; editing it was
  explicitly granted in this agent's assignment.

## Research table (all probed live with browser UA, 2026-06-11)

| Org | Platform / ATS | Slug / endpoint | Live postings | Notes |
|---|---|---|---|---|
| NFL League Office | Greenhouse | `nflcareers` | 36 | Pre-verified by orchestrator; re-confirmed live. 0 titles currently contain "product" — filter keeps 0 today, monitoring is the point. |
| BSE Global / Brooklyn Nets | Greenhouse | `bseglobal` | 25 | Pre-verified by orchestrator. |
| MLB League Office | Greenhouse (embedded) | `majorleaguebaseball` | 76 | Found via `mktg.mlbstatic.com/mlb/careers/opportunities/greenhouse.js` (`GH_BOARD = 'majorleaguebaseball'`) loaded by www.mlb.com/careers/opportunities. Heavy NYC PM presence (Sr PM Subscriptions/Streaming, Sr PM Fan Data Platform, etc.). |
| NBA League Office | Workday CXS | `nba.wd108/nbacareers` | 30 | careers.nba.com is Phenom People (CNAME nba.phenompeople.net; `/widgets` refineSearch POST also works, totalHits 30) but Phenom apply URLs expose the real Workday tenant `nba.wd108.myworkdayjobs.com/nbacareers` — used the existing `workday` ATS, no new code. |
| NHL League Office | TeamWork Online | hockey feed below | — | www.nhl.com/info/careers links to teamworkonline.com/hockey-jobs/hockeyjobs/nhl-league-office; league-office roles post under org "NHL Team Jobs" inside that feed. No NHL Workday tenant (nhl.wd1/wd5 CXS → 422). |
| NFL Teams (TWO) | TeamWork Online | `football-jobs/footballjobs/nfl-football-jobs` | 178 (4 pages) | |
| NBA Teams (TWO) | TeamWork Online | `basketball-jobs/nbateamjobs/nba-league-office` | 180 (4 pages) | |
| MLB Teams (TWO) | TeamWork Online | `baseball-jobs/baseballjobs/major-league-baseball` | 177 (4 pages) | Includes Yankees (3 postings at probe time). Mets post here when hiring. |
| NHL Teams + League Office (TWO) | TeamWork Online | `hockey-jobs/hockeyjobs/nhl-league-office` | 115 (3 pages) | Includes NY Islanders org page; Rangers are under MSG (see below). |
| MSG Sports (Knicks/Rangers) | Unresolved | — | — | msg.com/careers is JS-rendered with no ATS hosts in HTML. Workday CXS probes all 422: tenants msg/msgsports/msgentertainment × wd1/wd5 × sites External/Careers/MSG/EXT/External_Careers/MSGCareers/TheGarden/Careers_External/msgsports/msgentertainment. Not on TeamWork Online. Skipped — would need a headless browser. |
| NBA/MLB/NHL Workday guesses | dead | nba/mlb/nhl × wd1/wd5 | — | All 422 (= nonexistent; baseline: draftkings.wd1 → 200, bogus tenant → 422). |

### TeamWork Online findings (the "JACKPOT", slightly different shape)

- No JSON API needed: TWO portal pages are **server-rendered Rails/Turbo HTML** (Heroku +
  Cloudflare), 48 job cards per page, `?page=N` pagination, empty page past the end.
  The orchestrator's "0 links" result came from a stale URL —
  `/football-jobs/footballjobs/nfl-teams` is now a 404; the live NFL feed is
  `/football-jobs/footballjobs/nfl-football-jobs`.
- Card markup parsed: `organization-portal__job-title` (title + posting URL),
  `__job-category` (team/org), `__job-location` ("City · ST"). Posting detail pages are
  also server-rendered (title, org, location, salary, full description) — used for
  best-effort descriptions, capped at `TWO_DETAIL_CAP = 40` per feed per refresh,
  filtered postings only. Page cap `TWO_PAGE_CAP = 12` (current max feed depth is 4).
- `external_id` = trailing numeric posting id (e.g. `...-2173824`), sha1(url) fallback.

## Verification results

- `py_compile backend/sources/dream.py` — clean; `config.json` parses (19 dream companies).
- Standalone fetcher test: NHL feed → 115 postings, clean title/org/location/id;
  `resolve()` URL-pattern detection returns `{ats: teamworkonline, slug: ...}`.
- `POST /api/jobs/refresh` (Flask test client): **200 in 40s, zero errors** (even the
  usually-flaky Establish The Run passed this run).
  - fetched 1569, new 41, **new_dream 18**
  - per_source: dream-greenhouse 32, dream-workday 13, dream-ashby 8,
    **dream-teamworkonline 5**, greenhouse 1039, lever 222, ashby 215, remotive 28, remoteok 7
- Dream jobs by company (`SELECT company, COUNT(*) FROM jobs WHERE dream=1 GROUP BY company`):
  FanDuel 17, **NBA League Office 7**, Polymarket 5, **MLB League Office 5**, DraftKings 4,
  Sleeper 3, PrizePicks 3, Kalshi 3, Fanatics 2, BetMGM 2, Underdog 1,
  **Los Angeles Lakers 1, Florida Panthers 1, Dallas Cowboys 1, Charlotte Hornets 1,
  Atlanta Hawks 1, BSE Global / Brooklyn Nets 1**, Establish The Run 1.
- Sample new sports titles:
  - MLB League Office — Senior Product Manager, Subscriptions and Streaming (New York, NY)
  - MLB League Office — Senior Product Manager, Fan Data Platform (New York, NY)
  - NBA League Office — Data and Innovation Group Product Leader
  - Florida Panthers — Product Engineer (Sunrise, FL) [dream-teamworkonline]
  - Dallas Cowboys — Microsoft 365 Product Specialist (Frisco, TX) [dream-teamworkonline]
- DB integrity: statuses untouched (archived 2, tailored 22, rest new); no deletions.

## Known gaps

- MSG Sports (Knicks/Rangers) unmonitored — JS-only careers site, no discoverable ATS
  endpoint without a headless browser (see table).
- NFL League Office currently contributes 0 rows purely because no live title contains
  a config keyword or "product"; the board itself fetches fine (36 postings).
- TWO `company` is the team/org, not the config entry name — intentional, so a Yankees
  PM role doesn't surface as "MLB Teams (TeamWork Online)".
