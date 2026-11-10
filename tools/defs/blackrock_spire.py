SCARSHIELD = {
    "Scarshield Legionnaire": "Hall of Blackhand", "Scarshield Acolyte": "Hall of Blackhand",
    "Scarshield Raider": "Hall of Blackhand", "Scarshield Worg": "Hall of Blackhand",
    "Scarshield Spellbinder": "Hall of Blackhand", "Scarshield Warlock": "Hall of Blackhand",
    "Scarshield Quartermaster": "Hall of Blackhand", "Scarshield Sentry": "Hall of Blackhand",
    "Scarshield Infiltrator": "Hall of Blackhand", "Blackrock Spire": "Hall of Blackhand",
}
OGRES = {
    "Highlord Omokk": "Tazz'Alor", "Spirestone Enforcer": "Tazz'Alor", "Spirestone Ogre Magus": "Tazz'Alor",
    "Spirestone Reaver": "Tazz'Alor", "Spirestone Mystic": "Tazz'Alor", "Spirestone Warlord": "Tazz'Alor",
    "Spirestone Butcher": "Tazz'Alor", "Spirestone Battle Mage": "Tazz'Alor",
    "Spirestone Lord Magus": "Tazz'Alor", "Tazzalor": "Tazz'Alor",
}
TROLLS = {
    "Shadow Hunter Vosh'gajin": "Hordemar City", "War Master Voone": "Hordemar City",
    "Smolderthorn Mystic": "Hordemar City", "Smolderthorn Shadow Priest": "Hordemar City",
    "Smolderthorn Berserker": "Hordemar City", "Smolderthorn Axe Thrower": "Hordemar City",
    "Smolderthorn Seer": "Hordemar City", "Smolderthorn Witch Doctor": "Hordemar City",
    "Smolderthorn Headhunter": "Hordemar City", "Smolderthorn Shadow Hunter": "Hordemar City",
    "Bannok Grimaxe": "Hordemar City",
}
SPIDERS = {
    "Mother Smolderweb": "Skitterweb Tunnels", "Spire Spider": "Skitterweb Tunnels",
    "Spire Spiderling": "Skitterweb Tunnels", "Crystal Fang": "Skitterweb Tunnels",
    "Spire Scorpid": "Skitterweb Tunnels",
}
FIREBRAND = {
    "Quartermaster Zigris": "Skitterweb Tunnels", "Firebrand Grunt": "Skitterweb Tunnels",
    "Firebrand Legionnaire": "Skitterweb Tunnels", "Firebrand Darkweaver": "Skitterweb Tunnels",
    "Firebrand Invoker": "Skitterweb Tunnels", "Firebrand Pyromancer": "Skitterweb Tunnels",
    "Firebrand Dreadweaver": "Skitterweb Tunnels",
}
BANNER = (195, 0, 825, 91)


def merge(*parts):
    out = {}
    for part in parts:
        out.update(part)
    return out


MAP = {
    "instance": 229,
    "slug": "blackrock-spire",
    "floors": [
        {
            "ref": "blackrock-spire-1",
            "uimap": 250,
            "decor": [BANNER, (695, 160, 1002, 610)],
            "areas": {
                "Tazz'Alor": [(610, 388), (523, 385), (580, 360), (640, 420), (560, 425), (485, 400), (500, 455), (545, 470)],
                "Hordemar City": [(498, 290), (560, 318), (630, 315), (670, 330)],
                "Skitterweb Tunnels": [(625, 500), (625, 468), (580, 515), (655, 480)],
            },
            "aliases": merge(OGRES, TROLLS, SPIDERS, {"Urok Doomhowl": "Tazz'Alor"}),
        },
        {
            "ref": "blackrock-spire-2",
            "uimap": 251,
            "decor": [BANNER],
            "areas": {
                "Hordemar City": [(520, 320), (540, 385), (600, 385), (640, 360), (600, 425), (660, 420), (555, 462), (580, 340)],
                "Skitterweb Tunnels": [(668, 518), (618, 493), (650, 478), (540, 500), (585, 505)],
            },
            "aliases": merge(TROLLS, SPIDERS),
        },
        {
            "ref": "blackrock-spire-3",
            "uimap": 252,
            "decor": [BANNER],
            "areas": {
                "Mok'Doom": [(388, 348), (385, 390), (435, 385), (365, 430)],
                "Hordemar City": [(600, 315), (540, 270), (600, 270), (660, 280), (600, 380), (640, 410), (520, 383), (670, 320)],
                "War Master Voone": [(460, 440), (490, 475), (530, 450)],
            },
            "aliases": merge(TROLLS, {
                "Urok Doomhowl": "Mok'Doom", "Mokdoom": "Mok'Doom", "Urok Enforcer": "Mok'Doom",
                "Urok Ogre Magus": "Mok'Doom", "Ghok Bashguud": "Mok'Doom",
                "War Master Voone": "War Master Voone", "Bannok Grimaxe": "War Master Voone",
                "Smolderthorn Berserker": "War Master Voone",
            }),
        },
        {
            "ref": "blackrock-spire-4",
            "uimap": 253,
            "decor": [BANNER, (695, 55, 1002, 625)],
            "start": [(368, 282)],
            "areas": {
                "Hall of Blackhand": [(338, 243), (385, 322), (405, 300)],
                "Hordemar City": [(530, 197), (490, 240), (525, 250), (470, 300), (445, 300)],
                "Skitterweb Tunnels": [(505, 412), (455, 370), (440, 400), (430, 470), (430, 500)],
            },
            "aliases": merge(SCARSHIELD, TROLLS, SPIDERS, FIREBRAND),
        },
        {
            "ref": "blackrock-spire-5",
            "uimap": 254,
            "decor": [BANNER, (15, 325, 288, 645), (288, 385, 328, 645)],
            "areas": {
                "Bloodaxe Veteran": [(380, 410), (385, 465), (345, 465), (420, 470), (440, 380), (440, 440)],
                "Halycon's Lair": [(380, 590), (385, 545), (400, 515)],
                "The Storehouse": [(540, 603), (540, 565), (480, 527), (530, 530)],
            },
            "aliases": {
                "Bloodaxe Raider": "Bloodaxe Veteran", "Bloodaxe Worg": "Bloodaxe Veteran",
                "Bloodaxe Evoker": "Bloodaxe Veteran", "Bloodaxe Summoner": "Bloodaxe Veteran",
                "Bloodaxe Warmonger": "Bloodaxe Veteran", "Bloodaxe Worg Pup": "Bloodaxe Veteran",
                "Quartermaster Zigris": "Bloodaxe Veteran", "Ghok Bashguud": "Bloodaxe Veteran",
                "Halycon": "Halycon's Lair", "Gizrul the Slavener": "Halycon's Lair",
                "Halycons Lair": "Halycon's Lair",
                "Overlord Wyrmthalak": "The Storehouse", "Spirestone Warlord": "The Storehouse",
                "Smolderthorn Berserker": "The Storehouse", "Burning Felguard": "The Storehouse",
            },
        },
        {
            "ref": "blackrock-spire-6",
            "uimap": 255,
            "decor": [BANNER, (695, 85, 1002, 525)],
            "areas": {
                "Hall of Binding": [(268, 128), (300, 180), (300, 150), (300, 210)],
                "Dragonspire Hall": [(365, 150), (340, 110), (385, 110)],
                "The Rookery": [(330, 255), (295, 235), (380, 235), (360, 285)],
                "Chamber of Battle": [(580, 340), (578, 405), (470, 403), (530, 403)],
            },
            "aliases": {
                "Pyroguard Emberseer": "Hall of Binding", "Blackhand Incarcerator": "Hall of Binding",
                "Blackhand Summoner": "Dragonspire Hall", "Blackhand Veteran": "Dragonspire Hall",
                "Blackhand Dreadweaver": "Dragonspire Hall", "Upper Blackrock Spire": "Dragonspire Hall",
                "Solakar Flamewreath": "The Rookery", "Rookery Whelp": "The Rookery",
                "Rookery Guardian": "The Rookery", "Rookery Hatcher": "The Rookery",
                "Father Flame": "The Rookery", "Rookery": "The Rookery",
                "Blackrock Stadium": "Chamber of Battle", "Warchief Rend Blackhand": "Chamber of Battle",
                "Gyth": "Chamber of Battle", "The Furnace": "Chamber of Battle",
                "The Beast": "Chamber of Battle", "Spire Throne": "Chamber of Battle",
                "General Drakkisath": "Chamber of Battle", "Lord Valthalak": "Chamber of Battle",
                "Goraluk Anvilcrack": "Chamber of Battle", "Jed Runewatcher": "Chamber of Battle",
                "Hall of Blackhand": "Chamber of Battle", "Blackhand Elite": "Chamber of Battle",
                "Blackhand Dragon Handler": "Chamber of Battle", "Blackhand Assassin": "Chamber of Battle",
                "Blackhand Iron Guard": "Chamber of Battle", "Chromatic Whelp": "Chamber of Battle",
                "Chromatic Dragonspawn": "Chamber of Battle", "Chromatic Elite Guard": "Chamber of Battle",
                "Rage Talon Dragonspawn": "Chamber of Battle", "Rage Talon Flamescale": "Chamber of Battle",
                "Rage Talon Dragon Guard": "Chamber of Battle", "Rage Talon Captain": "Chamber of Battle",
                "Rage Talon Fire Tongue": "Chamber of Battle",
            },
        },
    ],
}


# Every floor's sheet also carries a faint silhouette of the whole spire
# (x 240-690, y 85-600). It counts as drawing, so it is shared out among the
# floor's areas: a grid of extra seeds, each given to the area that already
# has the nearest seed, so the real cell boundaries stay where they were.
def _spread(floor):
    seeds = [(x, y, name) for name, pts in floor["areas"].items() for x, y in pts]
    fixed = [(x, y) for x, y, _ in seeds] + list(floor.get("start", []))
    extra = []
    for gx in range(250, 700, 55):
        for gy in range(95, 610, 55):
            if any((gx - x) ** 2 + (gy - y) ** 2 < 45 ** 2 for x, y in fixed):
                continue
            name = min(seeds, key=lambda s: (gx - s[0]) ** 2 + (gy - s[1]) ** 2)[2]
            extra.append((gx, gy, name))
    for gx, gy, name in extra:
        floor["areas"][name].append((gx, gy))


for _floor in MAP["floors"]:
    _spread(_floor)
