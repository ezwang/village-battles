def get_max_building_level(building):
    """ Returns the maximum building level for a particular building. """
    if building == "RP":
        return 1
    return 20


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


def get_max_capacity(level):
    """ Accepts the warehouse level and returns the maximum population for the village. """
    return int(1000 * 1.2**(level - 1))


def get_max_population(level):
    """ Accepts the farm level and returns the maximum population for the village. """
    return int(200 * 1.2**(level - 1))


def get_building_cost(building, level):
    """ Returns a tuple of (wood, clay, iron) indicating how much this building costs. """
    return (50, 50, 50)


def get_troop_cost(troop):
    """ Returns a tuple of (wood, clay, iron) indicating how much a unit of this type costs. """
    return (25, 25, 25)


def get_troop_time(troop):
    """ Returns troop build time in seconds. """
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
    return 1


def get_troop_travel(troop):
    """ Returns troop travel time in seconds. """
    return 10


def get_troop_carry(troop):
    """ Returns the number of resources that this type of unit. """
    return 10


def get_hq_buff(level):
    """ Returns a multiplier for the build time. """
    return 0.9**(level - 1)


def get_barracks_buff(level):
    """ Returns a multiplier for the troop build time. """
    return 0.95**(level - 1)
