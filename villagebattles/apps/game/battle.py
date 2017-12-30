import json
import copy

from django.db.models import Sum

from .constants import get_troop_carry, get_troop_attack, get_troop_defense
from .helpers import get_troop_type_display


def do_damage(attack):
    attacking = attack.troops.all()
    defending = attack.destination.all_troops.all()

    total_attacker_attack = sum([x.amount * get_troop_attack(x.type) / 100 for x in attacking])
    total_defender_attack = sum([x.amount * get_troop_attack(x.type) / 100 for x in defending])

    total_defender_defense = sum([x.amount * get_troop_defense(x.type) / 100 for x in defending])

    if total_attacker_attack > total_defender_defense:
        attack_power = 0.9
        defend_power = 0.5
    else:
        attack_power = 0.5
        defend_power = 0.9

    attacker_damage = total_attacker_attack * attack_power
    defender_damage = total_defender_attack * defend_power

    for defender in defending:
        defender.amount -= attacker_damage
        if defender.amount <= 0:
            defender.delete()
        else:
            defender.save()

    for attacker in attacking:
        attacker.amount -= defender_damage
        if attacker.amount <= 0:
            attacker.delete()
        else:
            attacker.save()


def calculate_loot(attack):
    total = sum([get_troop_carry(x.type) * x.amount for x in attack.troops.all()])
    each = int(total / 3)
    wood = min(attack.destination.wood, each)
    attack.destination.wood -= wood
    clay = min(attack.destination.clay, each)
    attack.destination.clay -= clay
    iron = min(attack.destination.iron, each)
    attack.destination.iron -= iron
    total -= wood + clay + iron
    if total > 0:
        if attack.destination.wood > 0:
            extra = min(attack.destination.wood, total)
            attack.destination.wood -= extra
            wood += extra
            total -= extra
    if total > 0:
        if attack.destination.clay > 0:
            extra = min(attack.destination.clay, total)
            attack.destination.clay -= extra
            clay += extra
            total -= extra
    if total > 0:
        if attack.destination.iron > 0:
            extra = min(attack.destination.iron, total)
            attack.destination.iron -= extra
            iron += extra
    attack.destination.save()
    return (wood, clay, iron)


def get_defending_troops(village):
    troops = village.all_troops.values("type").annotate(amount=Sum("amount"))
    return [(get_troop_type_display(x["type"]), x["amount"]) for x in troops]


def process_attack(attack):
    from .models import Report

    content = {
        "attacker": {
            "village": {
                "id": attack.source.id,
                "name": str(attack.source)
            },
            "troops": [(x.get_type_display(), x.amount) for x in attack.troops.all()]
        },
        "defender": {
            "village": {
                "id": attack.destination.id,
                "name": str(attack.destination)
            },
            "troops": get_defending_troops(attack.destination)
        }
    }

    do_damage(attack)

    # Add remaining troop values
    attacker_remaining = [(x.get_type_display(), x.amount) for x in attack.troops.all()]
    content["attacker"]["remaining_troops"] = attacker_remaining
    content["defender"]["remaining_troops"] = get_defending_troops(attack.destination)

    defender_action = "defends"
    attacker_action = "attacks"

    last_owner = attack.destination.owner

    if attack.troops.filter(type="NB").exists():
        attack.destination.loyalty = attack.destination.loyalty - 20
        if attack.destination.loyalty <= 0:
            defender_action = "conquered by"
            attacker_action = "conquers"
            attack.destination.loyalty = 20
            attack.destination.owner = attack.source.owner
        attack.save()
        content["loyalty"] = attack.destination.loyalty

    loot = calculate_loot(attack)
    content["loot"] = {
        "wood": loot[0],
        "clay": loot[1],
        "iron": loot[2]
    }

    attack.loot = ",".join([str(x) for x in loot])
    attack.save()

    content["remaining"] = {
        "wood": attack.destination.wood,
        "clay": attack.destination.clay,
        "iron": attack.destination.iron,
    }

    attacker_copy = copy.deepcopy(content)
    defender_copy = copy.deepcopy(content)

    # If defender destroyed all of the troops, hide information
    if not content["attacker"]["remaining_troops"]:
        del attacker_copy["defender"]["remaining_troops"]
        del attacker_copy["defender"]["troops"]
        del attacker_copy["remaining"]

    # Create the reports
    attacker_copy = json.dumps(attacker_copy, sort_keys=True, indent=4)
    defender_copy = json.dumps(defender_copy, sort_keys=True, indent=4)

    Report.objects.create(
        title="{} {} {}".format(attack.source, attacker_action, attack.destination),
        owner=attack.source.owner,
        world=attack.source.world,
        body=attacker_copy
    )
    Report.objects.create(
        title="{} {} {}".format(attack.destination, defender_action, attack.source),
        owner=last_owner,
        world=attack.destination.world,
        body=defender_copy
    )
