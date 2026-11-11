# Ruins of Lordaeron (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/ruins-of-lordaeron.png, drawn by tools/draw_minimap_sheet.py from the
# instance's minimap. Areas are keyed by the instance's sub-zone names, with bosses as aliases.
# WHERE each name sits on the sheet is a GUESS from the terrain and the
# encounter order: check in game and move the seeds.
MAP = {'instance': 2999,
 'slug': 'ruins-of-lordaeron',
 'floors': [{'art': 'ruins-of-lordaeron',
             'decor': [],
             'start': [(510, 60), (510, 110), (505, 160)],
             'areas': {'Market Street': [(400, 110), (310, 110), (300, 220), (340, 300), (280, 330)],
                       "King's Alley": [(610, 110), (700, 110), (680, 220), (700, 320), (620, 330)],
                       'Lordaeron Graveyard': [(330, 430), (300, 500), (390, 520), (450, 450), (420, 560)],
                       'Lordamere Overlook': [(640, 470), (580, 540), (500, 600), (700, 430), (560, 430)],
                       "Rath'mael": [(505, 300), (505, 230), (505, 370), (450, 300), (560, 300)]},
             'aliases': {'Witherfang': 'Market Street',
                         'The Abandoned': 'Market Street',
                         'The Butcher': "King's Alley",
                         'Lordaeron Captain': "King's Alley",
                         'Viktor the Vile': 'Lordaeron Graveyard',
                         'Bjork': 'Lordamere Overlook'}}]}
