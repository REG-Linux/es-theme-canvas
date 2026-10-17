import json, time, urllib.parse, urllib.request
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
WD = "https://www.wikidata.org/w/api.php"
qids = sorted({q for q in MAP.values() if q})
ents = {}
for i in range(0, len(qids), 40):
    r = get(WD, {"action": "wbgetentities", "ids": "|".join(qids[i:i+40]), "props": "labels|descriptions|claims", "languages": "en", "format": "json"})
    ents.update(r["entities"])
    time.sleep(0.5)
# labels of referenced items
props = ["P176", "P178", "P123", "P880", "P136", "P31", "P495", "P408", "P155", "P156", "P437", "P404", "P179"]
refs = set()
for e in ents.values():
    for p in props:
        for c in e.get("claims", {}).get(p, []):
            v = c["mainsnak"].get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v: refs.add(v["id"])
refs = sorted(refs - set(ents))
labels = {}
for i in range(0, len(refs), 45):
    r = get(WD, {"action": "wbgetentities", "ids": "|".join(refs[i:i+45]), "props": "labels", "languages": "en", "format": "json"})
    for k, v in r["entities"].items():
        labels[k] = v.get("labels", {}).get("en", {}).get("value", "")
    time.sleep(0.5)
for k, e in ents.items():
    labels[k] = e.get("labels", {}).get("en", {}).get("value", "")
json.dump({"entities": ents, "labels": labels}, open("wikidata.json", "w"))
# images
files = {}
for k, e in ents.items():
    for c in e.get("claims", {}).get("P18", [])[:1]:
        files[k] = c["mainsnak"]["datavalue"]["value"]
info = {}
names = sorted(set(files.values()))
for i in range(0, len(names), 40):
    r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "titles": "|".join("File:" + n for n in names[i:i+40]),
        "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": "640", "format": "json"})
    norm = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
    for p in r["query"]["pages"].values():
        if "imageinfo" not in p: continue
        ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
        title = norm.get(p["title"], p["title"])[5:]
        info[title] = {"thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "mime": ii.get("mime"),
            "license": em.get("LicenseShortName", {}).get("value", ""), "licenseUrl": em.get("LicenseUrl", {}).get("value", ""),
            "artist": em.get("Artist", {}).get("value", ""), "credit": em.get("Credit", {}).get("value", ""),
            "usage": em.get("UsageTerms", {}).get("value", "")}
    time.sleep(0.5)
json.dump({"files": files, "info": info}, open("commons.json", "w"), indent=1)
print(len(ents), "items", len(files), "images", len(info), "infos")
