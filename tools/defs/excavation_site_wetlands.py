# Excavation Site: Wetlands (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/excavation-site-wetlands.png, painted by tools/codex_sheet.py from the
# instance's minimap. That minimap is a whole stretch of the Wetlands; the dungeon is the
# walled basin west of the river, and the sheet shows only that (crop in
# tools/draw_minimap_sheet.py). Areas are keyed by the instance's sub-zone names, with
# bosses as aliases.
# PLACED IN GAME: the entrance (matched against the in-game minimap on arrival) and the
# Lost Marsh (the pond with docks, Marsh Crocolisks and Saltspine).
# STILL A GUESS from the terrain and the encounter order: the other three areas.
MAP = {'instance': 2998,
 'slug': 'excavation-site-wetlands',
 'floors': [{'art': 'excavation-site-wetlands',
             'decor': [],
             'start': [(725, 290), (765, 305), (805, 320)],
             'areas': {'Lost Marsh': [(550, 370), (520, 340), (600, 360), (560, 420), (700, 430), (650, 300), (760, 590)],
                       "Stalker's Thicket": [(560, 230), (480, 250), (430, 320), (620, 200)],
                       'Lost Dig Site': [(340, 140), (380, 90), (300, 200), (410, 170), (300, 300)],
                       'Site of the Guardian': [(228, 412), (300, 440), (380, 420), (390, 510), (250, 500)]},
             'aliases': {'Saltspine': 'Lost Marsh',
                         'Shadetooth': "Stalker's Thicket",
                         'Highland Horror': 'Lost Dig Site',
                         'Relic Guardian': 'Site of the Guardian'}}]}
