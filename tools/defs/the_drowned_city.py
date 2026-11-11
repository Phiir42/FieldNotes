# The Drowned City (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/the-drowned-city.png, drawn by tools/draw_minimap_sheet.py from the
# instance's minimap. Areas are keyed by the instance's sub-zone names, with bosses as aliases.
# WHERE each name sits on the sheet is a GUESS from the terrain and the
# encounter order: check in game and move the seeds.
MAP = {'instance': 2970,
 'slug': 'the-drowned-city',
 'floors': [{'art': 'the-drowned-city',
             'decor': [],
             'start': [(800, 280), (880, 290), (730, 260), (940, 295)],
             'areas': {'Eternal Amphitheater': [(490, 310),
                                                (400, 300),
                                                (610, 330),
                                                (500, 240),
                                                (500, 380),
                                                (640, 250),
                                                (600, 400)],
                       'The Unsinkable': [(530, 110), (480, 90), (590, 130), (520, 170)],
                       'Flooded Shrine': [(390, 200), (350, 240), (440, 180)],
                       'Deep Archives': [(510, 480), (470, 540), (560, 560), (420, 450), (600, 540)],
                       'Altar of the Serpent': [(290, 310), (210, 320), (250, 280)],
                       'Abyssal Dais': [(110, 320), (90, 130), (160, 200), (220, 220), (130, 430), (215, 410)]},
             'aliases': {"Ataal'Byzal": 'Eternal Amphitheater',
                         'Deathless Guardians': 'Eternal Amphitheater',
                         'Captain Dreadrise': 'The Unsinkable',
                         "Zul'Alai": 'Flooded Shrine',
                         "Var'Taka": 'Deep Archives',
                         'Primeval Elemental': 'Altar of the Serpent',
                         "Min'loth the Serpent": 'Abyssal Dais'}}]}
