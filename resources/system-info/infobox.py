"""Discontinuation years from English Wikipedia infoboxes (`| discontinued = ...`),
for the systems Wikidata gives no end date. Only the year is kept."""
import json, re, time, urllib.parse, urllib.request
from mapping import MAP

UA = {"User-Agent": "REG-Linux-theme-builder/1.0 (cjom@reglinux.org)"}

def get(url, params):
    u = url + "?" + urllib.parse.urlencode(params)
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 + 5 * i)
    raise RuntimeError(u)

qids = sorted({q for q in MAP.values() if q})
titles = {}
for i in range(0, len(qids), 45):
    r = get("https://www.wikidata.org/w/api.php", {"action": "wbgetentities", "ids": "|".join(qids[i:i+45]),
        "props": "sitelinks", "sitefilter": "enwiki", "format": "json"})
    for k, v in r["entities"].items():
        t = v.get("sitelinks", {}).get("enwiki", {}).get("title")
        if t:
            titles[k] = t
    time.sleep(0.4)

FIELD = re.compile(r"^\|\s*discontinued\s*=(.*?)(?=^\|\s*[a-z_ ]+\s*=|^\}\})", re.M | re.S | re.I)
out = {}
for q, t in sorted(titles.items()):
    r = get("https://en.wikipedia.org/w/api.php", {"action": "parse", "page": t, "prop": "wikitext", "section": 0,
        "redirects": 1, "format": "json", "formatversion": 2})
    text = r.get("parse", {}).get("wikitext", "")
    m = FIELD.search(text)
    time.sleep(0.3)
    if not m:
        continue
    value = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", "", m.group(1), flags=re.S)
    # citations and footnotes carry years too ({{sfn|Montfort|Bogost|2009}})
    value = re.sub(r"\{\{\s*(sfnp?|sfnm|efn|refn|r|rp|cn|citation needed|harvnb|harv|ref label|note|cite[^|}]*)\b[^{}]*\}\}",
                   "", value, flags=re.I)
    years = [int(y) for y in re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", value)]
    if years:
        out[q] = {"year": max(years), "article": r.get("parse", {}).get("title", t)}
json.dump(out, open("infobox.json", "w"), indent=1)
print(len(out), "discontinuation years")
