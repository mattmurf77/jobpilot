# MANIFEST F — Big-4 Team-by-Team Career-Site Coverage Audit (2026-07-10)

Re-run of the interrupted coverage audit. Scope: all 124 Big-4 teams (32 NFL + 30 NBA +
30 MLB + 32 NHL). Method: (1) paginated all four TeamWork Online (TWO) league feeds and
scraped the four TWO league landing directories (`/football-jobs`, `/basketball-jobs`,
`/baseball-jobs`, `/hockey-jobs`) for org portals; (2) probed every holdout's careers
site for ATS signatures (myworkdayjobs / greenhouse / lever / ashby / icims /
smartrecruiters / jobvite / ultipro / dayforce / paycom / paylocity / adp / bamboohr /
hireology / radancy), including Workday CXS POST probes (`{"limit":1,"offset":0}`) and
greenhouse/lever/ashby/smartrecruiters/workable slug probes.

## Files changed

- `config.json` — appended 2 `dream_companies` entries (all 28 existing entries
  preserved exactly):
  - **LA Clippers** — greenhouse `laclippers` (verified live via boards-api, 10 postings).
  - **Seattle Seahawks** — `generic` on `https://seattleseahawks.applytojob.com/apply`
    (JazzHR-hosted, server-rendered; `extract_job_links` returned 15 clean title+URL
    links when tested).
- No backend or web files touched (other agents own those).

## Coverage model

A team counts as covered if any of: (a) it has a TWO org portal — the four league-wide
TWO feed entries in config aggregate every org's postings, and zero current postings
still counts because the feed catches future ones; (b) a dedicated board for it (or its
ownership group) already exists in `config.json`; (c) a new verified entry was added in
this audit. Teams on unsupported ATSes (iCIMS, UKG/UltiPro, Dayforce, Paycom, Paylocity,
ADP Workforce Now, BambooHR, Hireology, Radancy) are documented as gaps, not added.

## NFL (32) — 22 TWO / 4 existing config / 1 added / 5 unmonitorable

| Team | Coverage |
|---|---|
| Arizona Cardinals | TWO (`football-jobs/arizona-cardinals-jobs/arizona-cardinals`) |
| Atlanta Falcons | TWO (`football-jobs/atlanta-falcons-careers/amb-atlanta-falcons-jobs`) |
| Baltimore Ravens | Own board in config (generic, baltimoreravens.com/employment) |
| Buffalo Bills | TWO (`football-jobs/buffalo-bills/buffalo-bills-29559`) |
| Carolina Panthers | TWO via Tepper Sports & Entertainment (`multiple-properties/tepper-sports-entertainment-jobs/carolina-panthers`) |
| Chicago Bears | UNMONITORABLE — ADP Workforce Now (unsupported); careers page anchors are "click here" junk, generic diff not viable |
| Cincinnati Bengals | TWO (`football-jobs/footballjobs/cincinnati-bengals`) |
| Cleveland Browns | TWO (`football-jobs/browns/cleveland-browns-28698`) |
| Dallas Cowboys | TWO (`football-jobs/dallascowboys/dallas-cowboys-29704`) |
| Denver Broncos | Own board in config (greenhouse `denverbroncosteamllc`) |
| Detroit Lions | TWO (`football-jobs/detroit-lions/lions`) |
| Green Bay Packers | TWO (`football-jobs/greenbay-packers-jobs/green-bay-packers-`) |
| Houston Texans | TWO (`football-jobs/texans/houston-texans`) |
| Indianapolis Colts | TWO (`football-jobs/indianapolis-colts-jobs/indianapolis-colts`) |
| Jacksonville Jaguars | TWO (`football-jobs/footballjobs/jacksonville-jaguars`) |
| Kansas City Chiefs | TWO (`football-jobs/chiefs/kansas-city-chiefs-29577`) |
| Las Vegas Raiders | TWO (`football-jobs/raiders/raiders-jobs`) |
| Los Angeles Chargers | TWO (`football-jobs/los-angeles-chargers-jobs/los-angeles-chargers`) |
| Los Angeles Rams | TWO (`football-jobs/la-rams-careers/los-angeles-rams`) |
| Miami Dolphins | TWO (`football-jobs/miami-dolphins-jobs/miami-dolphins`) |
| Minnesota Vikings | UNMONITORABLE — ADP Workforce Now (cid 79875354-…); no server-rendered job list found |
| New England Patriots | UNMONITORABLE — Paycom via The Kraft Group (thekraftgroup.com/careers lists ~12 Paycom department portals, JS boards) |
| New Orleans Saints | UNMONITORABLE — Dayforce (`bensonenterprises/SITE/SAINTSPELSCAREERS`, shared with Pelicans) |
| New York Giants | TWO (`football-jobs/new-york-giants-jobs/new-york-giants`) |
| New York Jets | TWO (`football-jobs/footballjobs/new-york-jets`) |
| Philadelphia Eagles | Own board in config (greenhouse `philadelphiaeagles`) |
| Pittsburgh Steelers | TWO (`football-jobs/footballjobs/pittsburgh-steelers-`) |
| San Francisco 49ers | Own board in config (generic, 49ers.com/employment) |
| Seattle Seahawks | **ADDED** — generic on JazzHR page `seattleseahawks.applytojob.com/apply` (found via iframe on seahawks.com → www2.seahawks.com/employment/openings) |
| Tampa Bay Buccaneers | UNMONITORABLE — Dayforce (`tbb/CANDIDATEPORTALTBB`) |
| Tennessee Titans | TWO (`football-jobs/footballjobs/tennessee-titans`) |
| Washington Commanders | TWO (`football-jobs/washington-commanders-jobs/washington-commanders-jobs`) |

## NBA (30) — 16 TWO / 2 existing config / 1 added / 11 unmonitorable

| Team | Coverage |
|---|---|
| Atlanta Hawks | TWO (`basketball-jobs/atlanta-hawks-jobs/atlanta-hawks-jobs`) |
| Boston Celtics | UNMONITORABLE — ADP Workforce Now (single portal link, JS board) |
| Brooklyn Nets | TWO (`basketball-jobs/brooklynnets/bse-global-jobs`) + existing config greenhouse `bseglobal` |
| Charlotte Hornets | TWO (`basketball-jobs/charlotte/charlotte-hornets`) |
| Chicago Bulls | UNMONITORABLE — Paylocity (`recruiting.paylocity.com/.../The-Chicago-Bulls`); nba.com/bulls/careers is JS-only |
| Cleveland Cavaliers | TWO (`basketball-jobs/cleveland-cavaliers/cleveland-cavaliers-28520`) |
| Dallas Mavericks | UNMONITORABLE (JS-only) — nba.com/mavs/careers renders client-side, no ATS host discoverable, careers.mavs.com NXDOMAIN |
| Denver Nuggets | Existing config: Kroenke Sports & Entertainment TWO board |
| Detroit Pistons | UNMONITORABLE — Paylocity (`recruiting.paylocity.com/.../Detroit-Pistons`) |
| Golden State Warriors | TWO (`basketball-jobs/warriors/golden-state-warriors-careers`) |
| Houston Rockets | TWO (`basketball-jobs/houston-rockets-jobs/houston-rockets`) |
| Indiana Pacers | TWO (`basketball-jobs/pacers/pacers-sports-entertainment`) |
| LA Clippers | **ADDED** — greenhouse `laclippers` (10 live postings via boards-api) |
| Los Angeles Lakers | TWO (`basketball-jobs/los-angeles-lakers/los-angeles-lakers-jobs`) |
| Memphis Grizzlies | UNMONITORABLE — iCIMS (`careers-grizzlies.icims.com`, unsupported ATS) |
| Miami Heat | UNMONITORABLE — UKG UltiPro (`recruiting.ultipro.com/MIA1004MHLP`) |
| Milwaukee Bucks | TWO (`basketball-jobs/milwaukee-bucks-jobs/milwaukee-bucks`) |
| Minnesota Timberwolves | UNMONITORABLE — Dayforce (`packportal/CANDIDATEPORTAL`) |
| New Orleans Pelicans | UNMONITORABLE — Dayforce (`bensonenterprises/SITE/SAINTSPELSCAREERS`, shared with Saints) |
| New York Knicks | UNMONITORABLE — MSG Sports, JS-only careers site (known gap from MANIFEST E) |
| Oklahoma City Thunder | UNMONITORABLE — Paycom; job links exist on nba.com/thunder/employment but only inside JS strings (extract_job_links → 0) |
| Orlando Magic | TWO (`basketball-jobs/orlandomagic/orlando-magic-28482`) |
| Philadelphia 76ers | TWO via HBSE (`multiple-properties/harris-blitzer-sports-entertainment-jobs/philadelphia-76ers-jobs`) |
| Phoenix Suns | TWO (`basketball-jobs/phoenix-suns/phoenix-suns`) |
| Portland Trail Blazers | UNMONITORABLE — Radancy/ttcportals (`jobs.ripcity.org`, CNAME lb.ttcportals.com; 403 bot-blocked) |
| Sacramento Kings | TWO (`basketball-jobs/sacramento-kings-jobs/sacramento-kings`) |
| San Antonio Spurs | TWO (`multiple-properties/spurs-jobs/san-antonio-spurs`) |
| Toronto Raptors | Existing config: MLSE workday `mlse.wd3/MLSE` |
| Utah Jazz | TWO (`basketball-jobs/utah-jazz-jobs/utah-jazz`) |
| Washington Wizards | TWO via Monumental (`multiple-properties/monumentalsports/monumental-sports`) |

## MLB (30) — 26 TWO / 2 existing config / 0 added / 2 unmonitorable

| Team | Coverage |
|---|---|
| Arizona Diamondbacks | TWO (`baseball-jobs/arizona-diamondbacks-jobs/arizona-diamondbacks`) |
| Athletics | TWO (`baseball-jobs/athletics-jobs/athletics-jobs`) |
| Atlanta Braves | TWO (`baseball-jobs/atlanta-braves/atlanta-braves-jobs`) |
| Baltimore Orioles | TWO (`baseball-jobs/orioles-jobs/baltimore-orioles-jobs`) |
| Boston Red Sox | TWO via Fenway Sports Group (`baseball-jobs/fenwaysports/boston-red-sox`) |
| Chicago Cubs | TWO (`baseball-jobs/chicagobaseball/chicago-cubs`) |
| Chicago White Sox | TWO (`baseball-jobs/chicago-white-sox/chicago-white-sox-`) |
| Cincinnati Reds | TWO (`baseball-jobs/cincinnati-reds/cincinnati-reds`) |
| Cleveland Guardians | Own board in config (greenhouse `clevelandguardiansbops`) |
| Colorado Rockies | TWO (`baseball-jobs/colorado-rockies/colorado-rockies-jobs`) |
| Detroit Tigers | TWO via Ilitch Sports (`multiple-properties/ilitch-sports/detroit-tigers`) |
| Houston Astros | UNMONITORABLE — UKG UltiPro (`recruiting2.ultipro.com/HOU1000`); the TWO link on mlb.com/astros/team/jobs (`baseball-jobs/houstonbaseball/houston-astros`) is stale → 404 |
| Kansas City Royals | TWO (`baseball-jobs/kansas-city-royals-jobs/kansas-city-royals`) |
| Los Angeles Angels | TWO (`baseball-jobs/los-angeles-angels-jobs/los-angeles-angels`) |
| Los Angeles Dodgers | TWO (`baseball-jobs/los-angeles-dodgers-jobs/los-angeles-dodgers`) |
| Miami Marlins | TWO (`baseball-jobs/miamibaseball/miami-marlins`) |
| Milwaukee Brewers | TWO (`baseball-jobs/milwaukeebaseball/milwaukee-brewers`) |
| Minnesota Twins | TWO (`baseball-jobs/minnesota-twins/minnesota-twins-jobs`) |
| New York Mets | TWO (`baseball-jobs/new-york-mets-jobs/new-york-mets-jobs`) |
| New York Yankees | TWO (`baseball-jobs/new-york-yankees/new-york-yankees`) |
| Philadelphia Phillies | TWO (`baseball-jobs/philadelphia-phillies/philadelphia-phillies`) |
| Pittsburgh Pirates | TWO (`baseball-jobs/pittsburghpirates/pittsburgh-pirates-jobs`) |
| San Diego Padres | UNMONITORABLE — Hireology (`careers.hireology.com/sandiegopadres`, JS-rendered, unsupported ATS) |
| San Francisco Giants | Own board in config (lever `sfgiants`) |
| Seattle Mariners | TWO (`baseball-jobs/seattle-mariners/seattle-mariners`) |
| St. Louis Cardinals | TWO (`baseball-jobs/stl-cardinals/st--louis-cardinals`) |
| Tampa Bay Rays | TWO (`baseball-jobs/tampa-bay-rays/tampa-bay-rays`) |
| Texas Rangers | TWO (`baseball-jobs/texasbaseball/texas-rangers`) |
| Toronto Blue Jays | TWO (`baseball-jobs/toronto-blue-jays-jobs/toronto-blue-jays`) |
| Washington Nationals | TWO (`baseball-jobs/washington-nationals/washington-nationals`) |

## NHL (32) — 25 TWO / 3 existing config / 0 added / 4 unmonitorable

| Team | Coverage |
|---|---|
| Anaheim Ducks | TWO (`hockey-jobs/anaheim-ducks-jobs/anaheim-ducks-hockey-club`) |
| Boston Bruins | TWO (`hockey-jobs/boston-bruins-jobs/boston-bruins-jobs`) |
| Buffalo Sabres | TWO (`hockey-jobs/buffalosports/buffalo-sabres-29560`) |
| Calgary Flames | UNMONITORABLE — UKG UltiPro Canada (`recruiting.ultipro.ca/CAL5002` via csecjobs.com) |
| Carolina Hurricanes | TWO (`hockey-jobs/carolina-hurricanes-jobs/carolina-hurricanes`) |
| Chicago Blackhawks | TWO (`hockey-jobs/chicago-blackhawks/chicago-blackhawks`) |
| Colorado Avalanche | Existing config: Kroenke Sports & Entertainment TWO board |
| Columbus Blue Jackets | TWO (`hockey-jobs/hockeyjobs/columbus-blue-jackets`) |
| Dallas Stars | TWO (`hockey-jobs/dallas-stars-jobs/dallas-stars`) |
| Detroit Red Wings | TWO via Ilitch Sports (`multiple-properties/ilitch-sports/detroit-red-wings`) |
| Edmonton Oilers | TWO (`hockey-jobs/edmontonoilers/edmonton-oilers-29182`) |
| Florida Panthers | TWO (`hockey-jobs/floridapanthers/florida-panthers`) |
| Los Angeles Kings | TWO (`hockey-jobs/los-angeles-kings-jobs/los-angeles-kings-28605`) |
| Minnesota Wild | TWO (`hockey-jobs/minnesota-wild-jobs/minnesota-se`) |
| Montreal Canadiens | UNMONITORABLE — no reachable careers endpoint: groupech.ca times out, carrieres subdomains NXDOMAIN, nhl.com/canadiens careers paths 404, no ATS/TWO signature found |
| Nashville Predators | TWO (`hockey-jobs/nashville-predators/nashville-predators`) |
| New Jersey Devils | TWO via HBSE (`multiple-properties/harris-blitzer-sports-entertainment-jobs/new-jersey-devils-jobs`) |
| New York Islanders | TWO (`hockey-jobs/new-york-islanders/new-york-islanders`) |
| New York Rangers | UNMONITORABLE — MSG Sports, JS-only careers site (known gap from MANIFEST E) |
| Ottawa Senators | UNMONITORABLE — BambooHR (`ottawasenators.bamboohr.com/careers`, unsupported ATS) |
| Philadelphia Flyers | TWO via Comcast Spectacor (`hockey-jobs/philadelphia-flyers-jobs/philadelphia-flyers-jobs`) |
| Pittsburgh Penguins | TWO (`hockey-jobs/pittsburgh-penguins/pittsburgh-penguins`) |
| San Jose Sharks | TWO (`hockey-jobs/sharkssports/san-jose-sharks`) |
| Seattle Kraken | TWO (`hockey-jobs/seattle-kraken-/nhl-seattle-jobs`) |
| St. Louis Blues | TWO (`hockey-jobs/hockeyjobs/st--louis-blues`) |
| Tampa Bay Lightning | TWO (`hockey-jobs/tampanhl/tampa-bay-lightning-jobs`) |
| Toronto Maple Leafs | Existing config: MLSE workday `mlse.wd3/MLSE` |
| Utah Mammoth | TWO (`hockey-jobs/utah-nhl-jobs/utah-nhl-jobs`) |
| Vancouver Canucks | TWO (`hockey-jobs/vancouver-canucks/vancouver-canucks`) |
| Vegas Golden Knights | TWO (`hockey-jobs/vegas-golden-knights/vegas-nhl`) |
| Washington Capitals | TWO via Monumental (`multiple-properties/monumentalsports/washington-capitals-jobs`) |
| Winnipeg Jets | Existing config: True North Sports (generic, tnse.com/join-our-team) |

## Totals

- Covered: 102 / 124 (89 TWO-native + 11 existing config boards + 2 added this audit)
- Unmonitorable: 22 (11 NBA, 5 NFL, 4 NHL, 2 MLB) — all on unsupported ATSes
  (Dayforce ×4-team, Paylocity ×2, Paycom ×2, ADP ×3, UltiPro/UKG ×3, iCIMS ×1,
  BambooHR ×1, Hireology ×1, Radancy ×1) or JS-only/unreachable (MSG ×2, Mavericks,
  Canadiens).
- Most-wanted future ATS support by unlocked teams: Dayforce (Saints+Pelicans, Bucs,
  Timberwolves), UKG UltiPro (Heat, Astros, Flames), Paylocity (Bulls, Pistons),
  ADP Workforce Now (Bears, Vikings, Celtics), Paycom (Patriots/Kraft Group, Thunder).

## Verification (POST /api/jobs/refresh, Flask test client, 2026-07-10)

- `config.json` parses; 30 dream companies (28 preserved exactly + 2 appended).
- Refresh: **200 in 53s, zero errors** (Establish The Run passed this run too).
  - fetched 1703, new 537, **new_dream 36**
  - per_source: greenhouse 1093, lever 268, ashby 235, dream-greenhouse 37,
    dream-teamworkonline 13, dream-workday 11, dream-ashby 7, **dream-generic 2**,
    remotive 30, remoteok 7
- New-entry rows: Seattle Seahawks 2 (dream-generic — "Digital Marketing Products
  Coordinator", "Part-Time Digital Products Coordinator"). LA Clippers board fetches
  clean (10 postings) but 0 currently pass the title filter — monitoring is the point,
  same situation as NFL League Office in MANIFEST E.
- DB integrity: statuses untouched (archived 2, tailored 22 — identical to MANIFEST E);
  no deletions.
