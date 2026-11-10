# The Temple of Atal'Hakkar (Sunken Temple). Sheet 1 is the game's own sheet
# of the main level. The game has no sheet for the lower level (the round
# statue chamber and its ring corridor), so sheet 2 is tools/art/
# sunken-temple-lower.png, drawn in the same style from the layout on Atlas's
# classic Sunken Temple map.
MAP = {
    "instance": 109,
    "slug": "sunken-temple",
    "floors": [
        {
            "ref": "sunken-temple-1",
            "uimap": 220,
            "decor": [(215, 0, 800, 58), (215, 20, 300, 88), (715, 20, 800, 88)],
            "start": [(497, 72), (497, 115), (560, 70), (592, 78), (500, 170)],
            "areas": {
                "Pit of Sacrifice": [(500, 300), (500, 235), (440, 300), (560, 300), (500, 370),
                                     (430, 250), (570, 250), (430, 360), (575, 365)],
                "Sanctum of the Fallen God": [(240, 300), (335, 315), (240, 200), (240, 420), (300, 230), (330, 400),
                                              (190, 300), (350, 240), (360, 380), (260, 160), (250, 440)],
                "Lair of the Chosen": [(760, 300), (672, 305), (660, 210), (700, 400), (760, 420), (640, 240),
                                       (650, 380), (800, 300), (690, 190), (780, 440)],
                "Chamber of the Dreamer": [(500, 440), (500, 500), (500, 580), (440, 580), (560, 580), (670, 505)],
                "Shade of Eranikus": [(665, 585), (720, 560), (690, 640), (600, 640), (730, 620)],
            },
            "aliases": {
                "The Pit of Sacrifice": "Pit of Sacrifice",
                "Dreamscythe": "Pit of Sacrifice",
                "Weaver": "Pit of Sacrifice",
                "Gasher": "Pit of Sacrifice",
                "Loro": "Pit of Sacrifice",
                "Hukku": "Pit of Sacrifice",
                "Zolo": "Pit of Sacrifice",
                "Zul'Lor": "Pit of Sacrifice",
                "Mijan": "Pit of Sacrifice",
                "Avatar of Hakkar": "Sanctum of the Fallen God",
                "Shade of Hakkar": "Sanctum of the Fallen God",
                "Hakkari Bloodkeeper": "Sanctum of the Fallen God",
                "Hakkari Minion": "Sanctum of the Fallen God",
                "Nightmare Suppressor": "Sanctum of the Fallen God",
                "Jammal'an the Prophet": "Lair of the Chosen",
                "Ogom the Wretched": "Lair of the Chosen",
                "Atal'ai High Priest": "Lair of the Chosen",
                "Mummified Atal'ai": "Lair of the Chosen",
                "Morphaz": "Chamber of the Dreamer",
                "Hazzas": "Chamber of the Dreamer",
            },
        },
        {
            "art": "sunken-temple-lower",
            "decor": [(230, 0, 790, 52), (230, 18, 300, 82), (720, 18, 790, 82)],
            "areas": {
                # the stair down and the ring corridor around the statue chamber
                "Murk Slitherer": [(502, 70), (502, 150), (398, 134), (450, 100), (502, 215), (631, 269), (685, 398),
                                   (631, 527), (502, 581), (373, 527), (319, 398), (373, 269),
                                   (411, 222), (613, 241), (352, 541), (587, 574)],
                # the round chamber with the six statues
                "Atal'alarion": [(502, 398), (502, 310), (590, 398), (414, 398), (502, 490),
                                 (565, 335), (440, 335), (565, 460), (440, 460)],
            },
            "aliases": {
                "Murk Worm": "Murk Slitherer",
                "Murk Spitter": "Murk Slitherer",
                "Deep Lurker": "Murk Slitherer",
                "Saturated Ooze": "Murk Slitherer",
                "Cursed Atal'ai": "Murk Slitherer",
                "Unliving Atal'ai": "Murk Slitherer",
                "Hall of Serpents": "Murk Slitherer",
                "The Pit of Refuse": "Atal'alarion",
                "Pit of Refuse": "Atal'alarion",
            },
        },
    ],
}
