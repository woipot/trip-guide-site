#!/usr/bin/env python3
"""Geocode places with OpenStreetMap Nominatim (1 request/second, per their policy).
Usage: python3 -I geocode.py out.json  < places.tsv
places.tsv lines: key<TAB>query   (English names work best; add the city: "Chen Clan Ancestral Hall Guangzhou")
Prints the top 2 candidates per key so you can sanity-check, and merges the first hit into out.json as
{key: [lat, lon, "query"]} — the same shape as trip.json "points". Fix wrong hits by hand."""
import json, os, sys, time, urllib.parse, urllib.request
out = sys.argv[1]
res = json.load(open(out)) if os.path.exists(out) else {}
UA = {"User-Agent": "trip-guide-site/1.0 (personal trip planning)"}
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line.strip() or "\t" not in line: continue
    key, q = line.split("\t", 1)
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 2, "accept-language": "en"})
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    except Exception as e:
        print(key, "ERROR", e); time.sleep(2); continue
    if not d:
        print(key, "| NOT FOUND — try another spelling or the local-script name"); time.sleep(1.2); continue
    print(key, "|", " || ".join(f'{float(x["lat"]):.5f},{float(x["lon"]):.5f} {x["display_name"][:70]}' for x in d))
    res[key] = [round(float(d[0]["lat"]), 5), round(float(d[0]["lon"]), 5), q]
    time.sleep(1.2)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
