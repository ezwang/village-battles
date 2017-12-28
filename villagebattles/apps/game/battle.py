import json


def process_attack(attack):
    from .models import Report

    content = {
        "attacker": {
            "village": str(attack.source),
            "troops": [(x.get_type_display(), x.amount) for x in attack.troops.all()]
        },
        "defender": {
            "village": str(attack.destination),
            "troops": [(x.get_type_display(), x.amount) for x in attack.destination.troops.all()]
        }
    }

    body = json.dumps(content, sort_keys=True, indent=4)
    attacker = Report.objects.create(
        title="{} attacks {}".format(attack.source, attack.destination),
        owner=attack.source.owner,
        world=attack.source.world,
        body=body
    )
    defender = Report.objects.create(
        title="{} defends {}".format(attack.destination, attack.source),
        owner=attack.destination.owner,
        world=attack.destination.world,
        body=body
    )
