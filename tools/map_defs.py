"""Where each area sits on each dungeon map. Read by make_maps.py.

All coordinates are pixels of the 1002x668 reference image in refs/.

A floor has:
  ref     the reference image name in refs/ (without .png)
  uimap   the floor's retail uiMapID, to look up its map tile file IDs
  decor   boxes (left, top, right, bottom) of page decoration that is always
          shown: the title banner and the illustration
  start   seed points of the part visible on arrival (the entrance)
  areas   { "Sub-zone name": [seed points] }

Every drawn pixel outside the decor boxes belongs to the area with the
nearest seed, so seeds go on the area's rooms and on its label. Add seeds to
pull a corridor or label towards the right area.
  aliases { "Other name the game may use": "Sub-zone name" }
"""

MAPS = [
    {
        "instance": 230,
        "slug": "blackrock-depths",
        "floors": [
            {
                "ref": "blackrock-depths-1",
                "uimap": 242,
                "decor": [(230, 25, 790, 78), (230, 78, 330, 100), (690, 78, 790, 100), (775, 150, 1002, 560)],
                "start": [(330, 560), (345, 500), (375, 470)],
                "areas": {
                    "Detention Block": [(475, 585), (513, 516), (440, 540)],
                    "Ring of the Law": [(510, 425), (570, 450)],
                    "Dark Iron Highway": [(255, 350), (340, 348), (340, 390), (410, 400)],
                    "Shadowforge City": [(440, 190), (465, 230), (560, 215), (650, 285), (520, 330), (470, 290), (700, 250), (600, 340)],
                    "Hall of Crafting": [(650, 160), (722, 140), (635, 140)],
                },
                "aliases": {"Ring of Law": "Ring of the Law"},
            },
            {
                "ref": "blackrock-depths-2",
                "uimap": 243,
                "decor": [(25, 20, 575, 100), (20, 100, 310, 500), (20, 500, 265, 540)],
                "areas": {
                    "The Lyceum": [(665, 75), (600, 130)],
                    "The Imperial Seat": [(860, 80), (800, 75), (898, 135)],
                    "Summoners' Tomb": [(535, 160), (515, 112)],
                    "Mold Foundry": [(490, 240), (425, 232), (475, 200)],
                    "Chamber of Enchantment": [(540, 320), (585, 268), (510, 280)],
                    "Shadowforge City": [(580, 400), (603, 353), (620, 440), (690, 470), (640, 380), (460, 330), (440, 470)],
                    "The Grim Guzzler": [(495, 420), (470, 365)],
                    "The Domicile": [(550, 470), (530, 492)],
                    "West Garrison": [(365, 470), (365, 545), (300, 523), (365, 430)],
                    "East Garrison": [(430, 600), (378, 625), (440, 520)],
                    "Ring of the Law": [(503, 600), (530, 548)],
                    "Shrine of Thaurissan": [(590, 570), (640, 592), (570, 520)],
                    "The Molten Bridge": [(668, 238), (705, 208), (640, 200)],
                },
                "aliases": {"Ring of Law": "Ring of the Law"},
            },
        ],
    },
]
