---
name: trip-guide-site
description: Plans a trip and builds it as a polished, interactive three-page travel site (plan with day-by-day route maps, distances, photo galleries and a live budget with upgrade options; an offline pocket guide with illustrated chapters per sight; a phrasebook with big-text display and speech), published as an Artifact. Use this whenever the user wants to plan a trip, vacation, city break or itinerary — "хочу поехать в …", "составь программу поездки", "план путешествия", "маршрут по городу", "отель до N тысяч", "что посмотреть в …", "путеводитель", "экскурсия без гида" — or wants an existing travel plan turned into a nicer/interactive report, even if they only ask for "an HTML report" or a table. Also use it to update a trip site made earlier with this skill.
---

# Trip guide site

Turns a trip request into a researched plan and a three-page site:

1. **Plan page** — hero photo, key facts, overview map, hotel picker, day cards (gallery, timeline with distances between stops, walking per day, OSM route map, Yandex/Google route links, upgrade choices), custom sections (shopping, souvenirs, food, budget, practical, checklist), sticky live budget.
2. **Pocket guide** (`guide.html`) — one illustrated chapter per sight: hook, intro, story, 5–7 stations with photos, "find on site" checklist, did-you-know, tip; read-aloud and step-by-step "audio guide" mode; works offline once loaded.
3. **Phrasebook** (`phrases.html`) — categories, search, tap-to-show huge text, speech.

The bundled scripts do the heavy lifting; your job is research, judgment, writing and assembling `trip.json`.

Before starting, read `references/defaults.md` — the default brief (food price caps, hotel level, design, options, distances, page split) that fills gaps the user leaves. The user's own instructions always win.

## Workflow

### 1. Brief (keep it short)
From the message, pin down: destination(s), length and rough dates, travellers, home city/citizenship (drives visa, flights, payments), budget (hotel cap and food rules), interests, luggage, shopping goals, must-haves and no-gos. Ask only for what blocks you; otherwise use the defaults in defaults.md and state them. If dates are unknown, use example dates and say so — but keep closure-sensitive days (e.g. museums closed on Mondays) on the right weekday.

### 2. Research the facts that can wreck a trip
Use WebSearch (standard mode, several queries in one turn) for: entry/visa rules for the traveller's citizenship and their validity dates, current exchange rate, typical flight prices and direct routes, whether home-country bank cards work and what to do instead, internet blocks/roaming, local transport apps, weather for the month, local holidays and weekly closures, tax-free and customs limits for the return. `references/research-checklist.md` lists everything worth checking. Cite sources in the footer.

### 3. Fix the program in chat first
Write the day-by-day program as a compact table (day · date · areas/sights · night location) plus hotel plan and a budget estimate, and let the user react before building anything heavy. Users routinely cut or move days ("убери 5-й день", "сафари верни"); that is cheap in a table and expensive in a built site. When the user asks for a full report straight away, you may build v1 directly — but for any later restructuring, confirm the table first.

Program rules that worked well:
- Group sights geographically; one area per half-day; put closure-prone sights on open days.
- One fine-dining meal max, placed where the route already passes; everything else local and within the per-meal cap.
- Day trips to satellite towns as whole days; overnight elsewhere only when it saves real transit time (compute door-to-door, not just train time).
- Every priced item gets a realistic range for the whole party in local currency.
- Where a noticeably better version costs little more (boat deck vs. lower deck, observation level, massage tier, train class, taxi vs. metro), make it an **option** with a one-line "what you get" note. Don't invent options that are pure padding.

### 4. Gather data (scripts in `scripts/`, run with `python3 -I`)
Work in a trip folder (e.g. `<workdir>/trip/`) with the layout in `references/trip-json.md`; the site output goes to the working directory.
- **Coordinates**: `geocode.py trip/points.json < places.tsv` (Nominatim). Check each hit's display name; fix strays by hand. Use these coordinates everywhere so maps stay consistent.
- **Map layers**: `osm_fetch.py trip/osm/default S W N E` for the main city (box just around the day stops, ~0.2–0.4°), and one extra layer per far-away area (e.g. `trip/osm/sz` for another city). Use `--rivers-only` for big regional boxes. Overpass is often busy; the script retries.
- **Photos for the plan page** (hero, 1–3 per day, dishes, sections): search with `commons_search.py "query" 8`, pick CC0/PD/CC BY/CC BY-SA images ≥1000 px, then `commons_fetch.py photos picks.tsv trip <out>` (writes `img/<slug>.jpg` + `trip/credits.json`). Always look at what you picked: download previews into a folder and run `contact_sheet.py <dir> sheet.jpg`, then Read the sheet. Drop menus, blurry night shots, wrong subjects. Captions must describe what is really in the frame.

### 5. Pocket guide chapters (parallel agents)
Split the sights into groups of ~7 and launch one background agent per group (general-purpose), all in one message. Use the prompt template in `references/guide-agents.md` — it defines the chapter JSON, the writing rules (dense, factual, no clichés, fact-checked, legends labelled) and the photo rules (Commons only, previewed with Read, `local:<slug>` for plan photos). Agents write `trip/guide/<group>.json`. While they work, build everything else. When they finish, run `commons_fetch.py guide trip <out>` to download their photos into `img/g/`.

Also write: a short intro chapter for the city ("<City> in 5 minutes") and for each other city visited — map them via `guide_intro` / a stop's `guide` field.

### 6. Write trip.json and sections, build
- `trip/trip.json` — follow `references/trip-json.md` (example: `assets/example-guangzhou/trip.json`).
- `trip/sections/NN-name.html` — free sections after the plan, each `<section class="block" id="…" data-nav="Label">`. Tokens `{{DISHES}}`, `{{SOUVENIRS}}`, `{{BUDGET}}` are replaced by generated blocks. Reuse the CSS classes from the example sections (`prac`, `rest-cols`, `shop-grid`, `souvs`, `check`, `note`, …) so they match the design.
- Build: `python3 -I scripts/build_site.py trip <out>` → `<main_file>`, `guide.html`, `phrases.html`. It prints the budget total and any missing images.

### 7. Check once, publish, report
Preview and publishing details (local server, wrapper for the main page, upload in batches, `index.html` naming) are in `references/publishing.md`. Look at the pages once (desktop + phone width, both themes), click one option to see the budget move, open one guide chapter; fix what's visibly broken, then publish. In the reply: link, what's in it, and the honest caveats (approximate prices, unverified details the agents flagged, photos shot elsewhere).

## Updating an existing trip
Edit `trip.json` / sections / guide files and rebuild — never hand-edit generated HTML. Re-publish with the same main file path so the URL stays. When days change, also update day references inside sections (shopping "день 8", checklist dates), souvenir "where" fields, hotel nights and booking dates; then rebuild and remove photos no longer used (`trip/used_images.json` lists what the build referenced) — pass `null` for them on publish.
