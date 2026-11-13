# Field Notes

A dungeon journal for **World of Warcraft: Forever** that starts blank and fills
in as you play. Nothing is shown until your character has seen it: the halls
you walk, the creatures you fight, the bosses you face and what they drop.

> **Beta.** This is an early test build. Most of it has only been played
> through the first half of the Deadmines. Expect rough edges, and please
> report them (see [Reporting problems](#reporting-problems)).

## What it does

- **Map** – a parchment sheet for each dungeon that is uncovered room by room
  as you reach it, drawn in the game's own dungeon-map art. Bosses you have
  faced are marked with a skull; click one for its page. Inside a dungeon the
  map key (`M`) opens this map instead of the game's empty one.
- **Bosses** – a page per boss: attempts, victories, defeats, your fastest
  kill, its abilities (written in once you have beaten it) and its loot.
- **Bestiary** – the creatures you have killed, with level, type and the
  abilities they are known to use.
- **Spoils** – every item of note found in the dungeon and who carried it.
  Shift-click a line to link the item in chat.
- **Diary** – a dated log of each visit, and a box on every page for notes of
  your own.

Maps ship for the 26 classic dungeons and raids (Ragefire Chasm to Naxxramas)
and for Alcaz Prison. The other new Forever dungeons work too – bosses,
bestiary, spoils and diary – but have no map yet.

## Installing

1. Download `FieldNotes-<version>.zip` from the
   [latest release](https://github.com/Phiir42/FieldNotes/releases).
2. Unzip it into your game's addon folder so that you end up with

   ```
   World of Warcraft\_forever_\Interface\AddOns\FieldNotes\FieldNotes.toc
   ```

3. Start the game (or `/reload`). The first time, a line in chat tells you the
   journal is in your pack.

To update, delete the old `FieldNotes` folder and unzip the new one. Your
journal is kept separately (in `WTF\Account\<you>\SavedVariables\FieldNotes.lua`)
and survives updates.

## Using it

Open the journal with the minimap button, `/fn`, or a key of your choice
(Options → Keybindings → AddOns → Field Notes). Inside a dungeon, the map key
opens straight to the map.

| Command | |
| --- | --- |
| `/fn` | open or close the journal |
| `/fn announce` | chat lines when something new is written down, on/off |
| `/fn quality <0-5>` | lowest item quality worth noting (default 2, uncommon) |
| `/fn button` | show or hide the minimap button |
| `/fn mapkey` | whether the map key opens the journal inside dungeons |
| `/fn sketch` | whether new parts of a map are sketched in or simply appear |
| `/fn maptest [instance id \| off]` | preview a shipped map without going there |
| `/fn debug` | what the game let the journal read, and what it hid |
| `/fn errors` | anything that went wrong, for reporting |
| `/fn version` | the installed version |

"Tear these pages out", at the bottom of a dungeon's first page, erases
everything noted about that dungeon.

## Things to know

- **The game hides a lot from addons inside dungeons.** Enemy names, ids and
  spell casts are not readable there, and the combat log is closed. The journal
  works from what is left: zone names, boss encounter events, experience and
  loot messages, corpses you loot, and what creatures say. So:
  - a creature enters the bestiary when you **kill it for experience** or
    **loot its corpse**, not when you first see it;
  - at maximum level, or for kills that give no experience, only looted
    corpses count;
  - abilities are not observed in the fight; they come from a list shipped
    with the addon and appear after the kill.
- **Maps of single-road dungeons fill in behind you.** Reaching a room also
  uncovers the rooms you must have passed through.
- **Boss positions are researched, not surveyed.** Most come from the classic
  spawn database and the retail dungeon journal; a few are best guesses
  (notably Shadowfang Keep's upper floors and all of Alcaz Prison).
- The journal is account-wide, English only for now.

## Reporting problems

Open an [issue](https://github.com/Phiir42/FieldNotes/issues) and include, if
you can:

- what you were doing and what you expected;
- the output of `/fn errors` and `/fn version`;
- a screenshot of the journal page that looks wrong;
- for map problems: the dungeon, where you were standing and which part of the
  map did or did not show;
- best of all, your saved journal:
  `WTF\Account\<you>\SavedVariables\FieldNotes.lua` (it holds only what the
  journal recorded: dungeon, creature and item names, and your own notes).

Saved journals from the new Forever dungeons are especially useful: the room
names and creatures recorded there are what the missing maps will be built from.

## For developers

```
FieldNotes/        the addon (Core, Record, Journal, Buttons; Maps and Abilities are generated)
tools/             the generators and tests
tools/defs/        one map definition per dungeon (see tools/defs/BRIEF.md)
```

- `python tools/test_addon.py` loads the addon into Lua 5.1 against a mock of
  the game client and plays a dungeon run through it (needs `pip install lupa`).
- `python tools/package.py` builds `dist/FieldNotes-<version>.zip`.
- `python tools/make_maps.py` and `python tools/make_abilities.py` rebuild the
  generated data. They need reference material that is not in this repository
  (map tiles and data tables from the game and from wago.tools, and the cmangos
  classic database), which they fetch or expect under `refs/`.

## Credits and licence

Field Notes is free software under the GNU General Public License, version 2
or (at your option) any later version; see [LICENSE](LICENSE).

Creature and ability data is derived from the
[cmangos classic database](https://github.com/cmangos/classic-db) (GPL), the
retail dungeon journal tables published by [wago.tools](https://wago.tools),
and the spell lists tracked by the BigWigs and LittleWigs boss modules.

The addon ships no game art: maps are drawn from tiles already in the game
client, shown through masks. World of Warcraft and all related names and art
are property of Blizzard Entertainment; this project is not affiliated with or
endorsed by Blizzard.
