# Krol'dok Stronghold (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/kroldok-stronghold.png, drawn by tools/draw_minimap_sheet.py from the
# instance's minimap. The instance has no sub-zones, so the areas uncover by boss.
# WHERE each name sits on the sheet is a GUESS from the terrain and the
# encounter order: check in game and move the seeds.
MAP = {'instance': 3039,
 'slug': 'kroldok-stronghold',
 'floors': [{'art': 'kroldok-stronghold',
             'decor': [],
             'start': [(300, 600), (250, 540), (350, 560)],
             'areas': {'Slavecrusher Grox': [(300, 330), (260, 420), (360, 430), (420, 490), (320, 380), (520, 530)],
                       'Twilight Commander Zarmok': [(430, 310), (480, 400), (530, 350), (560, 440)],
                       'Handler Ashka': [(580, 230), (540, 180), (640, 270), (690, 340), (500, 240)],
                       "Nar'gurk": [(740, 240), (750, 160), (720, 300)],
                       'Overseer Mugg': [(660, 80), (600, 90), (560, 130), (700, 50)]},
             'aliases': {}}]}
