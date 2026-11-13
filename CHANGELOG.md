# Changelog

## 0.2.0-beta.5 – not yet released

- Portraits: each boss page and bestiary entry shows the creature, drawn from
  the game's own model as a sepia sketch (or in colour, or not at all: see
  Preferences).
- Your own notes on single entries: click a creature in the bestiary, an item
  in the spoils or a hall on a dungeon's first page, and the notes box writes
  on that entry; the note shows under it.
- "See-through" now thins the paper and the window behind it and leaves the
  writing solid.
- Shadowfang Keep's later sheets and the Deadmines docks follow the order of
  real runs, so the map no longer runs ahead there.
- Friendly characters (captives, quest givers) are never filed as creatures,
  and trash first met during a boss fight returns to the bestiary once it is
  killed on its own.


## 0.2.0-beta.4

- Maps for the eight new Forever dungeons that had none: Blackmaw Hold, The
  Drowned City, The Hall of Thanes, City of Dalaran, Ruins of Lordaeron,
  Kroldok Stronghold, The Shaper's Terrace and the Excavation Site, painted in
  the game's map style from their minimaps. Room and boss placements on these
  are first guesses.
- The journal can be resized by dragging its bottom right corner, or made to
  fill the screen (the button beside the close button, `/fn full`, or
  Preferences).
- Fuller boss ability lists: fights that the server scripts in code (Arugal's
  curse and teleport, Onyxia, Ragnaros, Nefarian and 85 others) now list what
  those scripts cast.
- More in Preferences: the size of the writing, how light the paper is, how
  see-through the window is, and the size of the boss marks on the map.
- Dusts, essences and shards from disenchanting are no longer noted as loot.
- Blackfathom Deeps, Scarlet Monastery and Naxxramas: creatures are filed by
  where they really stand, as in the single-road dungeons.

## 0.2.0-beta.3

- A Preferences page at the bottom of the journal's contents (`/fn settings`,
  or right-click the minimap button): every option by clicking, plus the size
  of the journal window.
- Spoils are listed under the boss that carried them, then the rest.
- The journal remembers where you dragged it.
- Shadowfang Keep no longer uncovers rooms before you reach them, and in the
  other single-road dungeons creatures are filed by where they really stand.
- The map opens on the sheet you were last on, so boss marks on later sheets
  are not missed.
- A darker parchment look: the pages use the same sheet as the maps, with
  dark brown ink and red-brown headings.

## 0.2.0-beta.2

- Newly charted parts of a map are sketched in, room after room along the
  road, instead of appearing at once; a newly faced boss's marker is inked in
  after its room. New entries on the other pages (areas, bosses, bestiary,
  spoils, abilities) fade in the same way. `/fn sketch` turns this off.
- A slip of parchment shows on screen when something new is written down;
  click it to open the journal, drag it to move it (`/fn notices move`).
- The journal opens, closes and turns pages with sound (`/fn sound`).
- Your own deaths are written in the diary.
- The map key works in combat.
- Friendly characters who speak during a fight no longer enter the bestiary.
- Only "receives loot" chat lines count as loot: not rolls, not crafted items.

## 0.2.0-beta.1 – first public test build

Everything is new to testers; this lists what the build contains and what
changed since the private 0.1.0.

### The journal
- Pages per dungeon: overview with diary, bosses, map, bestiary, spoils, and
  your own notes on each dungeon and boss.
- Maps for 27 instances, uncovered area by area; single-road dungeons fill in
  behind you; raid wings and hub sheets are handled per wing.
- Boss markers on the maps (253 of 256 bosses placed), clickable.
- Shipped lore: abilities for 299 boss encounters and level, type and
  abilities for 1,131 dungeon creatures, shown only after you have met them.
- The map key opens the journal's map inside dungeons (`/fn mapkey`).

### Since 0.1.0
- The bestiary works on the Forever client: creatures are recorded from
  experience messages, looted corpses and what they say in combat, since the
  game hides their names and ids from addons.
- Loot is credited to the corpse it came from; trash drops no longer land on
  boss pages.
- Bosses stay out of the bestiary, including ones the addon has no data for.
- Creatures killed just before a boss pull are no longer filed under the boss.
- Errors are caught instead of interrupting play, kept, and shown by
  `/fn errors`.
- A key binding (Keybindings → AddOns), `/fn version`, a first-run chat line.

### Known gaps
- No maps yet for eight of the new Forever dungeons (Blackmaw Hold, The
  Drowned City, The Hall of Thanes, City of Dalaran, Ruins of Lordaeron,
  Kroldok Stronghold, The Shaper's Terrace, Excavation Site).
- Three bosses have no map marker (Mechanical Menagerie, The Molten Core
  encounter, Ezra Grimm).
- Boss marker positions for Alcaz Prison and upper Shadowfang Keep are guesses.
- Only played in the Deadmines so far; everything else is checked by an
  offline simulation, not in the game.
- English client only.
