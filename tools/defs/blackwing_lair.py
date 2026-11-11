BANNER = [(225, 0, 790, 98)]
BANNER1 = [(305, 0, 705, 72), (225, 35, 328, 105), (700, 35, 790, 95)]

SUPPRESSION = {
    "Suppression Room": "Halls of Strife",
    "Corrupted Red Whelp": "Halls of Strife",
    "Corrupted Green Whelp": "Halls of Strife",
    "Corrupted Blue Whelp": "Halls of Strife",
    "Corrupted Bronze Whelp": "Halls of Strife",
    "Blackwing Taskmaster": "Halls of Strife",
}

LABS = {
    "Blackwing Technician": "Crimson Laboratories",
    "Blackwing Warlock": "Crimson Laboratories",
    "Blackwing Spellbinder": "Crimson Laboratories",
    "Death Talon Overseer": "Crimson Laboratories",
    "Death Talon Flamescale": "Crimson Laboratories",
    "Death Talon Seether": "Crimson Laboratories",
    "Death Talon Wyrmkin": "Crimson Laboratories",
    "Death Talon Captain": "Crimson Laboratories",
    "Master Elemental Shaper Krixix": "Crimson Laboratories",
}

MAP = {
    "instance": 469,
    "slug": "blackwing-lair",
    "path": True,  # one road: areas are listed in the order you pass through them
    "floors": [
        {
            "ref": "blackwing-lair-1",
            "uimap": 287,
            "decor": BANNER1 + [(505, 60, 1002, 340), (600, 340, 1002, 640), (380, 640, 470, 668)],
            "start": [(527, 558), (500, 515)],
            "areas": {
                "Dragonmaw Garrison": [(415, 403), (350, 370), (480, 340), (350, 450), (480, 450),
                                       (420, 500), (400, 300), (345, 315), (440, 280), (520, 430),
                                       (548, 372)],
                "Shadow Wing Lair": [(330, 183), (270, 180), (300, 255), (370, 225), (380, 120),
                                     (450, 170), (410, 160), (360, 85), (450, 111)],
            },
            "aliases": {
                "Razorgore the Untamed": "Dragonmaw Garrison",
                "Grethok the Controller": "Dragonmaw Garrison",
                "Blackwing Guardsman": "Dragonmaw Garrison",
                "Blackwing Legionnaire": "Dragonmaw Garrison",
                "Blackwing Mage": "Dragonmaw Garrison",
                "Death Talon Dragonspawn": "Dragonmaw Garrison",
                "Vaelastrasz the Corrupt": "Shadow Wing Lair",
                "Shadowwing Lair": "Shadow Wing Lair",
            },
        },
        {
            "ref": "blackwing-lair-2",
            "uimap": 288,
            "decor": BANNER + [(570, 290, 720, 372), (598, 372, 630, 392), (650, 100, 1002, 640)],
            "areas": {
                "Shadow Wing Lair": [(440, 200), (400, 160), (480, 125), (530, 210), (420, 290),
                                     (370, 215)],
                "Halls of Strife": [(300, 300), (270, 270), (330, 350), (250, 330), (270, 410),
                                    (349, 385), (380, 440), (350, 480), (400, 520), (430, 570)],
                "Death Talon Hatcher": [(500, 350), (480, 400), (540, 440), (590, 500), (520, 480),
                                        (530, 550)],
            },
            "aliases": dict(SUPPRESSION, **{
                "Vaelastrasz the Corrupt": "Shadow Wing Lair",
                "Broodlord Lashlayer": "Death Talon Hatcher",
            }),
        },
        {
            "ref": "blackwing-lair-3",
            "uimap": 289,
            "decor": BANNER + [(555, 100, 1002, 335), (650, 335, 1002, 640), (638, 420, 660, 480)],
            "areas": {
                "Halls of Strife": [(380, 450), (350, 440), (450, 520), (480, 470), (560, 520),
                                    (420, 570), (520, 570), (600, 530)],
                "Broodlord Lashlayer": [(500, 410), (540, 390), (560, 440), (470, 400), (500, 365)],
                "Firemaw": [(460, 288), (420, 210), (400, 310), (500, 300), (440, 250), (470, 335)],
                "Crimson Laboratories": [(240, 220), (290, 270), (340, 290), (320, 245), (215, 205)],
                "Ebonroc": [(345, 140), (300, 160), (330, 190), (400, 120), (270, 130)],
            },
            "aliases": dict(SUPPRESSION, **dict(LABS, **{
                "Death Talon Hatcher": "Halls of Strife",
                "Death Talon Wyrmguard": "Firemaw",
            })),
        },
        {
            "ref": "blackwing-lair-4",
            "uimap": 290,
            "decor": BANNER + [(505, 110, 1002, 335), (580, 335, 615, 385), (225, 95, 400, 108)],
            "areas": {
                "Crimson Laboratories": [(220, 370), (160, 400), (270, 330), (230, 300), (290, 370)],
                "Flamegor": [(350, 248), (380, 200), (320, 300), (420, 320), (450, 280), (300, 220),
                             (400, 355)],
                "Chromaggus": [(393, 482), (440, 440), (480, 420), (540, 380), (500, 480),
                               (430, 400)],
                "Nefarian's Lair": [(703, 485), (640, 430), (700, 380), (780, 450), (800, 520),
                                    (700, 580), (620, 520), (570, 490), (650, 600), (705, 352)],
            },
            "aliases": dict(LABS, **{
                "Nefarian": "Nefarian's Lair",
                "Lord Victor Nefarius": "Nefarian's Lair",
                "Nefarians Lair": "Nefarian's Lair",
                "Black Drakonid": "Nefarian's Lair",
                "Red Drakonid": "Nefarian's Lair",
                "Blue Drakonid": "Nefarian's Lair",
                "Green Drakonid": "Nefarian's Lair",
                "Bronze Drakonid": "Nefarian's Lair",
                "Chromatic Drakonid": "Nefarian's Lair",
                "Bone Construct": "Nefarian's Lair",
                "Chromaggus' Lair": "Chromaggus",
            }),
        },
    ],
}
