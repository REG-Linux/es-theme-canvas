# System info generator

Builds `_inc/systems/info/<system>.xml` (trivia) and `_inc/systems/devices/<system>.webp`
(device photos) for the dual-screen views, and `CREDITS.md`, from Wikidata (CC0), Wikimedia
Commons (free licences only), RetroHub/ScreenScraper system art (CC BY-NC-SA 4.0, `RETROHUB` in
`build.py`), 3D Warehouse renders whose authors allow free use (`WAREHOUSE`) and, for library sizes, Wikipedia's list articles. Needs Python 3 with PyYAML, and ImageMagick.

```sh
ES=path/to/REG-WIP/package/frontend/es-system/es_systems.yml
cd resources/system-info
python3 fetch.py                 # Wikidata items + Commons image metadata -> *.json
python3 relabel.py               # English or language-neutral (mul) labels
python3 counts.py                # library sizes from Wikipedia list articles
python3 infobox.py               # discontinuation years from Wikipedia infoboxes
python3 build.py ../.. "$ES"     # trivia + images (existing images are kept)
python3 credits.py ../.. "$ES"   # CREDITS.md
```

`mapping.py` maps each REG-Linux system to its Wikidata item (curated by hand). `build.py`
holds the hand-picked images, the excluded ones, missing authors and the photos whose gradient
background `gradient_cut.py` removes (`GRADIENT_CUT`). Delete an image from
`_inc/systems/devices/` to fetch it again.
