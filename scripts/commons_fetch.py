#!/usr/bin/env python3
"""Download freely licensed images from Wikimedia Commons, compress them and record credits.

1) Page photos:   python3 -I commons_fetch.py photos <picks.tsv> <trip_dir> <out_dir>
   picks.tsv lines: slug<TAB>File title (without "File:")<TAB>width     e.g.  chen<TAB>Chen Clan Ancestral Hall 2025.06 02.jpg<TAB>1200
   -> out_dir/img/<slug>.jpg, credits merged into trip_dir/credits.json
2) Guide photos:  python3 -I commons_fetch.py guide <trip_dir> <out_dir>
   scans trip_dir/guide/*.json for "hero"/"image" refs that are Commons titles (not "local:x")
   -> out_dir/img/g/<slug>.jpg, credits in trip_dir/credits_g.json
Only CC0 / Public domain / CC BY / CC BY-SA are accepted. Compression: sips (macOS) or Pillow, JPEG ~q40-60."""
import glob, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "trip-guide-site/1.0 (personal use)"}
OK_LIC = re.compile(r"CC0|Public domain|^PD|CC BY", re.I)

def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for k in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception: time.sleep(5 * (k + 1))
    return None

def get(url):
    for k in range(5):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        except Exception: time.sleep(5 * (k + 1))
    return None

def compress(src, dst, width, quality=40):
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality), "-Z", str(width), src, "--out", dst], capture_output=True)
        if os.path.exists(dst): return
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB"); im.thumbnail((width, width * 3))
        im.save(dst, "JPEG", quality=max(quality + 20, 60), optimize=True, progressive=True); return
    except Exception:
        shutil.copy(src, dst)

def fetch(title, width, dst):
    d = api({"action": "query", "titles": "File:" + title, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": width, "format": "json"})
    pg = list(d["query"]["pages"].values())[0] if d else {}
    if "imageinfo" not in pg: return None, "not found"
    ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
    lic = m.get("LicenseShortName", {}).get("value", "")
    if not OK_LIC.search(lic): return None, "license " + lic
    data = get(ii["thumburl"])
    if not data: return None, "download"
    tmp = dst + ".src"; open(tmp, "wb").write(data); compress(tmp, dst, width); os.remove(tmp)
    art = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", ""))).strip()[:80]
    time.sleep(0.8)
    return {"title": pg["title"], "page": ii["descriptionurl"], "license": lic, "artist": art}, None

def slug_for(title):
    s = re.sub(r"[^A-Za-z0-9]+", "-", title.rsplit(".", 1)[0]).strip("-").lower()[:50]
    return (s or "img") + "-" + hashlib.md5(title.encode()).hexdigest()[:6]

mode = sys.argv[1]
if mode == "photos":
    picks, trip, out = sys.argv[2:5]
    cp = os.path.join(trip, "credits.json"); cr = json.load(open(cp)) if os.path.exists(cp) else {}
    os.makedirs(os.path.join(out, "img"), exist_ok=True)
    for line in open(picks):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2 or not parts[0].strip(): continue
        slug, title = parts[0], parts[1]; w = int(parts[2]) if len(parts) > 2 and parts[2] else 1200
        meta, err = fetch(title, w, os.path.join(out, "img", slug + ".jpg"))
        print(slug, "OK" if meta else "FAIL " + err)
        if meta: cr[slug] = meta; json.dump(cr, open(cp, "w"), ensure_ascii=False, indent=1)
elif mode == "guide":
    trip, out = sys.argv[2:4]
    cp = os.path.join(trip, "credits_g.json"); cr = json.load(open(cp)) if os.path.exists(cp) else {}
    os.makedirs(os.path.join(out, "img", "g"), exist_ok=True)
    refs = {}
    for fp in glob.glob(os.path.join(trip, "guide", "*.json")):
        for g in json.load(open(fp)):
            if g.get("hero") and not g["hero"].startswith("local:"): refs[g["hero"]] = 1400
            for s in g.get("stations", []):
                r = s.get("image")
                if r and not r.startswith("local:"): refs.setdefault(r, 1100)
    bad = []
    for title, w in refs.items():
        if title in cr and os.path.exists(os.path.join(out, "img", "g", cr[title]["file"])): continue
        f = slug_for(title) + ".jpg"
        meta, err = fetch(title, w, os.path.join(out, "img", "g", f))
        if not meta: bad.append(f"{title}: {err}"); continue
        meta["file"] = f; cr[title] = meta; json.dump(cr, open(cp, "w"), ensure_ascii=False, indent=1)
    print("guide refs", len(refs), "ok", sum(1 for t in refs if t in cr), "failed", bad)
