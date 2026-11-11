# The Hall of Thanes (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/the-hall-of-thanes.png, drawn by tools/draw_minimap_sheet.py from the
# instance's minimap. The instance has no sub-zones, so the areas uncover by boss.
# WHERE each name sits on the sheet is a GUESS from the terrain and the
# encounter order: check in game and move the seeds.
MAP = {'instance': 3065,
 'slug': 'the-hall-of-thanes',
 'floors': [{'art': 'the-hall-of-thanes',
             'decor': [],
             'start': [(497, 610), (497, 560)],
             'areas': {'Faldrim Anvilmar': [(497, 495),
                                            (440, 497),
                                            (555, 497),
                                            (370, 497),
                                            (625, 497),
                                            (450, 545),
                                            (545, 545)],
                       'Infurnus': [(497, 420), (640, 400), (580, 410)],
                       'Plunder': [(340, 250),
                                   (330, 350),
                                   (420, 330),
                                   (640, 150),
                                   (670, 280),
                                   (590, 330),
                                   (497, 340),
                                   (620, 60),
                                   (400, 380)],
                       'Durgen Dirgehammer': [(497, 248), (497, 290)]},
             'aliases': {}}]}
