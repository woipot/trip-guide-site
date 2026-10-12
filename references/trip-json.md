# Trip folder and trip.json

```
trip/
  trip.json            structured data (this file)
  sections/NN-x.html   free HTML sections after the day plan, in file-name order
  guide/*.json         guide chapters written by agents (arrays of chapter objects)
  osm/default/         water.json parks.json subway.json  (osm_fetch.py)
  osm/<other>/         extra map layer for a far-away area, referenced by day.layer
  credits.json         written by commons_fetch.py photos
  credits_g.json       written by commons_fetch.py guide
<out>/img/<slug>.jpg   plan-page photos;  <out>/img/g/*.jpg guide photos
```

Money: every `lo`/`hi`/`cost` in days, options and hotels is in **local currency for the whole party**. `fixed_costs` are in **home currency**. A complete real example: `assets/example-guangzhou/trip.json`.

## Top level

| key | meaning |
|---|---|
| `title` | page `<title>`, e.g. "Гуанчжоу на двоих" |
| `lang` | page language code, `ru` |
| `main_file` | file name of the main page, e.g. `guangzhou-trip.html` (published as the Artifact; served as `index.html`) |
| `hero` | `{image: slug, alt, kicker, h1, sub, glyph?}` — glyph = big vertical local-script name (optional) |
| `facts` | 4 items `{label, value, note}` shown under the hero (weather, visa, hotels, rate) |
| `currency` | `{local: "¥", home: "₽", rate: 12.5, thousand: "тыс."}` — rate = home per 1 local |
| `fixed_costs` | `[{label, note, lo, hi, bar}]` home currency; `lo/hi: null` → a "—" row (e.g. shopping) |
| `overview` | `{title, text, labels: {"5": "Фошань"}, exclude_days: []}` — days with a non-default layer are excluded automatically |
| `base` | point key of the main hotel; first leg of default-layer days starts here |
| `hotel_label` | label of the hotel square on maps |
| `points` | `{key: [lat, lon, "Google query"]}` — from geocode.py; the query feeds Google Maps route links |
| `hotel_section` | `{title, intro, note_html}` |
| `hotels` | groups `[{heading, nights, options: [{title, sub, lo, hi, note, rec?}]}]` — one radio group each; `rec: true` = default |
| `days` | see below |
| `guide_map` | `{point_key: guide_chapter_id}` — adds "Гид: что смотреть →" links and assigns chapters to days |
| `guide_order` | chapter ids in reading order |
| `guide_intro` | chapter ids shown under "Перед поездкой" (city intro) |
| `guide_page` | `{eyebrow, title}` |
| `dishes` | `[[slug, native, name, note]]` photo cards for `{{DISHES}}` |
| `souvenirs` | `[[name, native, price, where, tip]]` for `{{SOUVENIRS}}` |
| `speech_lang` | default speech language for phrases, e.g. `zh-CN`, `ja-JP`, `tr-TR` |
| `phrases` | `[{cat, lang, items: [[ru, native, latin/transliteration, ru reading]]}]` |
| `numbers` | `[[digit, native, latin, reading]]` |
| `phrases_page` | `{title, intro, extra_html}` |
| `footer_html` | sources paragraph(s) |

## Day

```json
{"n": 3, "date": "вс, 22 ноября", "area": "Юэсю · старый центр", "title": "…", "lede": "1–2 sentences",
 "photos": [["nanyue", "caption"], ["zhenhai", "caption"]],      // 1–3, first is big
 "hotel": "base",            // optional: draw hotel square on this day's map
 "layer": "sz",              // optional: map layer folder; omit for default
 "start": "szhotel",         // optional: point the first leg is measured from (default: base on default layer, none elsewhere)
 "mode": "mt",               // Yandex route mode: mt (transit), pd (walk), auto
 "transport": [30, 40],      // metro/taxi money not tied to a stop
 "chips": [{"text": "музеи закрыты", "tone": "gold"}],   // tones: "", gold, red
 "noroute": false,           // true = pins without the dashed route line (alternative options)
 "stops": [ … ]}
```

## Stop

```json
{"t": "18:00", "name": "Ужин в Wisca", "zh": "惠食佳", "text": "1–3 sentences",
 "pin": "wisca", "label": "Wisca",          // pin → numbered marker + distance leg from the previous pin
 "cost": [500, 800], "price": "2 × 250–400 ¥", // fixed cost (whole party) and its display text
 "walk": 1.5,                                // km walked inside the place
 "leg": "метро линии 3 ~25 мин",             // override the auto leg text; or ["text", walk_km]
 "guide": "city",                            // chapter id for stops without a pin
 "opts": [ {"title": "Обычный теплоход", "price": "120–200 ¥", "lo": 120, "hi": 200, "note": "what you get", "walk": 0}, … ]}
```
With `opts`, the first option is the default and its price counts in the total; don't also set `cost`. Deltas vs. the first option are shown automatically in home currency.

Auto legs: straight-line distance ×1.3; ≤1.8 km → walking time (counted into the day's walking km), ≤5 km → taxi or walk, else metro/taxi. Override legs for cable cars, ferries, trains and river crossings.
