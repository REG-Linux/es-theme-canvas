import json, time, urllib.parse, urllib.request
UA = {"User-Agent": "REG-Linux-theme-builder/1.0 (cjom@reglinux.org)"}
def get(p):
    u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(p)
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: return json.load(r)
        except Exception: time.sleep(3 + 5 * i)
w = json.load(open("wikidata.json"))
ids = sorted(set(w["labels"]) | set(w["entities"]))
for i in range(0, len(ids), 45):
    r = get({"action": "wbgetentities", "ids": "|".join(ids[i:i+45]), "props": "labels|descriptions", "languages": "en|mul", "format": "json"})
    for k, v in r["entities"].items():
        lab = v.get("labels", {}); l = (lab.get("en") or lab.get("mul") or {}).get("value", "")
        w["labels"][k] = l
        if k in w["entities"]:
            w["entities"][k]["labels"] = {"en": {"value": l}} if l else {}
            d = v.get("descriptions", {}).get("en")
            if d: w["entities"][k]["descriptions"] = {"en": d}
    time.sleep(0.4)
json.dump(w, open("wikidata.json", "w"))
print(sum(1 for v in w["entities"].values() if not v.get("labels")), "items still without labels")
