# trip-guide-site

A [Claude Code](https://claude.com/claude-code) skill that plans a trip and builds it as an interactive three-page travel site:

- **Plan**: hero photo, key facts, overview map, hotel picker, day cards with photo galleries, a timeline with distances and walking time between stops, an OpenStreetMap route map per day, Yandex and Google route links, upgrade options with price differences, and a live budget that recalculates as you choose.
- **Pocket guide**: one illustrated chapter per sight, with a story, 5–7 stations in walking order, a "find on site" checklist, did-you-know facts and a tip. Chapters can be read aloud or followed step by step like an audio guide, and work offline once the page is loaded.
- **Phrasebook**: categories, search, tap a phrase to show it in huge text, and speech playback.

Claude does the research and writing. Parallel "guide" sub-agents write and fact-check the chapters and pick freely licensed photos. The bundled Python scripts handle geocoding, map data, photo licensing and credits, the maps and the final HTML.

> The generated UI text is in **Russian**, and prices convert from local currency to a home currency of your choice. To produce sites in another language, translate the strings in `scripts/build_site.py` and `assets/*.js`.

## Install

```bash
git clone https://github.com/<you>/trip-guide-site ~/.claude/skills/trip-guide-site
```

Restart Claude Code. The skill triggers on requests like "plan a 10-day trip to Istanbul, hotel up to €100/night" or "хочу поехать в Гуанчжоу на неделю, составь программу".

## Requirements

- Claude Code with web search and sub-agents. The Artifact tool is optional and is used to publish a private shareable page.
- Python 3.9+ (standard library only).
- Image compression uses `sips` (built into macOS) or [Pillow](https://pypi.org/project/Pillow/) on other systems.
- Internet access to OpenStreetMap Nominatim and Overpass, and to Wikimedia Commons.

## How it works

1. A short brief, filled in from `references/defaults.md` where the user leaves gaps.
2. Research of the facts that can wreck a trip: visa, money, connectivity, closures, customs (`references/research-checklist.md`).
3. The program is agreed as a table in chat before anything heavy is built.
4. Data gathering:
   - `scripts/geocode.py`: coordinates from Nominatim;
   - `scripts/osm_fetch.py`: water, parks and metro layers;
   - `scripts/commons_search.py` and `scripts/commons_fetch.py`: freely licensed photos with credits;
   - `scripts/contact_sheet.py`: a grid of candidate photos to review visually.
5. Guide chapters from parallel agents, using the prompt in `references/guide-agents.md`.
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
