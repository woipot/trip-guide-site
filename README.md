# trip-guide-site

An Agent Skill for [Claude Code](https://claude.com/claude-code) and [OpenAI Codex](https://developers.openai.com/codex/) that plans a trip and builds it as an interactive three-page travel site:

- **Plan**: hero photo, key facts, overview map, hotel picker, day cards with photo galleries, a timeline with distances and walking time between stops, an OpenStreetMap route map per day, Yandex and Google route links, upgrade options with price differences, and a live budget that recalculates as you choose.
- **Pocket guide**: one illustrated chapter per sight, with a story, 5–7 stations in walking order, a "find on site" checklist, did-you-know facts and a tip. Chapters can be read aloud or followed step by step like an audio guide, and work offline once the page is loaded.
- **Phrasebook**: categories, search, tap a phrase to show it in huge text, and speech playback.

The agent does the research and writing. Guide-writer prompts produce fact-checked chapters and pick freely licensed photos, using parallel sub-agents when available or running sequentially. The bundled Python scripts handle geocoding, map data, photo licensing and credits, the maps and the final HTML.

> The generated UI text is in **Russian**, and prices convert from local currency to a home currency of your choice. To produce sites in another language, translate the strings in `scripts/build_site.py` and `assets/*.js`.

## Install

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/woipot/trip-guide-site ~/.claude/skills/trip-guide-site
```

Restart Claude Code.

### OpenAI Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/woipot/trip-guide-site ~/.agents/skills/trip-guide-site
```

`~/.agents/skills` is where Codex looks for personal skills; it also scans `.agents/skills` inside a repository, so you can vendor the skill into a project instead. The `SKILL.md` frontmatter already has the required `name` and `description`, so no conversion is needed. Restart Codex if the skill does not appear in `/skills`. See the [Codex skills documentation](https://developers.openai.com/codex/skills).

## Quick start

Start Claude Code or Codex in a writable folder for your trip data and generated site, then ask:

> Use the trip-guide-site skill to plan a 10-day trip to Istanbul, hotel up to €100/night.

Or in Codex, explicitly mention the skill:

> $trip-guide-site Хочу поехать в Гуанчжоу на неделю, составь программу.

The agent gathers the brief, researches current facts and proposes the itinerary before building. Open the generated `index.html` locally, or publish the output folder (including both companion pages and images) to GitHub Pages or another static host. The Codex compatibility note in `SKILL.md` covers alternatives to Claude-specific tools.

## Requirements

- Claude Code or Codex with web search, shell access and a writable working folder. Sub-agents and the Artifact publishing tool are optional.
- Python 3.9+; building HTML uses only the standard library.
- Photo compression uses `sips` (built into macOS) or [Pillow](https://pypi.org/project/Pillow/). Contact sheets require Pillow or, on macOS, Swift with AppKit. Install Pillow into the Python environment used by `python3` (for example, a virtual environment); `python3 -I` ignores user-site packages.
- Internet access for research and fetching data from OpenStreetMap Nominatim, Overpass and Wikimedia Commons. The bundled example can be built without network access.
- A browser for preview; speech playback depends on the browser's available voices.

## How it works

1. A short brief, filled in from `references/defaults.md` where the user leaves gaps.
2. Research of the facts that can wreck a trip: visa, money, connectivity, closures, customs (`references/research-checklist.md`).
3. The program is agreed as a table in chat before anything heavy is built.
4. Data gathering:
   - `scripts/geocode.py`: coordinates from Nominatim;
   - `scripts/osm_fetch.py`: water, parks and metro layers;
   - `scripts/commons_search.py` and `scripts/commons_fetch.py`: freely licensed photos with credits;
   - `scripts/contact_sheet.py`: a grid of candidate photos to review visually.
5. Guide chapters from parallel agents or sequential writing, using the prompt in `references/guide-agents.md`.
6. `scripts/build_site.py trip/ out/` builds `index.html`, `guide.html` and `phrases.html`, plus a fragment that can be published as an Artifact. The data format is described in `references/trip-json.md`.
7. Publish as an Artifact, or upload the output folder to any static host such as GitHub Pages.

`assets/example-guangzhou/` holds a complete real trip (11 days in Guangzhou and Shenzhen) to use as a reference. To build it:

```bash
python3 -I scripts/build_site.py assets/example-guangzhou /tmp/gz-site
```

Maps render without background layers and photos are missing until you fetch them with the scripts.

## Customising

Edit `references/defaults.md` to set your own default style: food budget per meal, hotel level, trip length and design preferences. The skill treats the file as the brief whenever the user doesn't say otherwise.

## Data and licences

- Maps: © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright). The attribution is added to every site automatically. Geocoding uses Nominatim at 1 request per second, per its [usage policy](https://operations.osmfoundation.org/policies/nominatim/).
- Photos: Wikimedia Commons, limited to CC0, public domain, CC BY and CC BY-SA. The author and licence of every photo are listed on the page that shows it.
- Prices, visa rules and opening hours in generated plans are estimates as of the build date. Check them before travelling.

## Кратко по-русски

Навык для Claude Code и OpenAI Codex: исследует поездку и собирает сайт на русском языке с маршрутом по дням, картами, фотографиями и интерактивным бюджетом, карманным гидом и разговорником. Установите репозиторий по инструкции выше и опишите направление, даты, бюджет и интересы. Готовый сайт можно открыть локально или разместить на GitHub Pages; цены, визовые правила и часы работы нужно проверить перед поездкой.
