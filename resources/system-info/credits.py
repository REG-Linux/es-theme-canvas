import html, json, os, re, sys, yaml
from mapping import MAP
theme_dir, systems_yml = sys.argv[1], sys.argv[2]
systems = yaml.safe_load(open(systems_yml))
credits = json.load(open("credits.json"))
w = json.load(open("wikidata.json"))
counts = json.load(open("counts.json")) if os.path.exists("counts.json") else {}

def plain(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

def cell(s):
    return s.replace("|", "\\|")

lines = ["# Credits", "",
 "Canvas is by Siddy212 (https://github.com/Siddy212/canvas-es), CC BY-NC-SA. The theme's",
 "own credits are in README.md and NOTICE.md. This file covers the per-system device art and",
 "trivia added for dual-screen devices (`_inc/systems/devices/`, `_inc/systems/info/`).", "",
 "## Trivia: Wikidata (CC0)", "",
 "Each `_inc/systems/info/<system>.xml` is written from the structured data of one Wikidata",
 "item: its description, first release and discontinuation dates, launch price, manufacturer,",
 "units sold, predecessor and successor, processors, and for games their developer, genre and",
 "modes. Wikidata's structured data is dedicated to the public domain under",
 "[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)",
 "([Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)). No Wikipedia text is",
 "used. The sentences are generated, so check them against the item when in doubt.", "",
 "| System | Wikidata item |", "| --- | --- |"]
for key, sysdef in systems.items():
    q = MAP.get(key)
    if not q or q not in w["entities"]:
        continue
    theme = str(sysdef.get("theme", key))
    label = w["labels"].get(q, "")
    lines.append(f"| `{theme}` | [{cell(label)} ({q})](https://www.wikidata.org/wiki/{q}) |")
lines += ["", "## Library sizes: Wikipedia", "",
 "The number of games in a system's library is taken from the opening of its English Wikipedia",
 "list article, where that article states it. Only the number is used, not the article's text.",
 "Wikipedia text is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).", "",
 "| System | Games | Article |", "| --- | --- | --- |"]
for key, sysdef in systems.items():
    q = MAP.get(key)
    if q in counts and key not in ("msu-md", "snes-msu1"):
        a = counts[q]["article"]
        url = "https://en.wikipedia.org/wiki/" + a.replace(" ", "_")
        lines.append(f"| `{sysdef.get('theme', key)}` | {counts[q]['games']:,} | [{cell(a)}]({url}) |")
infobox = json.load(open("infobox.json")) if os.path.exists("infobox.json") else {}
lines += ["", "## Discontinuation years: Wikipedia", "",
 "Where Wikidata has no end date, the year a system was discontinued is taken from the",
 "\"discontinued\" field of its English Wikipedia infobox (only the year). The later of the two is",
 "used. Wikipedia text is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).", "",
 "| System | Year | Article |", "| --- | --- | --- |"]
for key, sysdef in systems.items():
    q = MAP.get(key)
    if q in infobox:
        a = infobox[q]["article"]
        lines.append(f"| `{sysdef.get('theme', key)}` | {infobox[q]['year']} | [{cell(a)}](https://en.wikipedia.org/wiki/{a.replace(' ', '_')}) |")
lines += ["", "## Device images", "",
 "Each `_inc/systems/devices/<system>.webp` is a copy of the file named below, under that file's",
 "own licence. Most are from Wikimedia Commons. A few are from RetroHub's system art",
 "(https://github.com/retrohub-org/retrohub), which credits them to ScreenScraper",
 "(https://www.screenscraper.fr) under CC BY-NC-SA 4.0, the licence canvas itself uses. Renders",
 "of SketchUp 3D Warehouse models are used where the model's author allows free use; they are",
 "credited to that author.", "",
 "Changes made: resized to 640x400 at most and saved as WebP, and, for photos on a plain white",
 "or smooth gradient background, the background made transparent and the image cropped to the",
 "device. From Commons only public-domain, CC0, CC BY and CC BY-SA files are used. A CC BY-SA or",
 "CC BY-NC-SA image stays under that licence: reuse it under those terms, with the author",
 "credited. The products shown are trademarks of their owners.", "",
 "Many of the console photos are by Evan Amos (Vanamo Media), who releases them into the",
 "public domain.", "",
 "| Image | Shows | Author | Licence | Source |", "| --- | --- | --- | --- | --- |"]
for theme, name, fname, fi in sorted(credits, key=lambda c: c[0]):
    author = plain(fi.get("artist")) or plain(fi.get("credit")) or "unknown"
    lic = fi.get("license", "")
    lic_md = f"[{lic}]({fi['licenseUrl']})" if fi.get("licenseUrl") else lic
    lines.append(f"| `{theme}.webp` | {cell(name)} | {cell(author)} | {lic_md} | [{cell(fname)}]({fi['page']}) |")
open(f"{theme_dir}/CREDITS.md", "w").write("\n".join(lines) + "\n")
print(len(lines), "lines")
