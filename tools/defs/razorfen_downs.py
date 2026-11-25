MAP = {
    "instance": 129,
    # on the skulls painted on the sheet, which agree with where the classic data puts them
    "bosses": {"Amnennar the Coldbringer": (1, 444, 403)},
    "slug": "razorfen-downs",
    "path": True,  # one road: areas are listed in the order you pass through them
    "floors": [
        {
            "ref": "razorfen-downs-1",
            "uimap": 300,
            "decor": [(245, 10, 800, 88), (240, 40, 330, 98), (745, 60, 808, 97), (700, 60, 745, 91), (612, 385, 965, 655)],
            "start": [(237, 127), (262, 140)],
            "areas": {
                "Death's Head Geomancer": [(310, 150), (400, 120), (470, 135), (440, 190), (340, 200), (300, 270), (490, 240), (370, 165), (290, 330)],
                "The Caller's Chamber": [(590, 228), (563, 172), (545, 215), (645, 255), (600, 290)],
                "The Murder Pens": [(732, 105), (760, 150), (820, 125), (740, 200), (830, 190), (700, 175), (690, 250)],
                "The Bone Pile": [(858, 310), (858, 342), (800, 270), (900, 290), (840, 370), (740, 325), (670, 330)],
                # named after its boss: the game calls the way in "Spiral of Thorns" too, long
                # before the spiral itself (a real run, 2026-11-23)
                "Glutton": [(345, 443), (330, 370), (400, 492), (428, 528), (520, 480), (560, 410), (520, 335), (270, 400), (225, 420), (430, 325), (480, 560)],
                "Amnennar the Coldbringer": [(443, 402), (400, 365), (485, 440), (430, 455), (470, 370)],
            },
            "aliases": {
                "Withered Warrior": "Death's Head Geomancer",
                "Withered Battle Boar": "Death's Head Geomancer",
                "Withered Spearhide": "Death's Head Geomancer",
                "Withered Quilguard": "Death's Head Geomancer",
                "Death's Head Cultist": "Death's Head Geomancer",
                "Razorfen Battleguard": "Death's Head Geomancer",
                "Tuten'kash": "The Caller's Chamber",
                "Tomb Fiend": "The Caller's Chamber",
                "Tomb Reaver": "The Caller's Chamber",
                "Plaguemaw the Rotting": "The Murder Pens",
                "Belnistrasz": "The Murder Pens",
                "Withered Reaver": "Death's Head Geomancer",
                "Mordresh Fire Eye": "The Bone Pile",
                "Spiral of Thorns": "Death's Head Geomancer",
                "Battle Boar Horror": "Death's Head Geomancer",
                "Ragglesnout": "Glutton",
                "Boneflayer Ghoul": "Death's Head Geomancer",
                "Thorn Eater Ghoul": "Glutton",
                "Skeletal Frostweaver": "Death's Head Geomancer",
                "Splinterbone Centurion": "Death's Head Geomancer",
                "Splinterbone Warrior": "Glutton",
                "Frozen Soul": "Death's Head Geomancer",
                "Freezing Spirit": "Death's Head Geomancer",
                "Frost Spectre": "Amnennar the Coldbringer",
                "Skeletal Summoner": "Death's Head Geomancer",
                "Skeletal Shadowcaster": "Amnennar the Coldbringer",
                "Splinterbone Captain": "Amnennar the Coldbringer",
            },
        },
    ],
}
