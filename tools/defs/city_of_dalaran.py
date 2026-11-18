# City of Dalaran (a Forever dungeon). The city is Wrath's Dalaran building
# (Forever's own copy of it, WMO 18950), set down in Alterac turned 66 degrees
# from where Northrend has it. The client still has Wrath's two Dalaran sheets
# (uiMap 125, the streets; 126, the Underbelly beneath them), so those are the
# sheets, kept the right way up: refs/city-of-dalaran-city.png and
# refs/city-of-dalaran-underbelly.png (named without a number so they stay out
# of the blank-parchment median), fetched with fetch_maps.stitch(125 / 126).
#
# Where the bosses stand: Wowhead's Forever spawn points (given on the Alterac
# Mountains map, uiMap 1416, which is this instance's own world frame), turned
# into Northrend's frame by the two placements of the building (Forever: world
# 275.1, 303.2, yaw 75; Northrend: 5824.9, 667.0, yaw 141) and onto the sheet
# by uiMap 125's bounds. Checked by laying sheet 125 over the instance's
# minimap that way: the streets meet. The "Mana Elemental" encounter is the
# Arcanic Enigma (Path of Renewal). The points have no height, so a boss under
# the streets would show on the street sheet above its spot: all are put on the
# streets, where every one of them lands on a drawn place (Atrexis's spot is
# also over the Circle of Wills; a run's sub-zones would settle it).
MAP = {'instance': 2959,
 'slug': 'city-of-dalaran',
 'bosses': {'Arcane Anomaly': (1, 697, 302),
            'Mana Wraith': (1, 716, 284),
            'Fel Ancient': (1, 497, 321),
            'Atrexis the Grave Knight': (1, 506, 343),
            'Mana Devourer': (1, 628, 426),
            'Mana Elemental': (1, 471, 142),
            'Lyn the Ignored': (1, 582, 179),
            'Unstable Sentinel': (1, 397, 213),
            'Shade of the Archmage': (1, 242, 259)},
 'floors': [{'ref': 'city-of-dalaran-city',
             'uimap': 125,
             'paper': True,  # Wrath's paper is lighter than the dungeon sheets': a blank of its own
             'threshold': 45,  # and stained: only what stands out more is the city
             # title banner, the Kirin Tor eye, the clouds and the compass
             'decor': [(28, 40, 420, 112), (805, 40, 990, 245), (0, 0, 130, 210), (0, 380, 215, 668),
                       (790, 380, 1002, 668), (215, 590, 330, 668), (880, 0, 1002, 40)],
             'areas': {'Arcane Anomaly': [(727, 305), (765, 300), (700, 330), (690, 270), (745, 340), (790, 260)],
                       'Mana Devourer': [(720, 495), (660, 440), (600, 420), (700, 560), (760, 450), (640, 510),
                                         (580, 380), (690, 465), (780, 520)],
                       'Fel Grove': [(490, 320), (450, 280), (540, 290), (500, 370), (440, 345), (560, 340)],
                       'The Eventide': [(480, 440), (520, 470), (440, 470), (555, 420), (500, 520), (430, 520)],
                       'The Silver Enclave': [(345, 465), (300, 500), (380, 400), (395, 525), (270, 440),
                                              (340, 550), (330, 380)],
                       'Unstable Sentinel': [(420, 230), (360, 190), (400, 270), (465, 200), (375, 250), (330, 230),
                                             (300, 190)],
                       'Mana Elemental': [(460, 120), (520, 110), (410, 100), (480, 160), (440, 70), (360, 120)],
                       'Lyn the Ignored': [(580, 175), (610, 110), (660, 150), (690, 215), (540, 200), (610, 250),
                                           (660, 90), (730, 180)],
                       'Shade of the Archmage': [(240, 305), (190, 280), (240, 370), (240, 230), (300, 330),
                                                 (165, 330), (200, 420), (250, 160)]},
             'aliases': {"Krasus' Landing": 'Arcane Anomaly',
                         'Mana Wraith': 'Arcane Anomaly',
                         'The Violet Hold': 'Mana Devourer',
                         'Fel Ancient': 'Fel Grove',
                         'Runeweaver Square': 'Fel Grove',
                         'Atrexis the Grave Knight': 'Fel Grove',
                         "A Hero's Welcome": 'The Silver Enclave',
                         'Magus Commerce Exchange': 'Unstable Sentinel',
                         'Trade District': 'Unstable Sentinel',
                         'Arcanic Enigma': 'Mana Elemental',
                         'Path of Renewal': 'Mana Elemental',
                         'Antonidas Memorial': 'Mana Elemental',
                         "Sunreaver's Sanctuary": 'Lyn the Ignored',
                         'The Violet Citadel': 'Shade of the Archmage'}},
            # The sewers: entered by the Sewer gate at the end of the long
            # south-west pipe (where the building's "Sewer" group lies).
            {'ref': 'city-of-dalaran-underbelly',
             'uimap': 126,
             'paper': True,
             'decor': [(28, 40, 420, 112), (805, 40, 990, 245), (0, 0, 130, 210), (0, 400, 140, 668),
                       (140, 560, 300, 668), (790, 380, 1002, 668), (880, 0, 1002, 40)],
             'start': [(165, 505), (205, 465), (245, 425)],
             'areas': {'The Underbelly': [(480, 250), (430, 330), (560, 300), (500, 400), (600, 250), (380, 220),
                                          (560, 430), (450, 180), (490, 297), (590, 360), (250, 285), (320, 275),
                                          (610, 90), (560, 160), (670, 330), (630, 320)],
                       'Cantrips & Crows': [(335, 385), (345, 345), (400, 405), (400, 455), (450, 470),
                                            (370, 330), (290, 360)]},
             'aliases': {'Sewer': 'The Underbelly',
                         'The Cantrips and Crows Tavern': 'Cantrips & Crows',
                         'Circle of Wills': 'The Underbelly'}}]}
