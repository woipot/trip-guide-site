#!/usr/bin/env python3
"""Download map layers (water, parks, subway lines) for a bounding box from the Overpass API.
Usage: python3 -I osm_fetch.py <out_dir> <south> <west> <north> <east> [--rivers-only] [--force]
Writes out_dir/water.json, parks.json, subway.json ({"elements": [...]}, Overpass 'out geom').
Use --rivers-only for big regional boxes (> ~0.3°): it keeps only river polygons, which is much lighter.
Overpass is often busy: the script retries several mirrors with pauses. Layers already on disk are skipped
(re-run later to fill a failed layer; --force refetches everything). Keep boxes as small as the days need."""
import json, os, sys, time, urllib.parse, urllib.request
out, s, w, n, e = sys.argv[1], *sys.argv[2:6]
rivers_only = "--rivers-only" in sys.argv
bb = f"({s},{w},{n},{e})"
water = (f'way["natural"="water"]["water"="river"]{bb};relation["natural"="water"]["water"="river"]{bb};' if rivers_only else
         f'way["natural"="water"]{bb};relation["natural"="water"]["water"~"river|lake|reservoir"]{bb};way["waterway"="riverbank"]{bb};')
Q = {
    "water": f"[out:json][timeout:180];({water});out geom qt;",
    "parks": f'[out:json][timeout:180];(way["leisure"~"park|nature_reserve"](if:length()>1200){bb};relation["leisure"~"park|nature_reserve"]{bb};);out geom qt;',
    "subway": f'[out:json][timeout:180];(way["railway"~"subway|light_rail"]{bb};);out geom qt;',
}
EPS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
       "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
os.makedirs(out, exist_ok=True)
for name, q in Q.items():
    if os.path.exists(os.path.join(out, name + ".json")) and "--force" not in sys.argv:
        print(name, "already present, skipped"); continue
    ok = False
    for attempt in range(8):
        ep = EPS[attempt % len(EPS)]
        try:
            req = urllib.request.Request(ep, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "trip-guide-site/1.0"})
            raw = urllib.request.urlopen(req, timeout=240).read()
            d = json.loads(raw)
            if "elements" in d:
                json.dump({"elements": d["elements"]}, open(os.path.join(out, name + ".json"), "w"))
                print(name, len(d["elements"]), "elements from", ep.split("/")[2]); ok = True; break
        except Exception as ex:
            print(name, "retry", attempt + 1, ep.split("/")[2], str(ex)[:60])
        time.sleep(15)
    if not ok: print(name, "FAILED — re-run this command later to fetch it; the map renders without it meanwhile")
