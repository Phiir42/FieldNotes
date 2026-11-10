MAP = {
    "instance": 329,
    "slug": "stratholme",
    "floors": [
        {
            # Main gate ("live" / Scarlet side)
            "ref": "stratholme-1",
            "uimap": 317,
            "decor": [(330, 5, 725, 72), (330, 72, 425, 98), (660, 72, 715, 88), (285, 350, 480, 548)],
            "start": [(640, 585), (688, 585), (520, 562), (800, 562), (608, 535), (718, 535)],
            "areas": {
                "King's Square": [(600, 450), (690, 450), (640, 380), (560, 400), (590, 300), (590, 230),
                                  (700, 345), (685, 332), (780, 350), (700, 260), (530, 330), (760, 420),
                                  (540, 470), (680, 200), (760, 230)],
                "Market Row": [(605, 137), (520, 130), (480, 110), (560, 170), (650, 120), (600, 185),
                               (540, 80), (640, 170)],
                "Crusaders' Square": [(348, 133), (347, 165), (400, 180), (440, 190), (380, 250), (410, 290),
                                      (300, 160), (460, 240), (440, 110)],
                "Festival Lane": [(903, 172), (760, 125), (830, 120), (870, 200), (890, 260), (850, 310),
                                  (730, 100), (800, 80), (920, 230), (700, 110)],
                "The Scarlet Bastion": [(330, 222), (290, 215), (240, 235), (255, 265), (225, 270)],
                "Cannon Master Willey": [(297, 270), (300, 300), (330, 285)],
                "The Hall of Lights": [(240, 320), (215, 345), (225, 375), (215, 420), (235, 450), (220, 480)],
                "The Hoard": [(85, 288), (40, 340), (70, 370), (110, 345), (150, 365), (180, 345), (120, 320)],
                "The Crimson Throne": [(283, 575), (205, 545), (270, 497), (245, 510)],
            },
            "aliases": {
                # sub-zone spelling variants
                "Kings Square": "King's Square",
                "Crusader's Square": "Crusaders' Square",
                "Scarlet Bastion": "The Scarlet Bastion",
                "Hall of Lights": "The Hall of Lights",
                "Crimson Throne": "The Crimson Throne",
                # King's Square
                "Skul": "King's Square",
                "Fras Siabi": "King's Square",
                "Stratholme Courier": "King's Square",
                # Market Row
                "Postmaster Malown": "Market Row",
                "The Unforgiven": "Market Row",
                "Vengeful Phantom": "Market Row",
                "Undead Postman": "Market Row",
                # Crusaders' Square
                "Timmy the Cruel": "Crusaders' Square",
                # Festival Lane
                "Hearthsinger Forresten": "Festival Lane",
                "Stonespine": "Festival Lane",
                # Scarlet Bastion entrance rooms
                "Crimson Guardsman": "The Scarlet Bastion",
                "Crimson Conjuror": "The Scarlet Bastion",
                "Crimson Initiate": "The Scarlet Bastion",
                "Crimson Gallant": "The Scarlet Bastion",
                "Crimson Hammersmith": "The Scarlet Bastion",
                # Willey's room
                "Crimson Rifleman": "Cannon Master Willey",
                "Willey Hopebreaker": "Cannon Master Willey",
                # Hall of Lights
                "Crimson Monk": "The Hall of Lights",
                "Crimson Priest": "The Hall of Lights",
                "Crimson Defender": "The Hall of Lights",
                "Crimson Sorcerer": "The Hall of Lights",
                "Crimson Battle Mage": "The Hall of Lights",
                "Crimson Inquisitor": "The Hall of Lights",
                # The Hoard
                "Malor the Zealous": "The Hoard",
                "Commander Malor": "The Hoard",
                # Crimson Throne
                "Archivist Galford": "The Crimson Throne",
                "Instructor Galford": "The Crimson Throne",
                "Grand Crusader Dathrohan": "The Crimson Throne",
                "Balnazzar": "The Crimson Throne",
            },
        },
        {
            # Service entrance ("dead" / Scourge side)
            "ref": "stratholme-2",
            "uimap": 318,
            "decor": [(40, 525, 440, 615), (15, 165, 345, 525), (345, 280, 440, 395), (345, 400, 385, 490)],
            "start": [(658, 605), (655, 570)],
            "areas": {
                "Elders' Square": [(577, 467), (640, 500), (680, 480), (620, 540), (690, 530), (688, 435),
                                   (640, 430), (610, 395), (510, 450), (510, 540), (530, 600), (600, 520)],
                "The Gauntlet": [(640, 245), (630, 190), (605, 183), (690, 220), (650, 350), (620, 330),
                                 (700, 270), (560, 230), (690, 370), (640, 290)],
                "Nerub'enkan": [(572, 305), (540, 320), (472, 320), (520, 370), (500, 280), (560, 345)],
                "Baroness Anastari": [(745, 305), (775, 315), (817, 245), (790, 375), (740, 250), (740, 355)],
                "Maleki the Pallid": [(677, 140), (700, 120), (752, 77), (720, 170), (660, 90)],
                "Slaughter Square": [(447, 47), (405, 42), (452, 130), (470, 170), (570, 100), (540, 140), (600, 110),
                                     (520, 80), (540, 190), (490, 200)],
                "The Slaughter House": [(392, 130), (352, 68), (370, 203), (360, 150), (400, 250), (430, 220)],
            },
            "aliases": {
                "Elder's Square": "Elders' Square",
                "Gauntlet": "The Gauntlet",
                "Slaughter House": "The Slaughter House",
                # Elders' Square
                "Magistrate Barthilas": "Elders' Square",
                "Service Entrance": "Elders' Square",
                # Gauntlet
                "Black Guard Swordsmith": "The Gauntlet",
                "Rockwing Gargoyle": "The Gauntlet",
                "Rockwing Screecher": "The Gauntlet",
                # Ziggurats
                "Nerubenkan": "Nerub'enkan",
                "Crypt Crawler": "Nerub'enkan",
                "Crypt Beast": "Nerub'enkan",
                "Baroness Anastari's Ziggurat": "Baroness Anastari",
                "Maleki": "Maleki the Pallid",
                # Slaughter Square
                "Ramstein the Gorger": "Slaughter Square",
                "Venom Belcher": "Slaughter Square",
                "Bile Spewer": "Slaughter Square",
                "Bile Slime": "Slaughter Square",
                "Black Guard Sentry": "Slaughter Square",
                "Mindless Undead": "Slaughter Square",
                # Slaughter House
                "Baron Rivendare": "The Slaughter House",
                "Lord Aurius Rivendare": "The Slaughter House",
            },
        },
    ],
}
