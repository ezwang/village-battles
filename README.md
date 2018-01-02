# Village Battles

[![Build Status](https://travis-ci.org/ezwang/village-battles.svg?branch=master)](https://travis-ci.org/ezwang/village-battles)

Village Battles is a simple real time strategy game.

**Features**
- Multiple Worlds
- Multiple Villages
- Building Creation
- Troop Creation
- Map Interface
- Attacking / Supporting
- Village Conquering
- Quests
- Reports
- Tribes

## Setup

Start a [redis](https://redis.io/download) server on port `6379`.

```bash
virtualenv --python=python3 venv
source venv/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py runserver
```
