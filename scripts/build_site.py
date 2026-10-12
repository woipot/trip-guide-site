#!/usr/bin/env python3
"""Build the three-page trip site from a trip folder.

Usage: python3 -I build_site.py <trip_dir> <out_dir>

trip_dir layout (see references/trip-json.md):
  trip.json            structured data: days, points, options, hotels, phrases...
  sections/*.html      free HTML blocks placed after the day plan, in file-name order.
                       Tokens they may contain: {{DISHES}} {{SOUVENIRS}} {{BUDGET}}
  guide/*.json         guide chapters (arrays), see references/guide-chapter.md
  osm/<layer>/         water.json parks.json subway.json from osm_fetch.py
  credits.json         {slug: {title, page, license, artist}} for out/img/<slug>.jpg
  credits_g.json       {commons title: {file, title, page, license, artist}} for out/img/g/
out_dir: gets <main_file> (fragment for the Artifact tool), index.html (standalone copy for local viewing or
         static hosting), guide.html, phrases.html; images must already be in out_dir/img.
"""
import glob, html, json, math, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from maps import load_water, load_lines, render  # noqa: E402

esc = html.escape
TRIP, OUT = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(TRIP, "trip.json")))
ASSETS = os.path.join(HERE, "..", "assets")
CSS = open(os.path.join(ASSETS, "style.css")).read()
R = T["currency"]["rate"]; LOC = T["currency"]["local"]; HOME = T["currency"]["home"]
THOUS = T["currency"].get("thousand", "тыс.")
MAIN = T.get("main_file", "trip.html")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Onest:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Noto+Serif+SC:wght@600;900&display=swap">')
P = {k: tuple(v) for k, v in T["points"].items()}  # key -> [lat, lon, google query]

# ---------- helpers ----------
def nf(x): return f"{int(round(x)):,}".replace(",", " ")
def kfmt(v):
    v = v / 1000
    return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 10 else f"{v:.0f}").replace(".", ",")
def home_range(lo, hi):
    a, b = kfmt(lo * R), kfmt(hi * R)
    return f"{a}–{b} {THOUS} {HOME}" if a != b else f"{a} {THOUS} {HOME}"
def km(x): return f"{int(round(x * 1000 / 50) * 50)} м" if x < 1 else f"{x:.1f} км".replace(".", ",")
def r5(m): return max(5, int(round(m / 5.0)) * 5)
def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b; p = math.pi / 180
    h = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))

def leg_html(d_air, override):
    route = d_air * 1.3; walk = 0.0
    if override:
        text, w = (override if isinstance(override, list) else (override, 0.0)); walk = float(w)
        info, kind = text, ("walk" if walk else "ride")
    elif route <= 1.8:
        info, walk, kind = f"~{r5(route / 4.5 * 60)} мин пешком", route, "walk"
    elif route <= 5:
        info, kind = f"такси ~{r5(5 + route / 20 * 60)} мин или ~{r5(route / 4.5 * 60)} мин пешком", "ride"
    else:
        info, kind = f"метро или такси ~{r5(10 + route / 28 * 60)} мин", "ride"
    return f'<li class="leg {kind}"><span class="legline"></span><span class="legtxt"><b>{km(route)}</b> · {esc(info)}</span></li>', walk

USED_IMG = set()
def fig(slug, cap, eager=False):
    USED_IMG.add(slug)
    lazy = "" if eager else ' loading="lazy"'
    return f'<figure><img src="img/{slug}.jpg" alt="{esc(cap)}"{lazy}><figcaption>{esc(cap)}</figcaption></figure>'

def choice_html(name, opts, label):
    base = (opts[0]["lo"] + opts[0]["hi"]) / 2
    out = [f'<div class="choice" role="radiogroup" aria-label="{esc(label)}">']
    for i, o in enumerate(opts):
        delta = ((o["lo"] + o["hi"]) / 2 - base) * R
        d = "базовый" if i == 0 else "без доплаты" if abs(delta) < 50 else (f"+ ≈{nf(round(delta / 100) * 100)} {HOME}" if delta > 0 else f"− ≈{nf(round(-delta / 100) * 100)} {HOME}")
        out.append(f'<label class="opt"><input type="radio" name="{name}" id="{name}-{i}" value="{i}" data-lo="{o["lo"]}" data-hi="{o["hi"]}" data-walk="{o.get("walk", 0)}"{" checked" if i == 0 else ""}>'
                   f'<span class="ot">{esc(o["title"])}</span><span class="op">{esc(o["price"])}</span><span class="on">{esc(o["note"])}</span><span class="od">{d}</span></label>')
    return "".join(out) + "</div>"

# ---------- guide data ----------
GUIDE = []
for fp in sorted(glob.glob(os.path.join(TRIP, "guide", "*.json"))):
    GUIDE += json.load(open(fp))
GM = {g["id"]: g for g in GUIDE}
GUIDE_OF = T.get("guide_map", {})
ORDER = T.get("guide_order") or [g["id"] for g in GUIDE]

# ---------- map layers ----------
LAYERS = {}
def layer(name):
    if name not in LAYERS:
        d = os.path.join(TRIP, "osm", name)
        f = lambda n: os.path.join(d, n)
        LAYERS[name] = (load_water(f("water.json")) if os.path.exists(f("water.json")) else [],
                        load_water(f("parks.json")) if os.path.exists(f("parks.json")) else [],
                        load_lines(f("subway.json")) if os.path.exists(f("subway.json")) else [])
    return LAYERS[name]

# ---------- days ----------
days_html, daylist, ov_stops = [], [], []
tot_days = [0, 0]
base_key = T.get("base")
for d in T["days"]:
    n_ = d["n"]; tr = d.get("transport", [0, 0])
    flo, fhi, fwalk = tr[0], tr[1], 0.0
    olo, ohi, owalk = 0, 0, 0.0
    pins, items = [], []
    start = d.get("start", base_key if d.get("layer", "default") == "default" else None)
    prev = (P[start][0], P[start][1]) if start else None
    n = 0
    for si, s in enumerate(d["stops"]):
        pin = s.get("pin")
        if pin:
            n += 1; lat, lon, q = P[pin]
            pins.append(dict(lat=lat, lon=lon, label=s.get("label"), n=n, en=q))
            if prev is not None or s.get("leg"):
                lh, w = leg_html(hav(prev, (lat, lon)) if prev else 0, s.get("leg"))
                if prev is None:  # override without a known start: hide the distance
                    lh = re.sub(r"<b>.*?</b> · ", "", lh)
                items.append(lh); fwalk += w
            prev = (lat, lon)
            dot = f'<span class="dot pin">{n}</span>'
        else:
            dot = '<span class="dot plain"></span>'
        fwalk += s.get("walk", 0)
        if s.get("cost"): flo += s["cost"][0]; fhi += s["cost"][1]
        pr = f'<span class="price">{esc(s["price"])}</span>' if s.get("price") and not s.get("opts") else ""
        ch = ""
        if s.get("opts"):
            ch = choice_html(f"d{n_}s{si}", s["opts"], s["name"])
            o = s["opts"][0]; olo += o["lo"]; ohi += o["hi"]; owalk += o.get("walk", 0)
            pr = '<span class="price var">есть варианты</span>'
        gid = GUIDE_OF.get(pin or "") or s.get("guide")
        gl = f'<a class="glink" href="guide.html#g-{gid}">Гид: что смотреть →</a>' if gid in GM else ""
        items.append(f'<li class="stop">{dot}<div class="sbody"><div class="row1"><span class="time">{esc(s.get("t", ""))}</span>{pr}</div>'
                     f'<b>{esc(s["name"])}</b><span class="zh">{esc(s.get("zh", ""))}</span><p>{esc(s.get("text", ""))}</p>{gl}{ch}</div></li>')
    dlo, dhi, dwalk = flo + olo, fhi + ohi, fwalk + owalk
    tot_days[0] += dlo; tot_days[1] += dhi
    extra = [dict(lat=P[d["hotel"]][0], lon=P[d["hotel"]][1], label=T.get("hotel_label", "Отель"))] if d.get("hotel") else []
    mapsvg = links = ""
    if pins:
        L = layer(d.get("layer", "default"))
        mapsvg = render(L[0], pins, extra, parks=L[1], metro=L[2], route=not d.get("noroute"), title=f"Карта дня {n_}")
        ya = "https://yandex.ru/maps/?" + urllib.parse.urlencode({"rtext": "~".join(f"{p['lat']},{p['lon']}" for p in pins), "rtt": d.get("mode", "mt")})
        gg = "https://www.google.com/maps/dir/" + "/".join(urllib.parse.quote_plus(p["en"]) for p in pins)
        links = f'<div class="map-links"><a href="{esc(ya)}" target="_blank" rel="noopener">Маршрут в Яндекс Картах ↗</a><a href="{esc(gg)}" target="_blank" rel="noopener">Google Maps ↗</a></div>'
        if d.get("layer", "default") == "default" and n_ not in T.get("overview", {}).get("exclude_days", []):
            ov_stops.append(dict(lat=sum(p["lat"] for p in pins) / len(pins), lon=sum(p["lon"] for p in pins) / len(pins), n=n_,
                                 label=T.get("overview", {}).get("labels", {}).get(str(n_))))
    wk = f"{dwalk:.1f}".replace(".", ",")
    chips = f'<span class="eyebrow">{esc(d.get("date", ""))}</span><span class="chip">{esc(d.get("area", ""))}</span><span class="chip walk" data-walkchip>пешком ≈ {wk} км</span>'
    for c in d.get("chips", []):
        chips += f'<span class="chip {esc(c.get("tone", ""))}">{esc(c["text"])}</span>'
    ph = d.get("photos", [])
    gallery = (f'<div class="gallery g{min(len(ph), 3)}">' + "".join(fig(s_, c, eager=(n_ == 1)) for s_, c in ph[:3]) + "</div>") if ph else ""
    cost = (f'<div class="cost"><div><span class="lbl">Расходы за день на двоих</span><span class="v" data-cost>≈ {nf(dlo)}–{nf(dhi)} {LOC} · {home_range(dlo, dhi)}</span></div>'
            f'<div><span class="lbl">Пешком за день</span><span class="v" data-walk>≈ {wk} км</span></div></div>')
    frame = f'<div class="map-frame">{mapsvg}</div>' if mapsvg else ""
    days_html.append(f'<article class="day" id="day{n_}" data-flo="{flo}" data-fhi="{fhi}" data-fwalk="{fwalk:.2f}"><div class="day-head"><div class="day-no">{n_:02d}</div><div><div class="meta">{chips}</div>'
                     f'<h3>{esc(d["title"])}</h3><p class="lede">{esc(d.get("lede", ""))}</p></div></div>{gallery}'
                     f'<div class="day-body"><ol class="timeline">{"".join(items)}</ol><aside class="map-card">{frame}{links}{cost}</aside></div></article>')
    daylist.append(f'<li><a href="#day{n_}"><span class="num">{n_:02d}</span><span><span class="d">{esc(d.get("date", ""))} · {esc(d.get("area", ""))}</span><span class="t">{esc(d["title"])}</span></span></a></li>')

L0 = layer("default")
overview = render(L0[0], ov_stops, ([dict(lat=P[base_key][0], lon=P[base_key][1], label=T.get("hotel_label", "Отель"))] if base_key else []),
                  parks=L0[1], metro=L0[2], route=False, title="Карта всей поездки", pad=0.10, max_aspect=1.15) if ov_stops else ""

# ---------- hotels ----------
hotel_blocks, hlo, hhi = [], 0, 0
for gi, grp in enumerate(T.get("hotels", [])):
    nights = grp["nights"]; name = f"hotel{gi}"
    out = [f'<h3 class="sub-h">{esc(grp["heading"])}</h3><div class="choice hotels-choice" role="radiogroup" aria-label="{esc(grp["heading"])}" data-nights="{nights}">']
    rec_i = next((i for i, o in enumerate(grp["options"]) if o.get("rec")), 0)
    for i, o in enumerate(grp["options"]):
        rec = '<span class="rec">рекомендую</span>' if o.get("rec") else ""
        out.append(f'<label class="opt"><input type="radio" name="{name}" id="{name}-{i}" value="{i}" data-lo="{o["lo"]}" data-hi="{o["hi"]}"{" checked" if i == rec_i else ""}>'
                   f'<span class="ot">{esc(o["title"])}{rec}</span><span class="op">{nf(o["lo"])}–{nf(o["hi"])} {LOC} / ночь</span>'
                   f'<span class="on">{esc(o.get("sub", ""))}. {esc(o.get("note", ""))}</span><span class="od">{nights} ноч. ≈ {home_range(o["lo"] * nights, o["hi"] * nights)}</span></label>')
    out.append("</div>")
    hotel_blocks.append("".join(out))
    hlo += grp["options"][rec_i]["lo"] * nights; hhi += grp["options"][rec_i]["hi"] * nights
H = T.get("hotel_section", {})
hotel_section = (f'<section class="block" id="hotel"><div class="sec-head"><span class="eyebrow">Где жить</span><h2>{esc(H.get("title", "Отель: выберите уровень"))}</h2>'
                 f'<p>{esc(H.get("intro", ""))}</p></div>{"".join(hotel_blocks)}'
                 f'<div class="combo"><b>Все отели</b><span data-hoteltotal>≈ {home_range(hlo, hhi)}</span></div>'
                 f'{H.get("note_html", "")}</section>') if T.get("hotels") else ""

# ---------- budget ----------
FIX = T.get("fixed_costs", [])
fix_lo = sum(f["lo"] for f in FIX if f.get("lo") is not None); fix_hi = sum(f["hi"] for f in FIX if f.get("hi") is not None)
tot = (fix_lo + (hlo + tot_days[0]) * R, fix_hi + (hhi + tot_days[1]) * R)
def tr_(lo, hi): return f"≈ {round(lo / 1000)}–{round(hi / 1000)} {THOUS} {HOME}"
colors = ["b1", "b4", "b5"]
bars = [f'<div class="b2" data-bar="hotel" style="flex:{(hlo + hhi) * R / 2:.0f}"><span>Отели</span></div>',
        f'<div class="b3" data-bar="days" style="flex:{sum(tot_days) * R / 2:.0f}"><span>Еда, билеты, транспорт</span></div>']
rows = []
for i, f in enumerate(FIX):
    if f.get("lo") is not None:
        bars.insert(0 if i == 0 else len(bars), f'<div class="{colors[min(i, 2)]}" style="flex:{(f["lo"] + f["hi"]) / 2:.0f}"><span>{esc(f.get("bar", ""))}</span></div>')
    rows.append(f'<tr><td>{esc(f["label"])}</td><td>{esc(f.get("note", ""))}</td><td class="num">{nf(f["lo"]) if f.get("lo") is not None else "—"}</td><td class="num">{nf(f["hi"]) if f.get("hi") is not None else "—"}</td></tr>')
rows.insert(1 if FIX else 0, f'<tr><td>Отели</td><td data-hotelcalc>по выбору в разделе «Где жить»</td><td class="num" data-c="hotel-lo">{nf(hlo * R)}</td><td class="num" data-c="hotel-hi">{nf(hhi * R)}</td></tr>')
rows.insert(2 if FIX else 1, f'<tr><td>Еда, билеты, транспорт</td><td>сумма по дням с вашими вариантами</td><td class="num" data-c="days-lo">{nf(tot_days[0] * R)}</td><td class="num" data-c="days-hi">{nf(tot_days[1] * R)}</td></tr>')
ndays = len(T["days"])
budget = (f'<div class="big-total"><b data-total>{tr_(*tot)}</b><span style="color:var(--muted)">за {ndays} дн. на двоих, без покупок</span></div>'
          f'<div class="bar" role="img" aria-label="Структура бюджета">{"".join(bars)}</div>'
          f'<div class="tbl"><table><thead><tr><th>Статья</th><th>Расчёт</th><th class="num">{HOME}, от</th><th class="num">{HOME}, до</th></tr></thead><tbody>{"".join(rows)}'
          f'<tr class="total"><td>Итого</td><td>без покупок</td><td class="num" data-c="tot-lo">{nf(tot[0])}</td><td class="num" data-c="tot-hi">{nf(tot[1])}</td></tr></tbody></table></div>')
sticky = (f'<div class="sticky" id="sticky"><div class="sticky-in"><div><span class="eyebrow">Ваш вариант на двоих</span><b data-total>{tr_(*tot)}</b></div>'
          f'<div class="s-meta"><span data-upg>улучшений: 0</span><a href="#budget">Бюджет ↓</a><button type="button" id="reset">Сбросить</button></div></div></div>')

# ---------- dishes / souvenirs ----------
dishes = "".join(f'<figure class="dish"><div class="ph"><img src="img/{s}.jpg" alt="{esc(r)}" loading="lazy"></div><figcaption><span class="zh">{esc(z)}</span><span class="r">{esc(r)}</span><small>{esc(t)}</small></figcaption></figure>' for s, z, r, t in T.get("dishes", []))
USED_IMG.update(s for s, *_ in T.get("dishes", []))
souv = "".join(f'<li class="souv"><div><b>{esc(n)}</b> <span class="zh">{esc(z)}</span><small>{esc(w)}</small><p>{esc(tip)}</p></div><span class="p">{esc(p)}</span></li>' for n, z, p, w, tip in T.get("souvenirs", []))

# ---------- sections ----------
sections_html, toc = [], []
for fp in sorted(glob.glob(os.path.join(TRIP, "sections", "*.html"))):
    s = open(fp).read().replace("{{DISHES}}", dishes).replace("{{SOUVENIRS}}", souv).replace("{{BUDGET}}", budget)
    for m in re.finditer(r'<section class="block" id="([\w-]+)"[^>]*data-nav="([^"]+)"', s):
        toc.append((m.group(1), m.group(2)))
    for m in re.finditer(r'src="img/([\w-]+)\.jpg"', s):
        USED_IMG.add(m.group(1))
    sections_html.append(s)

# ---------- credits ----------
CR = json.load(open(os.path.join(TRIP, "credits.json"))) if os.path.exists(os.path.join(TRIP, "credits.json")) else {}
CRG = json.load(open(os.path.join(TRIP, "credits_g.json"))) if os.path.exists(os.path.join(TRIP, "credits_g.json")) else {}
def credit_line(m):
    name = m["title"].replace("File:", "").rsplit(".", 1)[0]
    if len(name) > 60: name = name[:57] + "…"
    return f'<div><a href="{esc(m["page"])}" target="_blank" rel="noopener">{esc(name)}</a> — {esc(m.get("artist") or "автор не указан")}, {esc(m["license"])}</div>'

# ---------- main page ----------
hero = T["hero"]; USED_IMG.add(hero["image"])
SITENAV = lambda cur: '<nav class="sitenav" aria-label="Страницы">' + "".join(
    f'<a href="{h}"{" aria-current=" + chr(34) + "page" + chr(34) if k == cur else ""}>{t}</a>' for k, h, t in
    (("plan", "#" if cur == "plan" else "index.html", "План поездки"), ("guide", "guide.html", "Карманный гид"), ("phrases", "phrases.html", "Словарик"))) + "</nav>"
facts = "".join(f'<div><span class="eyebrow">{esc(f["label"])}</span><b>{esc(f["value"])}</b><span class="s">{esc(f.get("note", ""))}</span></div>' for f in T.get("facts", []))
toc_html = "".join(f'<a href="#{i}">{esc(l)}</a>' for i, l in ([("route", "Маршрут")] if overview else []) + ([("hotel", "Отели")] if hotel_section else []) + [("plan", "По дням")] + toc)
OV = T.get("overview", {})
route_sec = (f'<section class="block" id="route"><div class="sec-head"><span class="eyebrow">Маршрут</span><h2>{esc(OV.get("title", "Вся поездка на одной карте"))}</h2><p>{esc(OV.get("text", ""))}</p></div>'
             f'<div class="overview"><div class="map-frame">{overview}<p class="map-note">Схема по данным OpenStreetMap. Квадрат — отель, кружки — районы, где проходит каждый день. Серые линии — метро, зелёным отмечены парки.</p></div>'
             f'<ol class="daylist">{"".join(daylist)}</ol></div></section>') if overview else ""
cfg = {"rate": R, "home": HOME, "local": LOC, "thousand": THOUS, "fixed": [fix_lo, fix_hi], "days": ndays, "key": "trip-" + re.sub(r"\W+", "-", T["title"]).lower()[:30]}
main_js = open(os.path.join(ASSETS, "main.js")).read()
credits_main = "".join(credit_line(CR[s]) for s in sorted(USED_IMG) if s in CR)
main = f'''<title>{esc(T["title"])}</title>
{FONTS}
<style>{CSS}</style>
<header class="hero"><img class="bg" src="img/{hero["image"]}.jpg" alt="{esc(hero.get("alt", ""))}">
<div class="inner"><div><div class="kicker">{esc(hero.get("kicker", ""))}</div><h1>{esc(hero["h1"])}</h1><p class="sub">{esc(hero.get("sub", ""))}</p></div>
{f'<div class="vert" aria-hidden="true">{esc(hero["glyph"])}</div>' if hero.get("glyph") else ""}</div></header>
<div class="wrap">
<div class="facts">{facts}</div>
{SITENAV("plan")}
<nav class="toc" aria-label="Разделы">{toc_html}</nav>
{route_sec}
{hotel_section}
<section class="block" id="plan" style="gap:0"><div class="sec-head"><span class="eyebrow">Программа</span><h2>По дням</h2>
<p>Номера в расписании совпадают с номерами на карте дня. Между точками указаны расстояние и как добраться: расстояние по прямой с запасом 30% на улицы, время примерное. Там, где за небольшую доплату есть вариант заметно лучше, его можно выбрать: стоимость дня и бюджет пересчитаются. Выбор сохраняется в этом браузере.</p></div>
{"".join(days_html)}</section>
{"".join(sections_html)}
<footer>{T.get("footer_html", "")}
<p>Карты: данные © участники <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>, лицензия ODbL. Маршруты на картах схематичные: точки соединены прямыми линиями, а не реальными дорогами.</p>
<p>Фотографии с Wikimedia Commons:</p><div class="credits">{credits_main}</div></footer>
</div>
{sticky}
<script>window.TRIP_CFG = {json.dumps(cfg, ensure_ascii=False)};</script>
<script>{main_js}</script>
'''
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, MAIN), "w").write(main)
# standalone copy for opening locally or static hosting (GitHub Pages etc.); not for the Artifact upload
open(os.path.join(OUT, "index.html"), "w").write(
    f'<!doctype html><html lang="{T.get("lang", "ru")}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
    '<style>html{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + main + '</body></html>')

# ---------- guide page ----------
def img_src(ref):
    if not ref: return None, None
    if ref.startswith("local:"):
        k = ref[6:]; return f"img/{k}.jpg", ("l", k)
    m = CRG.get(ref)
    return (f"img/g/{m['file']}", ("g", ref)) if m else (None, None)

def page(title, body, js):
    return (f'<!doctype html><html lang="{T.get("lang", "ru")}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'<title>{esc(title)}</title>{FONTS}<style>html{{color-scheme:light}}body{{margin:0;padding-block:env(safe-area-inset-top,0px) env(safe-area-inset-bottom,0px)}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>'
            f'<style>{CSS}</style></head><body>{body}<script>{js}</script></body></html>')

day_of = {gid: 0 for gid in T.get("guide_intro", [])}
for d in T["days"]:
    for s in d["stops"]:
        gid = GUIDE_OF.get(s.get("pin") or "") or s.get("guide")
        if gid and gid not in day_of: day_of[gid] = d["n"]
day_titles = {d["n"]: d["title"] for d in T["days"]}
glist = [GM[k] for k in ORDER if k in GM and k in day_of]
gcred = []
by_day = {}
for g in glist: by_day.setdefault(day_of[g["id"]], []).append(g)
gtoc, gbody = [], []
for dn in sorted(by_day):
    head = "Перед поездкой" if dn == 0 else f"День {dn} · {day_titles.get(dn, '')}"
    cards = []
    for g in by_day[dn]:
        hsrc, hc = img_src(g.get("hero"))
        if hc and hc not in gcred: gcred.append(hc)
        thumb = f'<img src="{hsrc}" alt="" loading="lazy">' if hsrc else '<span class="noimg">◆</span>'
        cards.append(f'<a class="tcard" href="#g-{g["id"]}">{thumb}<span>{esc(g["title"])}</span></a>')
        sts = []
        for k, s in enumerate(g.get("stations", [])):
            isrc, ic = img_src(s.get("image"))
            if ic and ic not in gcred: gcred.append(ic)
            figure = (f'<figure class="sfig"><img src="{isrc}" alt="{esc(s.get("caption") or s["title"])}" loading="lazy">'
                      + (f'<figcaption>{esc(s["caption"])}</figcaption>' if s.get("caption") else "") + '</figure>') if isrc else ""
            sts.append(f'<li class="gst" data-n="{k + 1}"><span class="gwhere">{esc(s.get("where", ""))}</span><h4>{esc(s["title"])}</h4>{figure}<p>{esc(s["text"])}</p></li>')
        st = g.get("story")
        story = f'<div class="story"><span class="eyebrow">История</span><h4>{esc(st.get("title", ""))}</h4><p>{esc(st.get("text", ""))}</p></div>' if st else ""
        dyk = g.get("didyouknow") or ([g["fact"]] if g.get("fact") else [])
        find = "".join(f'<li><label><input type="checkbox" id="gf-{g["id"]}-{k}"><span>{esc(x)}</span></label></li>' for k, x in enumerate(g.get("find", [])))
        nst = len(g.get("stations", []))
        herofig = (f'<figure class="chero"><img src="{hsrc}" alt="{esc(g.get("hero_caption") or g["title"])}" loading="lazy">'
                   + (f'<figcaption>{esc(g["hero_caption"])}</figcaption>' if g.get("hero_caption") else "") + '</figure>') if hsrc else ""
        gbody.append(f'''<article class="chap" id="g-{g["id"]}"><details{" open" if dn == 0 else ""}>
<summary><span class="sthumb">{thumb}</span><span class="stext"><span class="eyebrow">{esc(head)}</span><span class="ctitle">{esc(g["title"])} <span class="zh">{esc(g.get("zh", ""))}</span></span>
<span class="hook">{esc(g.get("hook") or "")}</span><span class="gmeta">{esc(g.get("time", ""))} · {nst} {"остановки" if 2 <= nst <= 4 else "остановок"}</span></span><span class="sopen" aria-hidden="true"></span></summary>
<div class="cbody">{herofig}<p class="cintro">{esc(g.get("intro", ""))}</p>
<div class="gtools"><button type="button" class="gbtn gplay">▶ Слушать</button><button type="button" class="gbtn gmode" aria-pressed="false">Пошаговый режим</button></div>
{story}<ol class="gstations">{"".join(sts)}</ol>
<div class="gnav" hidden><button type="button" class="gbtn gprev">← Назад</button><span class="gpos"></span><button type="button" class="gbtn gnext">Дальше →</button></div>
<div class="gextra"><div class="gfind"><span class="eyebrow">Найдите на месте</span><ul>{find}</ul></div>
<div class="gfact"><span class="eyebrow">Знаете ли вы</span>{"".join("<p>" + esc(x) + "</p>" for x in dyk)}<span class="eyebrow">Совет</span><p>{esc(g.get("tip", ""))}</p></div></div>
</div></details></article>''')
    gtoc.append(f'<div class="tday"><span class="eyebrow">{esc(head)}</span><div class="tgrid">{"".join(cards)}</div></div>')
    gbody.insert(len(gbody) - len(by_day[dn]), f'<h2 class="dayh">{esc(head)}</h2>')
for kind, k in gcred:
    if kind == "l": USED_IMG.add(k)
gcredits = "".join(credit_line(CR[k] if kind == "l" else CRG[k]) for kind, k in gcred if (CR.get(k) if kind == "l" else CRG.get(k)))
G = T.get("guide_page", {})
guide_body = f'''<div class="wrap">{SITENAV("guide")}
<header class="ghead"><span class="eyebrow">{esc(G.get("eyebrow", "Карманный гид"))}</span><h1>{esc(G.get("title", "Экскурсия без гида"))}</h1>
<p>По каждому месту программы: история, остановки в порядке обхода с фото, что найти глазами и неожиданные факты. Читайте или слушайте: кнопка «Слушать» использует голос вашего телефона. Пошаговый режим показывает по одной остановке, как аудиогид.</p>
<p class="note"><b>Без интернета.</b> Откройте эту страницу заранее, пока есть сеть, пролистайте до конца, чтобы подгрузились фото, и не закрывайте вкладку. Тексты останутся доступны и без сети.</p></header>
<nav class="gtoc2" aria-label="Главы">{"".join(gtoc)}</nav>
<div class="chapters">{"".join(gbody)}</div>
<footer><p>Ключевые факты сверены с открытыми источниками. Фотографии с Wikimedia Commons:</p><div class="credits">{gcredits}</div></footer></div>'''
if glist:
    open(os.path.join(OUT, "guide.html"), "w").write(page("Карманный гид", guide_body, open(os.path.join(ASSETS, "guide.js")).read()))

# ---------- phrases page ----------
PH = T.get("phrases", [])
if PH:
    tabs = '<button type="button" class="ptab" data-cat="all" aria-pressed="true">Все</button>' + "".join(
        f'<button type="button" class="ptab" data-cat="c{i}" aria-pressed="false">{esc(c["cat"])}</button>' for i, c in enumerate(PH))
    spk = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/><path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
    items = ""
    for i, c in enumerate(PH):
        for ru, native, latin, reading in c["items"]:
            items += (f'<li class="phrase" data-cat="c{i}" data-lang="{esc(c.get("lang", T.get("speech_lang", "en-US")))}" data-search="{esc((ru + " " + reading + " " + latin).lower())}">'
                      f'<button type="button" class="pshow" aria-label="Показать крупно: {esc(ru)}"><span class="pru">{esc(ru)}</span><span class="pzh">{esc(native)}</span>'
                      f'<span class="ppy">{esc(latin)} · <i>{esc(reading)}</i></span></button><button type="button" class="psay" aria-label="Произнести">{spk}</button></li>')
    nums = "".join(f'<div><b>{esc(a)}</b><span class="zh">{esc(b)}</span><small>{esc(c)} · {esc(d)}</small></div>' for a, b, c, d in T.get("numbers", []))
    PP = T.get("phrases_page", {})
    pbody = f'''<div class="wrap">{SITENAV("phrases")}
<header class="ghead"><span class="eyebrow">Словарик</span><h1>{esc(PP.get("title", "Фразы, которые реально пригодятся"))}</h1><p>{esc(PP.get("intro", "Нажмите на фразу, чтобы показать её собеседнику крупно. Значок динамика читает фразу голосом телефона. Русская транскрипция приблизительная."))}</p></header>
<div class="ptools"><input type="search" id="psearch" placeholder="Поиск по фразам…" aria-label="Поиск по словарику"><div class="ptabs">{tabs}</div></div>
<ul class="plist">{items}</ul>
{('<h2 class="dayh">Цифры</h2><div class="nums">' + nums + '</div>') if nums else ""}
{PP.get("extra_html", "")}</div>
<div class="pbig" id="pbig" hidden role="dialog" aria-modal="true" aria-label="Фраза крупно"><button type="button" class="pclose" aria-label="Закрыть">✕</button><div class="pbig-zh"></div><div class="pbig-py"></div><div class="pbig-ru"></div><p class="pbig-hint">Покажите экран собеседнику. Нажмите в любом месте, чтобы закрыть.</p></div>'''
    open(os.path.join(OUT, "phrases.html"), "w").write(page("Словарик", pbody, open(os.path.join(ASSETS, "phrases.js")).read()))

# ---------- report ----------
gfiles = sorted({CRG[k]["file"] for kind, k in gcred if kind == "g" and k in CRG})
missing = [s for s in USED_IMG if not os.path.exists(os.path.join(OUT, "img", s + ".jpg"))]
missing += [f for f in gfiles if not os.path.exists(os.path.join(OUT, "img", "g", f))]
json.dump({"images": sorted(USED_IMG), "guide_images": gfiles}, open(os.path.join(TRIP, "used_images.json"), "w"), indent=1)
print(f"built {MAIN} ({os.path.getsize(os.path.join(OUT, MAIN)) // 1024} KB), guide chapters {len(glist)}, phrases {sum(len(c['items']) for c in PH)}")
print(f"budget total ≈ {round(tot[0] / 1000)}–{round(tot[1] / 1000)} {THOUS} {HOME}; days {nf(tot_days[0])}–{nf(tot_days[1])} {LOC}")
if missing: print("MISSING IMAGES:", missing)
