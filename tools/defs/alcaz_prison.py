# Alcaz Prison (a Forever dungeon). The game has no map sheet for it, so the
# sheet is tools/art/alcaz-prison.png, drawn by tools/draw_alcaz_prison.py
# from the instance's minimap. The instance has no sub-zones, so the areas
# uncover by boss. Which boss stands in which chamber is a GUESS from the
# encounter order (entrance assumed to be the gatehouse on the east): check
# in game and move the names.


def P(*points):
    """Points traced on the minimap crop -> sheet px (as in draw_alcaz_prison.place)."""
    return [(round((x - 505) * 0.84 + 501), round((y - 330) * 0.84 + 342)) for x, y in points]


MAP = {
    "instance": 2994,
    "slug": "alcaz-prison",
    "floors": [
        {
            "art": "alcaz-prison",
            "decor": [],
            # the gatehouse, the passage west and the main hall
            "start": P((773, 255), (668, 252), (585, 268), (500, 268), (410, 268), (416, 308), (478, 308)),
            "areas": {
                # the north cells, the upper cross passage and the round room
                "Overseer Wrex": P((416, 65), (416, 180), (546, 65), (546, 190), (470, 154), (643, 153), (365, 154)),
                # the two cell blocks along the passage south
                "Tidemistress Ca'zass": P((544, 348), (470, 348), (620, 348), (544, 413), (470, 413), (620, 413)),
                # the south chamber and its three wings
                "Katerina the Cleaner": P((545, 512), (460, 512), (630, 512), (546, 600), (544, 462)),
                # the west chamber, the west hall, the north-west cell and the cross hall
                "The Questioner": P((318, 258), (228, 252), (316, 160), (316, 335), (316, 382), (240, 382), (395, 382)),
                # the clover-shaped chamber
                "Blazeroar": P((316, 520), (316, 458), (316, 592), (248, 522), (384, 522), (317, 428)),
            },
            "aliases": {},
        },
    ],
}
