# Writing a map definition

Field Notes is an addon for a classic-era client ("WoW Forever": vanilla
dungeons, raids and bosses). Its journal has a Map page per instance that
starts as blank parchment and uncovers each area's part of the map when the
player walks into that area or fights a boss or creature there.

## How it works

- `refs/<slug>-<floor>.png` are the retail game's map images, 1002x668.
  `refs/grid/<slug>-<floor>.png` are the same with a coordinate grid (lines
  every 50 px, labels every 100 px). Read the grid images to place coordinates.
- `tools/defs/blackrock_depths.py` is the worked example; the docstring at the
  top of `tools/make_maps.py` describes the format. A definition file holds
  `MAP = { "instance": N, "slug": "<slug>", "floors": [ {...}, ... ] }` with
  floors in the same order as the ref images, each with "ref", "uimap",
  "decor", optional "start", "areas", optional "aliases".
- Every drawn pixel on the map is assigned to the area whose seed point is
  nearest, except pixels inside the "decor" boxes (title banner, big character
  illustration), which are always shown. So put several seeds on each area's
  rooms and corridors and one on its text label, so the label uncovers with
  its area. Put decor boxes tightly around the banner and the illustration,
  not overlapping any rooms or labels.
- "start" = seed points on the instance entrance (where the player arrives;
  the map usually marks entrances and exits with a swirl icon). Only on
  floors the player can enter on.
- An area's "Name" is a trigger: the area uncovers when the journal records
  that name. Triggers can be (a) the in-game sub-zone name shown on the
  minimap when standing there (classic client, enUS), (b) a boss name, (c) a
  distinctive creature name found there. Use the most reliable trigger as the
  area's key and add the others in "aliases" (`{"Other name": "Area key"}`).
  Matching ignores case, punctuation and a leading "The".
- Many classic instances have few or no sub-zones, so every area should have
  at least one boss or common trash-mob name as a trigger where you know one,
  in addition to any sub-zone name. Use VANILLA bosses and creatures, not the
  retail replacements. The retail map's labels are good candidates for
  sub-zone names but are not guaranteed to match; look names up on the web
  (warcraft.wiki.gg, classic.wowhead.com) if you have web tools. If unsure,
  include your best guess plus alternatives as aliases; wrong aliases are
  harmless.
- Split each floor into areas a player would discover one after another
  (roughly one per named room, boss room or wing; 3 to 14 per floor). Areas
  must jointly cover the whole drawing: any drawing more than 150 px from
  every seed becomes always-visible decoration, which is wrong for rooms, so
  add seeds until nothing of the instance is left out.
- If the retail map clearly does not match the vanilla instance, still do
  your best and say so in your report.

## Verify (required)

From the repository root run `python tools/make_maps.py --only <slug>`.
It writes `refs/preview/<slug>-<floor>-cells.png` (each area tinted its own
colour, seeds numbered, legend top-left; grey tint = decoration) and
`refs/preview/<slug>-<floor>.png` (arrival, half and fully explored).
Read the cells image for every floor and fix: rooms tinted grey (need seeds),
labels owned by the wrong area (add a seed on the label), banner or
illustration not grey (fix decor boxes), cell boundaries that cut a room in
half (move or add seeds), any "!!" warnings printed. Iterate until each floor
looks right. (`python` here is a .bat shim: run scripts as files, never
multi-line `python -c`.)

## Rules

Only create or edit your own `tools/defs/*.py` file(s). Do not run
`make_maps.py` without `--only`, do not edit other files, do not use git, do
not touch the WoW install.

## Report

For each instance: floors done, the area keys with their aliases, which names
you are unsure about, and any mismatch between the retail map and vanilla.
