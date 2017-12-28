def get_max_building_level(building):
    if building == "RP":
        return 1
    return 10


def get_building_population(building, level):
    return 1 * level


def get_wood_rate(level):
    return int(30 * (1.2**(level - 1)))


def get_clay_rate(level):
    return int(30 * (1.2**(level - 1)))


def get_iron_rate(level):
    return int(30 * (1.2**(level - 1)))


def get_max_capacity(level):
    return int(1000 * 1.2**(level - 1))


def get_max_population(level):
    return int(200 * 1.2**(level - 1))


def get_building_cost(building, level):
    return (50, 50, 50)


def get_building_population_difference(building, level):
    if level == 0:
        return get_building_population(building, 0)
    return get_building_population(building, level) - get_building_population(building, level - 1)


def get_building_upgrade_time(building, level):
    """ Returns the building upgrade time in seconds. """
    return 30
