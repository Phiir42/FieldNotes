# City of Dalaran (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/city-of-dalaran.png, drawn by tools/draw_minimap_sheet.py from the
# instance's minimap. Areas uncover by boss (and the Fel Grove sub-zone).
# WHERE each name sits on the sheet is a GUESS from the terrain and the
# encounter order: check in game and move the seeds.
MAP = {'instance': 2959,
 'slug': 'city-of-dalaran',
 'floors': [{'art': 'city-of-dalaran',
             'decor': [],
             'start': [(650, 540), (690, 470), (600, 590)],
             'areas': {'Arcane Anomaly': [(590, 500), (640, 440), (560, 420)],
                       'Mana Devourer': [(500, 320), (470, 250), (540, 280), (420, 340), (500, 380)],
                       'Fel Grove': [(680, 170), (620, 110), (730, 280), (560, 80), (750, 380)],
                       'Unstable Sentinel': [(660, 300), (640, 350), (690, 350)],
                       'Lyn the Ignored': [(330, 250), (330, 350), (290, 300), (260, 420), (320, 430)],
                       'Atrexis the Grave Knight': [(450, 520), (440, 570), (400, 480), (520, 470), (380, 580)],
                       'Shade of the Archmage': [(410, 130), (350, 170), (470, 170), (330, 80)]},
             'aliases': {'Mana Elemental': 'Mana Devourer',
                         'Fel Ancient': 'Fel Grove',
                         'Mana Wraith': 'Shade of the Archmage'}}]}
