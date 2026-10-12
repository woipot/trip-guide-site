"""Search Wikimedia Commons images. Usage: python3 -I csearch.py "query" [limit]
Prints one line per result: TITLE | WxH | LICENSE | AUTHOR | THUMB_400_URL
Then preview a candidate:  curl -s -A "trip-guide-builder/1.0" -o /path/x.jpg "<THUMB_400_URL>"  and view it with the Read tool."""
import json, sys, time, re, urllib.request, urllib.parse
q = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
UA = {"User-Agent": "trip-guide-builder/1.0 (personal use)"}
p = {"action": "query", "generator": "search", "gsrsearch": "filetype:bitmap " + q, "gsrnamespace": 6, "gsrlimit": n,
     "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 400, "format": "json"}
url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)
for k in range(6):
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40)); break
    except Exception as e:
        time.sleep(5 * (k + 1))
else:
    sys.exit("search failed (rate limit?) — wait 30 s and retry")
pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
for pg in pages:
    ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
    art = re.sub(r"\s+", " ", re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", ""))).strip()[:40]
    print(f'{pg["title"][5:]} | {ii["width"]}x{ii["height"]} | {m.get("LicenseShortName", {}).get("value", "")} | {art} | {ii.get("thumburl", "")}')
time.sleep(1.5)
