MAP = {
    "instance": 409,
    "slug": "molten-core",
    "path": True,  # one road: areas are listed in the order you pass through them
    "floors": [
        {
            "ref": "molten-core-1",
            "uimap": 232,
            "decor": [(600, 25, 995, 110), (548, 55, 600, 108), (15, 290, 250, 650), (250, 535, 340, 650), (340, 575, 455, 650)],
            "start": [(265, 150), (290, 178), (310, 135), (200, 110)],
            # not one road: Lucifron and Magmadar's cavern is a dead end, and
            # beyond Geddon and Shazzrah the rest are taken in any order
            # (Golemagg's hall is the one named for Geddon, Majordomo's the
            # one named for Golemagg: bosses go where they stand)
            "roads": [["Molten Giant", "Gehennas", "Garr", "Shazzrah"], ["Magmadar Cavern"], ["Baron Geddon"],
                      ["Golemagg the Incinerator"], ["Sulfuron Harbinger"], ["Ragnaros' Lair"]],
            "areas": {
                "Molten Giant": [(380, 110), (450, 90), (500, 135), (420, 170), (520, 80), (400, 215)],
                "Magmadar Cavern": [(690, 158), (657, 252), (700, 120), (635, 285), (722, 215), (590, 215), (550, 195)],
                "Gehennas": [(333, 325), (380, 265), (395, 310), (350, 370)],
                "Garr": [(308, 465), (280, 490), (330, 415), (390, 430)],
                "Shazzrah": [(523, 518), (550, 565), (450, 490), (400, 520), (500, 610), (600, 600)],
                "Baron Geddon": [(685, 390), (680, 330), (740, 490), (640, 440), (760, 370), (700, 450)],
                "Golemagg the Incinerator": [(840, 438), (865, 460), (800, 400), (810, 470)],
                "Sulfuron Harbinger": [(828, 553), (780, 530), (720, 580), (700, 520)],
                "Ragnaros' Lair": [(558, 360), (515, 340), (610, 350), (560, 410), (555, 300), (450, 370), (480, 270)],
            },
            "aliases": {
                "Molten Destroyer": "Molten Giant",
                "Lucifron": "Magmadar Cavern",
                "Magmadar": "Magmadar Cavern",
                "Flamewaker Protector": "Magmadar Cavern",
                "Core Hound": "Magmadar Cavern",
                "Ancient Core Hound": "Magmadar Cavern",
                "Flamewaker": "Gehennas",
                "Firesworn": "Garr",
                "Lava Surger": "Garr",
                "Majordomo Executus": "Shazzrah",
                "Flamewaker Healer": "Shazzrah",
                "Flamewaker Elite": "Shazzrah",
                "Core Rager": "Golemagg the Incinerator",
                "Golemagg": "Golemagg the Incinerator",
                "Flamewaker Priest": "Sulfuron Harbinger",
                "Sulfuron": "Sulfuron Harbinger",
                "Ragnaros": "Ragnaros' Lair",
                "Ragnaros Lair": "Ragnaros' Lair",
                "Son of Flame": "Ragnaros' Lair",
            },
        },
    ],
}
