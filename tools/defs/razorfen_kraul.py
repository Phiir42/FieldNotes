MAP = {
    "instance": 47,
    "slug": "razorfen-kraul",
    "path": True,  # one road: areas are listed in the order you pass through them
    # on the skulls painted on the sheet (the spawn data puts them a little beside)
    "bosses": {"Aggem Thorncurse": (1, 807, 346), "Agathelos the Raging": (1, 79, 455),
               # where the classic data puts him (retail has him by Jargba); a real run met him
               # after Ramtusk and before the bats, as here
               "Roogug": (1, 649, 281)},
    "floors": [
        {
            "ref": "razorfen-kraul-1",
            "uimap": 301,
            "decor": [(235, 20, 810, 110), (150, 447, 350, 655), (60, 505, 150, 655)],
            "start": [(717, 558), (740, 572), (675, 545)],
            "areas": {
                "Roogug": [(635, 505), (640, 455), (808, 343), (860, 400), (770, 430), (700, 460), (600, 460), (560, 450)],
                "Charlga Razorflank": [(877, 277), (800, 240), (740, 215), (840, 220)],
                "Aggem Thorncurse": [(573, 205), (620, 190), (680, 260), (640, 300), (700, 340), (570, 330), (600, 380), (650, 230)],
                "Death Speaker Jargba": [(470, 240), (430, 290), (500, 300), (440, 380), (490, 410), (420, 440), (520, 240)],
                "Agathelos the Raging": [(110, 215), (160, 250), (80, 280), (150, 300), (100, 350), (170, 375), (130, 330)],
                "Blind Hunter": [(80, 455), (55, 420), (110, 480)],
                # this piece is listed last: Charlga Razorflank, the last boss, stands on it
                "Overlord Ramtusk": [(220, 205), (290, 210), (360, 215), (270, 290), (260, 400), (310, 430), (350, 280), (370, 400), (300, 330)],
            },
            "aliases": {
                "Razorfen Warrior": "Roogug",
                "Razorfen Geomancer": "Roogug",
                "Stone Rumbler": "Roogug",
                "Razorfen Defender": "Roogug",
                "Razorfen Servitor": "Roogug",
                "Razorfen Quilguard": "Roogug",
                # met on a real run half an hour before Jargba, though the classic data has the
                # priests out west by Charlga: Forever has moved them
                "Razorfen Warden": "Roogug",
                "Death's Head Priest": "Roogug",
                # the boars roam the whole warren; a real run met them two minutes in,
                # on the edge of the first stretch
                "Agam'ar": "Roogug",
                "Death's Head Sage": "Aggem Thorncurse",
                "Death's Head Seer": "Roogug",
                "Razorfen Handler": "Roogug",
                "Tamed Hyena": "Death Speaker Jargba",
                "Ward Guardian": "Death Speaker Jargba",
                "Death's Head Ward Keeper": "Death Speaker Jargba",
                "Razorfen Dustweaver": "Roogug",
                "Wind Howler": "Overlord Ramtusk",
                "Razorfen Groundshaker": "Roogug",
                "Razorfen Totemic": "Charlga Razorflank",
                "Razorfen Beast Trainer": "Roogug",
                "Quilguard Champion": "Aggem Thorncurse",
                # (Forever's own; a real run met it between the Champion and Ramtusk)
                "Razorfen Earthbreaker": "Aggem Thorncurse",
                "Rotting Agam'ar": "Roogug",
                "Raging Agam'ar": "Roogug",
                "Razorfen Beastmaster": "Charlga Razorflank",
                "Blood of Agamaggan": "Roogug",
                "Earthcaller Halmgar": "Death Speaker Jargba",
                "Kraul Bat": "Agathelos the Raging",
                "Greater Kraul Bat": "Agathelos the Raging",
                "Razorfen Spearhide": "Charlga Razorflank",
                "Razorfen Stalker": "Charlga Razorflank",
                "Death's Head Acolyte": "Charlga Razorflank",
                "Death's Head Adept": "Roogug",
            },
        },
    ],
}
