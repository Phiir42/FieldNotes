MAP = {
    "instance": 48,
    "slug": "blackfathom-deeps",
    "path": "sheets",  # each sheet is one road of its own, areas in the order you pass through them
    "creatures": "auto",  # file creatures by their spawn points (see make_maps.creature_rooms)
    # The sheets are met one after another (a real run went 1, 2, 3), so a
    # creature that lives on more than one is filed on the earliest only:
    # naga and satyrs met on the first sheet used to uncover the second.
    "in_order": True,
    # Baron Aquanis stands nowhere: he rises where the Fathom Core is taken from
    # the Fathom Stone (the stone's own spot on the second sheet).
    "bosses": {"Baron Aquanis": (2, 415, 504)},
    "floors": [
        {
            "ref": "blackfathom-deeps-1",
            "uimap": 221,
            "decor": [(335, 15, 735, 64), (250, 25, 335, 97), (735, 25, 815, 97), (700, 90, 1002, 230), (682, 230, 1002, 640)],
            "start": [(458, 75), (370, 95), (500, 100), (435, 90)],
            "areas": {
                "The Drowned Sacellum": [(530, 260), (535, 165), (560, 220), (460, 265), (630, 200), (430, 240), (410, 300), (520, 310)],
                "The Pool of Ask'ar": [(320, 332), (330, 270), (420, 400), (250, 400), (240, 460), (330, 500), (200, 490),
                                       (320, 570), (190, 365), (390, 340), (440, 460), (420, 622), (350, 598), (260, 330)],
                "Lady Sarevess": [(330, 403), (305, 385), (360, 420), (335, 375), (330, 432)],
                "Gelihast": [(112, 265), (200, 255), (125, 290), (215, 285), (170, 290)],
                # this piece (the tunnel east, where Gelihast stands) is walked last on this sheet
                "Ghamoo-ra": [(545, 378), (570, 430), (560, 480), (620, 450), (660, 445), (555, 540), (510, 595)],
            },
            "aliases": {
                "Drowned Sacellum": "The Drowned Sacellum",
                "Skittering Crustacean": "The Drowned Sacellum",
                "Snapping Crustacean": "The Drowned Sacellum",
                "Murkshallow Snapclaw": "Ghamoo-ra",
                "Aku'mai Fisher": "Ghamoo-ra",
                "Pool of Ask'ar": "The Pool of Ask'ar",
                "Blackfathom Sea Witch": "The Pool of Ask'ar",
                "Blackfathom Myrmidon": "The Pool of Ask'ar",
                "Blackfathom Tide Priestess": "The Pool of Ask'ar",
                "Blackfathom Oracle": "The Pool of Ask'ar",
                "Domina": "Lady Sarevess",
                "Shrine of Gelihast": "Gelihast",
                "Murkshallow Softshell": "Gelihast",
                "Blindlight Murloc": "Gelihast",
                "Blindlight Muckdweller": "Gelihast",
                "Blindlight Oracle": "Gelihast",
                "Subjugator Kor'ul": "Gelihast",
                # met in the tunnel before Gelihast on a real run, though the
                # classic spawn points have the acolytes in the Moonshrine only
                "Twilight Acolyte": "Ghamoo-ra",
            },
        },
        {
            "ref": "blackfathom-deeps-2",
            "uimap": 222,
            "decor": [(222, 12, 788, 103), (610, 100, 1002, 480), (478, 280, 610, 392), (870, 470, 1002, 525)],
            "areas": {
                "Fallenroot Satyr": [(380, 150), (345, 190), (435, 170), (400, 230), (385, 290), (365, 330), (320, 385)],
                "Moonshrine Ruins": [(310, 515), (400, 430), (380, 480), (445, 440), (430, 560), (315, 435), (410, 520), (440, 590)],
                "Moonshrine Sanctum": [(527, 545), (565, 466), (500, 510), (530, 595), (555, 510)],
                "Aku'mai's Lair": [(860, 577), (790, 565), (825, 500), (720, 568), (650, 575), (612, 525), (670, 600), (890, 560)],
            },
            "aliases": {
                "Fallenroot Rogue": "Fallenroot Satyr",
                "Fallenroot Shadowstalker": "Fallenroot Satyr",
                "Fallenroot Hellcaller": "Fallenroot Satyr",
                "Twilight Reaver": "Fallenroot Satyr",
                "Lorgus Jett": "Moonshrine Ruins",
                "Twilight Aquamancer": "Moonshrine Ruins",
                "Twilight Loreseeker": "Moonshrine Ruins",
                "Twilight Shadowmage": "Moonshrine Ruins",
                "Twilight Elementalist": "Moonshrine Ruins",
                "Aku'mai Snapjaw": "Moonshrine Ruins",
                "Barbed Crustacean": "Moonshrine Ruins",
                "Twilight Lord Kelris": "Moonshrine Sanctum",
                "Kelris": "Moonshrine Sanctum",
                "Twilight Lord Bathiel": "Moonshrine Sanctum",
                "Aku'mai": "Aku'mai's Lair",
                "Akumais Lair": "Aku'mai's Lair",
                "Aku'mai Servant": "Aku'mai's Lair",
                "Morridune": "Aku'mai's Lair",
            },
        },
        {
            "ref": "blackfathom-deeps-3",
            "uimap": 223,
            "decor": [(222, 12, 790, 103)],
            "areas": {
                "The Forgotten Pool": [(590, 200), (560, 280), (650, 300), (530, 400), (440, 420), (725, 193), (450, 330),
                                       (480, 240), (590, 130), (300, 230), (250, 400), (350, 600), (420, 520), (280, 520), (380, 180)],
            },
            "aliases": {
                "Forgotten Pool": "The Forgotten Pool",
                "Old Serra'kis": "The Forgotten Pool",
                "Deep Pool Threshfin": "The Forgotten Pool",
                "Thruk": "The Forgotten Pool",
            },
        },
    ],
}
