"""Per-system device art and trivia for the canvas theme, from Wikidata (CC0)
and Wikimedia Commons (free licences only)."""
import html, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
import yaml
from mapping import MAP

UA = {"User-Agent": "REG-Linux-theme-builder/1.0 (cjom@reglinux.org)"}
# usage: build.py <theme dir> <REG-WIP package/frontend/es-system/es_systems.yml>
THEME = sys.argv[1]
SYSTEMS = yaml.safe_load(open(sys.argv[2]))
INFO_DIR = os.path.join(THEME, "_inc/systems/info")
DEV_DIR = os.path.join(THEME, "_inc/systems/devices")
os.makedirs(INFO_DIR, exist_ok=True)
os.makedirs(DEV_DIR, exist_ok=True)

def get(url, params):
    u = url + "?" + urllib.parse.urlencode(params)
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 + 5 * i)
    raise RuntimeError(u)

wd = json.load(open("wikidata.json"))
ents, labels = wd["entities"], wd["labels"]
com = json.load(open("commons.json"))
counts = json.load(open("counts.json")) if os.path.exists("counts.json") else {}
infobox = json.load(open("infobox.json")) if os.path.exists("infobox.json") else {}
NO_COUNT = {"msu-md", "snes-msu1"}   # mods: the base system's library is not theirs
files, finfo = com["files"], com["info"]

# Images picked by hand where the item has none (or a screenshot), and ones left out
FILE_OVERRIDES = {
    "msx1": "MSX-Hit Bit HB-75P.jpg",
    "msx2": "Panasonic FS-A1 20180519a.jpg",
    "msx2+": "MSX FS-A1WX, Seattle, 2023-09-30.jpg",
    "laser310": "VTech Laser 310 Color Computer and cassette deck.jpg",
    "vis": "Tandy Video Information System (front, flap closed).webp",
    "namco2x6": "System 246C.jpg",
    "x1": "Sharp X1 computer set.jpg",
    "atomiswave": "Atomiswave.jpg",
    "naomi2": "Naomi 2.jpg",
    "archimedes": "Acorn A3000 front view.jpg",
}

# Arcade systems: three cut-out cabinets side by side, the middle one in front
# (Commons has only these four cut out, so the two images share two of them)
COMPOSITE = {
    "mame": ["Donkey Kong arcade at the QuakeCon 2005.png", "Borne arcade Pacman.png",
             "Mario Bros. cabinet at PAX East 2014.png"],
    "fbneo": ["Borne arcade Pacman.png", "Neo Geo full on.png",
              "Donkey Kong arcade at the QuakeCon 2005.png"],
}

def compose(paths, out, side_scale=0.82, overlap=0.18, height=900):
    """left, middle, right cut-outs -> one image, the sides smaller and behind."""
    from PIL import Image
    imgs = []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGBA")
        im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 160 else 0).getbbox())   # (not a glow)
        h = int(height * (1 if i == 1 else side_scale))
        imgs.append(im.resize((max(1, im.width * h // im.height), h), Image.LANCZOS))
    left, mid, right = imgs
    ov_l, ov_r = int(left.width * overlap), int(right.width * overlap)
    w = left.width + mid.width + right.width - ov_l - ov_r
    canvas = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    canvas.alpha_composite(left, (0, height - left.height))
    canvas.alpha_composite(right, (w - right.width, height - right.height))
    canvas.alpha_composite(mid, (left.width - ov_l, 0))
    tmp = out + ".png"
    canvas.save(tmp)
    subprocess.run(["magick", tmp, "-resize", "640x400>", "-strip", "-quality", "88", out], check=True)
    os.remove(tmp)
NO_IMAGE = {"prboom", "quake", "scummvm", "dos", "atom"}   # box art, GPL screenshots, unverifiable PD
# Authors the Commons metadata lacks, from the file pages' text
AUTHOR_OVERRIDES = {
    "CDTV.jpg": "Patric Klöter (commodore-amiga.de)",
    "MSX-Hit Bit HB-75P.jpg": "Eike Sauer",
    "Coleco-adam.jpg": "Andrew Lih",
    "Donkey Kong arcade at the QuakeCon 2005.png": "Joshua Driggs (ZapWizard); background removed by bayo and Shooke",
}
# Better photos from RetroHub's system art, which credits ScreenScraper, CC BY-NC-SA 4.0
# (canvas is CC BY-NC-SA too). system -> RetroHub asset name
RETROHUB = {
    "samcoupe": "samcoupe", "thomson": "to8", "spectravideo": "spectravideo", "x1": "x1",
    "x68000": "x68000", "pc98": "pc98", "naomi": "naomi", "naomi2": "naomigd", "sufami": "sufami",
    "atomiswave": "atomiswave", "msxturbor": "msxturbor", "dos": "dos",
    "apple2": "apple2", "coco": "coco", "pokemini": "pokemini", "ti99": "ti99",
}
RETROHUB_RAW = "https://raw.githubusercontent.com/retrohub-org/retrohub/main/assets/systems/{}-photo.png"
RETROHUB_PAGE = "https://github.com/retrohub-org/retrohub/blob/main/assets/systems/{}-photo.png"

# SketchUp 3D Warehouse renders of models whose authors allow free use (and Trimble's
# General Model License): system -> (model id, render, author, model title)
WAREHOUSE = {
    "amigacdtv": ("4d59fd18-74a8-448e-b560-17116ca3bb96", "bot_lt", "Sebastien G.", "Commodore Amiga CDTV"),
}
WAREHOUSE_API = "https://3dwarehouse.sketchup.com/warehouse/v1.0/entities/{}"
WAREHOUSE_PAGE = "https://3dwarehouse.sketchup.com/model/{}"

# White cases touching the white background: the cut would eat them
NO_CUT = set()
# Photos on a smooth gradient: gradient_cut.py, with its tolerance
GRADIENT_CUT = {"c20": 14}
OK_LICENSE = re.compile(r"^(public domain|pd|cc0|cc[ -]by(-sa)?( [\d.]+)?( [a-z]{2})?|copyrighted free use)$", re.I)

# licence data for the hand-picked files
need = [f for f in FILE_OVERRIDES.values() if f not in finfo]
if need:
    r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "titles": "|".join("File:" + n for n in need),
        "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": "640", "format": "json"})
    norm = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
    for p in r["query"]["pages"].values():
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
        finfo[norm.get(p["title"], p["title"])[5:]] = {"thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
            "license": em.get("LicenseShortName", {}).get("value", ""), "licenseUrl": em.get("LicenseUrl", {}).get("value", ""),
            "artist": em.get("Artist", {}).get("value", ""), "credit": em.get("Credit", {}).get("value", "")}

# labels of qualifier items (places of publication)
missing = set()
for e in ents.values():
    for c in e.get("claims", {}).get("P577", []):
        for q in c.get("qualifiers", {}).get("P291", []):
            v = q.get("datavalue", {}).get("value", {})
            if v.get("id") and v["id"] not in labels:
                missing.add(v["id"])
missing = sorted(missing)
for i in range(0, len(missing), 45):
    r = get("https://www.wikidata.org/w/api.php", {"action": "wbgetentities", "ids": "|".join(missing[i:i+45]),
        "props": "labels", "languages": "en", "format": "json"})
    for k, v in r["entities"].items():
        labels[k] = v.get("labels", {}).get("en", {}).get("value", "")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def claims(e, p):
    return [c for c in e.get("claims", {}).get(p, []) if c["mainsnak"].get("snaktype") == "value" and c.get("rank") != "deprecated"]

def item_labels(e, p, n=2, plain_only=False):
    out = []
    cs = claims(e, p)
    if plain_only:   # the claims with no qualifier first: a remaster's studio carries one
        cs = [c for c in cs if not c.get("qualifiers")] or cs
    for c in cs:
        l = labels.get(c["mainsnak"]["datavalue"]["value"].get("id"), "")
        if l and l not in out:
            out.append(l)
    return out[:n]

def first_date(e):
    best = None
    for p in ("P577", "P571"):
        for c in claims(e, p):
            v = c["mainsnak"]["datavalue"]["value"]
            m = re.match(r"\+(\d{4})-(\d{2})", v["time"])
            if not m:
                continue
            key = (int(m.group(1)), int(m.group(2)) if v["precision"] >= 10 else 13)
            place = ""
            for q in c.get("qualifiers", {}).get("P291", []):
                place = labels.get(q.get("datavalue", {}).get("value", {}).get("id"), "")
            if best is None or key < best[0]:
                best = (key, v["precision"], place)
        if best:
            return best
    return None

def units(e):
    vals = []
    for c in claims(e, "P2664"):
        try:
            vals.append(float(c["mainsnak"]["datavalue"]["value"]["amount"]))
        except (KeyError, ValueError):
            pass
    return max(vals) if vals else None

def end_year(e):
    years = []
    for c in claims(e, "P2669"):
        m = re.match(r"\+(\d{4})", c["mainsnak"]["datavalue"]["value"]["time"])
        if m:
            years.append(int(m.group(1)))
    wp = infobox.get(e["id"], {}).get("year")   # Wikipedia's infobox: Wikidata often has none
    if wp:
        years.append(wp)
    return max(years) if years else None   # the line's end, not its first model's

CURRENCY = {"Q4917": "${}", "Q25224": "£{}", "Q4916": "€{}", "Q8146": "¥{}"}

def launch_price(e):
    """The earliest price, in US dollars when there is one."""
    best = None
    for c in claims(e, "P2284"):
        v = c["mainsnak"]["datavalue"]["value"]
        cur = v.get("unit", "").rsplit("/", 1)[-1]
        if cur not in CURRENCY:
            continue
        when = "9999"
        for q in c.get("qualifiers", {}).get("P585", []):
            when = q.get("datavalue", {}).get("value", {}).get("time", when)[1:5]
        key = (cur != "Q4917", when)
        if best is None or key < best[0]:
            amount = float(v["amount"])
            best = (key, CURRENCY[cur].format(f"{amount:,.2f}".replace(".00", "")))
    return best[1] if best else None

def lineage(e):
    before = item_labels(e, "P155", 1, True)
    after = item_labels(e, "P156", 1, True)
    if before and after:
        return f"It followed the {before[0]} and was succeeded by the {after[0]}."
    if before:
        return f"It followed the {before[0]}."
    if after:
        return f"It was succeeded by the {after[0]}."
    return None

def fmt_units(n):
    if n >= 1e6:
        s = f"{n / 1e6:.1f}".rstrip("0").rstrip(".")
        return s + " million"
    return f"{int(n):,}"

def article(s):
    if re.match(r"^[A-Z][\w.-]*'s\b", s):   # "Sony's fourth home console"
        return ""
    if re.match(r"^(first|second|third|fourth|fifth|final|last)\b(?!-)", s, re.I):
        return "the"
    return "an" if s[:1].lower() in "aeiou" or re.match(r"^(8|11|18)\b", s) else "a"

def where(place):
    if not place:
        return ""
    if place.lower() == "worldwide":
        return " worldwide"
    the = place in ("United States", "United States of America", "United Kingdom", "Netherlands", "Philippines")
    return " in " + ("the " if the else "") + place

def sentence(s):
    s = s.strip()
    return s[:1].upper() + s[1:] + ("" if s.endswith(".") else ".")

def trivia(key, sysdef, e, qid):
    label = e.get("labels", {}).get("en", {}).get("value") or sysdef.get("name", key)
    desc = e.get("descriptions", {}).get("en", {}).get("value", "")
    hw = sysdef.get("hardware")
    parts = []
    if desc:
        a = article(desc)
        parts.append(f"{label} is {a + ' ' if a else ''}{desc}.")
    d = first_date(e)
    if d:
        (year, month), prec, place = d
        when = f"{MONTHS[month - 1]} {year}" if month <= 12 else str(year)
        end = end_year(e)
        if end and end > year:
            parts.append(f"First released{where(place)} in {when} and discontinued in {end}.")
        else:
            parts.append(f"First released{where(place)} in {when}.")
    if hw in ("port",):
        dev = item_labels(e, "P178", 1, True)
        if dev and "developed by" not in desc.lower():
            # (no publisher: Wikidata's first one is often a later re-release's)
            parts.append(f"Developed by {dev[0].rstrip('.')}")
        genre = item_labels(e, "P136", 1, True)
        modes = [re.sub(r" (video )?game$", "", m.lower()) for m in item_labels(e, "P404", 3, True)]
        if genre and genre[0].lower() not in desc.lower():
            parts.append(f"Genre: {genre[0]}.")
        if modes:
            parts.append(f"Game modes: {', '.join(modes)}.")
    else:
        makers = item_labels(e, "P176", 4, True)
        if makers and not any(m.lower() in desc.lower() for m in makers) and " by " not in desc:
            parts.append(f"Made by {min(makers, key=len).rstrip('.')}")
        price = launch_price(e)
        if price:
            parts.append(f"It launched at {price}" + (" in the US." if price.startswith("$") else "."))
        n = units(e)
        if n and n >= 1000:
            parts.append(f"About {fmt_units(n)} units were sold.")
        if qid in counts and key not in NO_COUNT:
            parts.append(f"Its library has {counts[qid]['games']:,} games.")
        line = lineage(e)
        if line:
            parts.append(line)
        cpu = item_labels(e, "P880")
        if cpu:
            parts.append(f"Processors include the {' and the '.join(cpu)}.")
    return "\n".join(sentence(p) for p in parts)   # one fact per line

# Still on sale: their years read "2017-" (Wikidata has no end date for them, but
# neither has it for many discontinued ones, which read "1990-?")
STILL_SOLD = {"switch", "commanderx16", "arduboy",
              "mame", "fbneo", "scummvm"}   # (emulators: still developed)

def years(key, sysdef, e):
    start = sysdef.get("release")
    if not isinstance(start, int):
        d = first_date(e)
        start = d[0][0] if d else None
    if not start:
        return None
    if sysdef.get("hardware") == "port":    # a game: its year
        return str(start)
    if key in STILL_SOLD:
        return f"{start}-"
    end = end_year(e)
    if end and end > start:
        return f"{start}-{end}"
    if end == start:
        return str(start)
    return f"{start}-?"

def plain(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

def commons_info(names):
    got = {}
    for i in range(0, len(names), 40):
        r = get("https://commons.wikimedia.org/w/api.php", {"action": "query", "titles": "|".join("File:" + n for n in names[i:i+40]),
            "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": "900", "format": "json"})
        norm = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
        for p in r["query"]["pages"].values():
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
            got[norm.get(p["title"], p["title"])[5:]] = {"thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "mime": ii.get("mime"),
                "license": em.get("LicenseShortName", {}).get("value", ""), "licenseUrl": em.get("LicenseUrl", {}).get("value", ""),
                "artist": em.get("Artist", {}).get("value", ""), "credit": em.get("Credit", {}).get("value", "")}
        time.sleep(0.5)
    return got

# A PNG upload of the same photo (Evan Amos often has one, cut out on transparency)
jpgs = sorted({(FILE_OVERRIDES.get(k) or files.get(q)) for k, q in MAP.items() if q} - {None})
jpgs = [f for f in jpgs if re.search(r"\.jpe?g$", f, re.I)]
png_alt = commons_info([re.sub(r"\.jpe?g$", ".png", f, flags=re.I) for f in jpgs])
for name, fi in png_alt.items():
    finfo[name] = fi

def prepare(raw, out):
    """Resize; a photo on plain white loses the white (cut from the corners)."""
    probe = subprocess.run(["magick", raw, "-alpha", "on", "-format",
        "%[fx:p{0,0}.a<0.5||p{w-1,h-1}.a<0.5?1:0] %[fx:min(min(p{0,0}.intensity,p{w-1,0}.intensity),min(p{0,h-1}.intensity,p{w-1,h-1}.intensity))]", "info:"],
        capture_output=True, text=True, check=True).stdout.split()
    has_alpha, corner = probe[0] == "1", float(probe[1])
    name = os.path.basename(out)[:-5]
    if name in GRADIENT_CUT and not has_alpha:
        cut = raw + ".cut.png"
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "gradient_cut.py"),
                        raw, cut, str(GRADIENT_CUT[name])], check=True)
        subprocess.run(["magick", cut, "-resize", "640x400>", "-strip", "-quality", "85", out], check=True)
        return
    cmd = ["magick", raw, "-alpha", "on"]
    if not has_alpha and corner >= 0.97 and os.path.basename(out)[:-5] not in NO_CUT:
        cmd += ["-fuzz", "2%", "-fill", "none"]
        w, h = map(int, subprocess.run(["magick", "identify", "-format", "%w %h", raw + "[0]"],
                                       capture_output=True, text=True, check=True).stdout.split())
        for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            cmd += ["-draw", f"color {x},{y} floodfill"]
    cmd += ["-trim", "+repage", "-resize", "640x400>", "-strip", "-quality", "85", out]
    subprocess.run(cmd, check=True)

credits = []
written = 0
for key, sysdef in SYSTEMS.items():
    qid = MAP.get(key)
    if not qid or qid not in ents:
        continue
    theme = str(sysdef.get("theme", key))
    e = ents[qid]
    text = trivia(key, sysdef, e, qid)
    span = years(key, sysdef, e)
    with open(os.path.join(INFO_DIR, f"{theme}.xml"), "w") as f:
        f.write("<theme>\n  <formatVersion>7</formatVersion>\n  <!-- " + f"Wikidata {qid} (CC0)" + " -->\n  <variables>\n")
        f.write(f"    <systemTrivia>{html.escape(text, quote=False)}</systemTrivia>\n")
        if span:
            f.write(f"    <systemYears>{span}</systemYears>\n")
        f.write("  </variables>\n</theme>\n")
    written += 1

    if key in COMPOSITE:
        names = COMPOSITE[key]
        missing = [n for n in names if n not in finfo]
        if missing:
            finfo.update(commons_info(missing))
        out = os.path.join(DEV_DIR, f"{theme}.webp")
        raws = []
        for n in names:
            raw = os.path.join("raw", "big-" + re.sub(r"[^A-Za-z0-9._-]", "_", n))
            os.makedirs("raw", exist_ok=True)
            if not os.path.exists(raw):
                with urllib.request.urlopen(urllib.request.Request(finfo[n]["thumb"], headers=UA), timeout=120) as r, open(raw, "wb") as w:
                    w.write(r.read())
                time.sleep(0.5)
            raws.append(raw)
        if not os.path.exists(out):
            compose(raws, out)
        for n in names:
            if n in AUTHOR_OVERRIDES:
                finfo[n]["artist"] = AUTHOR_OVERRIDES[n]
            credits.append((theme, sysdef.get("name", key), n, finfo[n]))
        continue

    if key in WAREHOUSE:
        mid, render, author, title = WAREHOUSE[key]
        out = os.path.join(DEV_DIR, f"{theme}.webp")
        if not os.path.exists(out):
            raw = os.path.join("raw", f"warehouse-{mid}-{render}.png")
            os.makedirs("raw", exist_ok=True)
            if not os.path.exists(raw):
                url = get(WAREHOUSE_API.format(mid), {"recordEvent": "false", "fields": "all"})["binaries"][render]["contentUrl"]
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(raw, "wb") as w:
                    w.write(r.read())
            # the render's flat grey backdrop, from the corners
            w_, h_ = map(int, subprocess.run(["magick", "identify", "-format", "%w %h", raw + "[0]"],
                                             capture_output=True, text=True, check=True).stdout.split())
            cmd = ["magick", raw, "-alpha", "on", "-fuzz", "4%", "-fill", "none"]
            for x, y in ((0, 0), (w_ - 1, 0), (0, h_ - 1), (w_ - 1, h_ - 1)):
                cmd += ["-draw", f"color {x},{y} floodfill"]
            cmd += ["-trim", "+repage", "-resize", "640x400>", "-strip", "-quality", "88", out]
            subprocess.run(cmd, check=True)
        credits.append((theme, sysdef.get("name", key), f"{title} (3D Warehouse render)", {
            "artist": author, "license": "free use (author) / 3D Warehouse General Model License",
            "licenseUrl": "https://3dwarehouse.sketchup.com/tos", "page": WAREHOUSE_PAGE.format(mid)}))
        continue

    if key in RETROHUB:
        rh = RETROHUB[key]
        out = os.path.join(DEV_DIR, f"{theme}.webp")
        if not os.path.exists(out):
            raw = os.path.join("raw", f"retrohub-{rh}.png")
            os.makedirs("raw", exist_ok=True)
            if not os.path.exists(raw):
                with urllib.request.urlopen(urllib.request.Request(RETROHUB_RAW.format(rh), headers=UA), timeout=120) as r, open(raw, "wb") as w:
                    w.write(r.read())
            prepare(raw, out)
        credits.append((theme, sysdef.get("name", key), f"{rh}-photo.png (RetroHub)", {
            "artist": "ScreenScraper community (via RetroHub)", "license": "CC BY-NC-SA 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by-nc-sa/4.0/", "page": RETROHUB_PAGE.format(rh)}))
        continue

    fname = FILE_OVERRIDES.get(key) or files.get(qid)
    if fname and re.sub(r"\.jpe?g$", ".png", fname, flags=re.I) in png_alt:
        alt = re.sub(r"\.jpe?g$", ".png", fname, flags=re.I)
        if OK_LICENSE.match(png_alt[alt]["license"].strip()):
            fname = alt
    if key in NO_IMAGE or not fname or fname not in finfo:
        continue
    fi = finfo[fname]
    if not OK_LICENSE.match(fi["license"].strip()):
        print("skip licence", key, fname, fi["license"])
        continue
    out = os.path.join(DEV_DIR, f"{theme}.webp")
    if not os.path.exists(out):
        raw = os.path.join("raw", re.sub(r"[^A-Za-z0-9._-]", "_", fname))
        os.makedirs("raw", exist_ok=True)
        if not os.path.exists(raw):
            with urllib.request.urlopen(urllib.request.Request(fi["thumb"], headers=UA), timeout=120) as r, open(raw, "wb") as w:
                w.write(r.read())
            time.sleep(0.5)
        prepare(raw, out)
    if fname in AUTHOR_OVERRIDES:
        fi["artist"] = AUTHOR_OVERRIDES[fname]
    credits.append((theme, sysdef.get("name", key), fname, fi))

json.dump([(t, n, f, i) for t, n, f, i in credits], open("credits.json", "w"), indent=1)
print(written, "trivia files,", len(credits), "images")
