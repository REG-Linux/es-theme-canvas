"""Library sizes from the lead of English Wikipedia's "List of ... games" articles."""
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

WD = "https://www.wikidata.org/w/api.php"
WP = "https://en.wikipedia.org/w/api.php"
ents = json.load(open("wikidata.json"))["entities"]

# console -> its list items (P2354 "has list"), then their enwiki titles
lists = {}
for q in sorted({q for q in MAP.values() if q}):
    for c in ents.get(q, {}).get("claims", {}).get("P2354", []):
        v = c["mainsnak"].get("datavalue", {}).get("value", {})
        if v.get("id"):
            lists.setdefault(q, []).append(v["id"])
ids = sorted({l for ls in lists.values() for l in ls} | {q for q in MAP.values() if q})
titles = {}
for i in range(0, len(ids), 45):
    r = get(WD, {"action": "wbgetentities", "ids": "|".join(ids[i:i+45]), "props": "sitelinks", "sitefilter": "enwiki", "format": "json"})
    for k, v in r["entities"].items():
        t = v.get("sitelinks", {}).get("enwiki", {}).get("title")
        if t:
            titles[k] = t
    time.sleep(0.4)

COUNT = re.compile(r"\b(?:there (?:are|were)|had|has|consists? of|includes?|contains?|a total of|library of)\s+"
                   r"(?:approximately |about |around |over |more than |roughly )?(\d[\d,]*)\s+(?:[\w-]+ ){0,4}?(?:games|titles)\b", re.I)

def lead(title):
    r = get(WP, {"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "redirects": 1, "titles": title, "format": "json"})
    p = list(r["query"]["pages"].values())[0]
    return p.get("title", title), p.get("extract", "")

out = {}
for q in sorted({q for q in MAP.values() if q}):
    cands = [titles[l] for l in lists.get(q, []) if l in titles]
    if q in titles:
        cands.append(f"List of {titles[q]} games")
    for t in cands:
        real, txt = lead(t)
        if not txt:
            continue
        m = COUNT.search(txt.replace("\n", " "))
        time.sleep(0.3)
        if m:
            n = int(m.group(1).replace(",", ""))
            if 5 <= n <= 20000:
                out[q] = {"games": n, "article": real, "sentence": m.group(0)}
                break
json.dump(out, open("counts.json", "w"), indent=1)
print(len(out), "systems with a game count")
