# Excavation Site: Wetlands (a Forever dungeon). The game has no map sheet for it, so the sheet
# is tools/art/excavation-site-wetlands.png, painted by tools/codex_sheet.py from the
# instance's minimap. That minimap is a whole stretch of the Wetlands; the dungeon is the
# walled basin west of the river, and the sheet shows only that (crop in
# tools/draw_minimap_sheet.py). Areas are keyed by the instance's sub-zone names, with
# bosses as aliases.
# PLACED IN GAME (in-game minimap screenshots matched against the instance's minimap, then
# marked out in tools/map_editor.py): the way in east of the pond; Saltspine in the pond;
# Shadetooth at its west outlet, where the Thicket's stream valley begins; the Highland Horror
# in the little clearing north of the square dig; the Relic Guardian by the wooden platform at
# the valley's south side. The sheet is cropped to the ground the run goes through; its
# edges the run never reaches open with the Relic Guardian, so the sheet is whole at the end.
MAP = {'instance': 2998,
 'slug': 'excavation-site-wetlands',
 'bosses': {'Saltspine': (1, 531, 313),
            'Shadetooth': (1, 402, 339),
            'Relic Guardian': (1, 367, 483),
            'Highland Horror': (1, 128, 275)},
 'floors': [{'art': 'excavation-site-wetlands',
             'decor': [],
             'start': [(937, 289), (896, 222), (800, 176), (732, 205)],
             'areas': {'Lost Marsh': [(669, 316), (655, 231), (509, 250), (509, 370)],
                       "Stalker's Thicket": [(440, 354),
                                             (382, 340),
                                             (357, 373),
                                             (313, 306),
                                             (272, 367),
                                             (210, 346)],
                       'Lost Dig Site': [(155, 344), (121, 310), (127, 274), (66, 333), (128, 414)],
                       'Site of the Guardian': [(367, 476),
                                                (268, 490),
                                                (175, 469),
                                                (200, 70),
                                                (330, 40),
                                                (470, 40),
                                                (620, 40),
                                                (760, 40),
                                                (700, 580),
                                                (820, 600),
                                                (930, 580),
                                                (560, 620),
                                                (100, 560),
                                                (40, 180)]},
             # creatures by where a real run first met them (14 Nov)
             # (the game names the open ground between the parts after the zone)
             'aliases': {'Wetlands': 'Lost Marsh', 'Highland Snapper': 'Lost Marsh', 'Highland Tortoise': 'Lost Marsh',
                         'Elder Crocolisk': 'Lost Marsh', 'Young Crocolisk': 'Lost Marsh',
                         'Marsh Skulker': 'Lost Marsh', 'Marsh Crocolisk': 'Lost Marsh',
                         'Thicket Hunter': "Stalker's Thicket", 'Thicket Lurker': "Stalker's Thicket",
                         'Young Riptooth': "Stalker's Thicket", 'Thicket Matriarch': "Stalker's Thicket",
                         'Dragonmaw Warder': 'Lost Dig Site', 'Dragonmaw Saboteur': 'Lost Dig Site',
                         'Dragonmaw Thaumaturgist': 'Lost Dig Site', 'Thicket Stalker': 'Lost Dig Site',
                         'Highland Lurker': 'Lost Dig Site', 'Highland Spider': 'Site of the Guardian',
                         'Saltspine': 'Lost Marsh',
                         'Shadetooth': "Stalker's Thicket",
                         'Highland Horror': 'Lost Dig Site',
                         'Relic Guardian': 'Site of the Guardian'}}]}
