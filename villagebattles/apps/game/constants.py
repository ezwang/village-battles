from django.conf import settings


def get_max_building_level(building):
    """ Returns the maximum building level for a particular building. """
    try:
        return settings.GAME_CONFIG["buildings"][building]["max_level"]
    except KeyError:
        return 20


def get_troop_attack(troop):
    try:
        return settings.GAME_CONFIG["troops"][troop]["attack"]
    except KeyError:
        return 50


def get_troop_defense(troop):
    try:
        return settings.GAME_CONFIG["troops"][troop]["defense"]
    except KeyError:
        return 50


def get_building_population(building, level):
    """ Returns how many population units a building takes up. """
    return 1 * level


def get_wood_rate(level):
    """ Accepts the wood mine level and returns wood produced per hour. """
    return int(30 * (1.2**(level - 1)))


def get_clay_rate(level):
    """ Accepts the clay mine level and returns clay produced per hour. """
    return int(30 * (1.2**(level - 1)))


def get_iron_rate(level):
    """ Accepts the iron mine level and returns iron produced per hour. """
    return int(30 * (1.2**(level - 1)))


def get_loyalty_regen():
    """ Returns the loyalty regeneration rate per hour. """
    return settings.GAME_CONFIG.get("loyalty_regen", 1)


def get_max_capacity(level):
    """ Accepts the warehouse level and returns the maximum population for the village. """
    return int(1000 * 1.2**(level - 1))


def get_max_population(level):
    """ Accepts the farm level and returns the maximum population for the village. """
    return int(200 * 1.2**(level - 1))


def get_building_cost(building, level):
    """ Returns a tuple of (wood, clay, iron) indicating how much this building costs. """
    try:
        return settings.GAME_CONFIG["buildings"][building]["cost"][level]
    except KeyError:
        return (50, 50, 50)


def get_troop_cost(troop):
    """ Returns a tuple of (wood, clay, iron) indicating how much a unit of this type costs. """
    try:
        return settings.GAME_CONFIG["troops"][troop]["cost"]
    except KeyError:
        return (25, 25, 25)


def get_troop_time(troop):
    """ Returns troop build time in seconds. """
    try:
        return settings.GAME_CONFIG["troops"][troop]["build_time"]
    except KeyError:
        return 30


def get_building_population_difference(building, level):
    """ Returns the difference in building population between the current level and the last one. """
    if level == 0:
        return get_building_population(building, 0)
    return get_building_population(building, level) - get_building_population(building, level - 1)


def get_building_upgrade_time(building, level):
    """ Returns the building upgrade time in seconds. """
    return 300 * 1.5**(level - 1)


def get_troop_population(troop):
    """ Returns the number of population units that this type of troop takes up. """
    try:
        return settings.GAME_CONFIG["troops"][troop]["population"]
    except KeyError:
        return 1


def get_troop_travel(troop):
    """ Returns troop travel time in seconds. """
    try:
        return settings.GAME_CONFIG["troops"][troop]["travel_time"]
    except KeyError:
        return 10


def get_troop_carry(troop):
    """ Returns the number of resources that this type of unit. """
    try:
        return settings.GAME_CONFIG["troops"][troop]["carry"]
    except KeyError:
        return 10


def get_hq_buff(level):
    """ Returns a multiplier for the build time. """
    try:
        return settings.GAME_CONFIG["buildings"]["HQ"]["buff"][level]
    except KeyError:
        return 1


def get_recruitment_buff(building, level):
    """ Returns a multiplier for the troop build time. """
    try:
        return settings.GAME_CONFIG["buildings"][building]["buff"][level]
    except KeyError:
        return 1


def building_requirements_met(building_type, village):
    """ Given a building type and a village, check if the village can build the building. """
    if building_type == "BR":
        return village.get_level("HQ") >= 3
    if building_type == "ST":
        return village.get_level("HQ") >= 10
    if building_type == "WS":
        return village.get_level("HQ") >= 15
    if building_type == "AC":
        return village.get_level("HQ") >= 20
    return True


def get_allowed_troops(building_type):
    try:
        return settings.GAME_CONFIG["buildings"][building_type]["troops"]
    except KeyError:
        return []
