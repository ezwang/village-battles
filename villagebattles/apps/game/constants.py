from django.conf import settings


def _get_value(path, level=None, initial=0, scale=0, constant=0, default=None):
    try:
        obj = settings.GAME_CONFIG
        for item in path:
            obj = obj[item]
    except KeyError:
        if default is not None:
            return default
        return initial * (scale ** (level - 1)) + constant
    if not level:
        return obj
    if isinstance(obj, list):
        return obj.get(level, initial)
    elif isinstance(obj, dict):
        return obj.get("initial", 1) * (obj.get("scale", scale) ** (level - 1)) + obj.get("constant", constant)
    else:
        return obj


def get_time_multiplier():
    return settings.GAME_CONFIG.get("time_multiplier", 1)


def get_max_building_level(building):
    """ Returns the maximum building level for a particular building. """
    return int(_get_value(["buildings", building, "max_level"], default=20))


def get_troop_attack(troop):
    return int(_get_value(["troops", troop, "attack"], default=50))


def get_troop_defense(troop):
    return int(_get_value(["troops", troop, "defense"], default=50))


def get_building_population(building, level):
    """ Returns how many population units a building takes up. """
    return int(_get_value(["buildings", building, "population"], level, default=level))


def get_wood_rate(level):
    """ Accepts the wood mine level and returns wood produced per hour. """
    return int(_get_value(["buildings", "WM", "production"], level, initial=30, scale=1.2) * get_time_multiplier())


def get_clay_rate(level):
    """ Accepts the clay mine level and returns clay produced per hour. """
    return int(_get_value(["buildings", "CM", "production"], level, initial=30, scale=1.2) * get_time_multiplier())


def get_iron_rate(level):
    """ Accepts the iron mine level and returns iron produced per hour. """
    return int(_get_value(["buildings", "IM", "production"], level, initial=30, scale=1.2) * get_time_multiplier())


def get_loyalty_regen():
    """ Returns the loyalty regeneration rate per hour. """
    return settings.GAME_CONFIG.get("loyalty_regen", 1)


def get_max_capacity(level):
    """ Accepts the warehouse level and returns the maximum population for the village. """
    return int(_get_value(["buildings", "WH", "capacity"], level, initial=1000, scale=1.2))


def get_max_population(level):
    """ Accepts the farm level and returns the maximum population for the village. """
    return int(_get_value(["buildings", "FM", "capacity"], level, initial=200, scale=1.2))


def get_building_cost(building, level):
    """ Returns a tuple of (wood, clay, iron) indicating how much this building costs. """
    try:
        return settings.GAME_CONFIG["buildings"][building]["cost"][level]
    except KeyError:
        return (50, 50, 50)


def get_troop_cost(troop):
    """ Returns a tuple of (wood, clay, iron) indicating how much a unit of this type costs. """
    return _get_value(["troops", troop, "cost"], default=(25, 25, 25))


def get_troop_time(troop):
    """ Returns troop build time in seconds. """
    return _get_value(["troops", troop, "build_time"], default=30) / get_time_multiplier()


def get_building_population_difference(building, level):
    """ Returns the difference in building population between the current level and the last one. """
    if level == 0:
        return get_building_population(building, 0)
    return get_building_population(building, level) - get_building_population(building, level - 1)


def get_building_upgrade_time(building, level):
    """ Returns the building upgrade time in seconds. """
    return _get_value(["buildings", building, "upgrade"], level, initial=60, scale=1.5) / get_time_multiplier()


def get_troop_population(troop):
    """ Returns the number of population units that this type of troop takes up. """
    return _get_value(["troops", troop, "population"], default=1)


def get_troop_travel(troop):
    """ Returns troop travel time in seconds. """
    return _get_value(["troops", troop, "travel_time"], default=10) / get_time_multiplier()


def get_troop_carry(troop):
    """ Returns the number of resources that this type of unit. """
    return _get_value(["troops", troop, "carry"], default=10)


def get_hq_buff(level):
    """ Returns a multiplier for the build time. """
    return _get_value(["buildings", "HQ", "buff"], level, initial=1, scale=0.97)


def get_recruitment_buff(building, level):
    """ Returns a multiplier for the troop build time. """
    return _get_value(["buildings", building, "buff"], level, initial=1, scale=0.97)


def building_requirements_met(building_type, village):
    """ Given a building type and a village, check if the village can build the building. """
    if building_type in ["BR", "WA"]:
        return village.get_level("HQ") >= 3
    if building_type == "ST":
        return village.get_level("HQ") >= 10
    if building_type == "WS":
        return village.get_level("HQ") >= 15
    if building_type == "AC":
        return village.get_level("HQ") >= 20
    return True


def get_allowed_troops(building_type):
    """ Get the types of troops a building can make. """
    return _get_value(["buildings", building_type, "troops"], default=[])
