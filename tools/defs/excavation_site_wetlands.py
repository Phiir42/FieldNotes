# Excavation Site: Wetlands (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/excavation-site-wetlands.png, painted by tools/codex_sheet.py from the
# instance's minimap. That minimap is a whole stretch of the Wetlands; the dungeon is the
# walled basin west of the river, and the sheet shows only that (crop in
# tools/draw_minimap_sheet.py). Areas are keyed by the instance's sub-zone names, with
# bosses as aliases.
# PLACED IN GAME (in-game minimap screenshots matched against the instance's minimap):
# the entrance, Saltspine (in the pond with the docks) and Shadetooth (at the pond's west
# outlet, with the Thicket raptors), so the Thicket is the stream valley running west, and
# the Highland Horror (in the little clearing with the bones, north of the square dig).
# STILL A GUESS from the terrain and the encounter order: the Lost Dig Site (the square
# dig with bones at the valley's west end) and the Site of the Guardian (the ruins with a
# stone ring in the north).
MAP = {'instance': 2998,
 'slug': 'excavation-site-wetlands',
 'bosses': {'Saltspine': (1, 516, 394), 'Shadetooth': (1, 478, 424), 'Highland Horror': (1, 320, 320)},
 'floors': [{'art': 'excavation-site-wetlands',
             'decor': [],
             'start': [(725, 290), (765, 305), (805, 320)],
             'areas': {'Lost Marsh': [(550, 370), (520, 340), (600, 360), (560, 420), (700, 430), (650, 300),
                                      (560, 230), (620, 200)],
                       "Stalker's Thicket": [(440, 410), (380, 400), (340, 440), (400, 500), (330, 510), (470, 610)],
                       'Lost Dig Site': [(228, 412), (250, 480), (180, 440), (120, 520), (260, 300), (330, 315), (70, 250), (90, 140), (40, 600)],
                       'Site of the Guardian': [(340, 140), (380, 90), (300, 200), (410, 170), (470, 250), (470, 30),
                                                # not yet seen: the north-east rim and the south, until placed
                                                (720, 130), (840, 180), (920, 300), (900, 420), (600, 540), (720, 590), (840, 520), (500, 600)]},
             'aliases': {'Saltspine': 'Lost Marsh',
                         'Shadetooth': "Stalker's Thicket",
                         'Highland Horror': 'Lost Dig Site',
                         'Relic Guardian': 'Site of the Guardian'}}]}
