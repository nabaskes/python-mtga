""" generate_set_map.py:

given a cards.json and a loc.json, generate a python-mtga style set map.
cards.json can be obtained from the script in Fugiman/deckmaster:
loc.json can also be obtained with minor modifications: data_loc_ instead of data_cards_

"""

import argparse
import json
import re


COLOR_ID_MAP = {1: "W", 2: "U", 3: "B", 4: "R", 5: "G"}
RARITY_ID_MAP = {0: "Token", 1: "Basic", 2: "Common", 3: "Uncommon", 4: "Rare", 5: "Mythic Rare"}


def generate_set_map(loc, cards, enums, set_name):
    """
    :param loc: dict w/ contents of of loc.json
    :param cards: dict w/ contents of cards.json
    :param set: set name (GRN, etc)
    """
    used_classnames = []
    set_name_class_cased = re.sub('[^0-9a-zA-Z_]', '', set_name)
    set_name_snake_cased = re.sub('[^0-9a-zA-Z_]', '', set_name.lower().replace(" ", "_"))
    loc_map = {}
    for obj in loc[0]["keys"]:
        if obj["id"] in loc_map.keys():
            print("WARNING: overwriting id {} = {} with {}".format(obj["id"], loc_map[obj["id"]], obj["text"]))
        loc_map[obj["id"]] = obj["text"]
    # loc_map = {obj["id"]: obj["text"] for obj in loc[0]["keys"]}
    enum_map = {obj["name"]: {inner_obj["id"]: inner_obj["text"] for inner_obj in obj["values"]} for obj in enums}
    set_cards = [card for card in cards if card["set"].upper() == set_name.upper()]
    assert set_cards, "No cards found in set {}. Double check your nomenclature, and ensure the input files contain your set!"

    print("translating {} cards from set {}".format(len(set_cards), set_name))
    output_lines = []
    for card in set_cards:
        try:
            card_title = loc_map[card["titleId"]]
            card_name_class_cased = re.sub('[^0-9a-zA-Z_]', '', card_title)
            card_name_class_cased_suffixed = card_name_class_cased
            card_suffix = 2

            while card_name_class_cased_suffixed in used_classnames:
                card_name_class_cased_suffixed = card_name_class_cased + str(card_suffix)
                card_suffix += 1
            used_classnames.append(card_name_class_cased_suffixed)

            card_name_snake_cased = re.sub('[^0-9a-zA-Z_]', '', card_title.lower().replace(" ", "_"))
            cc_raw = card["castingcost"]
            # cc's look like: o2o(U/B)o(U/B)o3oUoB, want to turn it into ["2", "(U/B)"] etc
            cost = [cost_part for cost_part in cc_raw.split("o")[1:] if cost_part != "0"]
            color_identity = [COLOR_ID_MAP[color_id] for color_id in card["colorIdentity"]]

            card_type_ids = [enum_map["CardType"][card_type] for card_type in card["types"]]
            card_types = " ".join([loc_map[loc_id] for loc_id in card_type_ids])

            sub_types_ids = [enum_map["SubType"][sub_type] for sub_type in card["subtypes"]]
            sub_types = " ".join([loc_map[loc_id] for loc_id in sub_types_ids])

            set_id = set_name.upper()

            rarity = RARITY_ID_MAP[card["rarity"]]

            set_number = int(card["CollectorNumber"])

            grp_id = card["grpid"]

            # params: name,    pretty_name, cost,            color_identity, card_type,  sub_types, set_id, rarity,        set_number, mtga_id
            # ex:     "a_b_c", "A B C",     ['3', 'W', 'W'], ['W'],          "Creature", "Angel",  "AKH",   "Mythic Rare", 1,          64801

            new_card_str = '{} = Card("{}", "{}", {}, {}, "{}", "{}", "{}", "{}", {}, {})'.format(
                card_name_class_cased_suffixed,
                card_name_snake_cased,
                card_title,
                cost,
                color_identity,
                card_types,
                sub_types,
                set_id,
                rarity,
                set_number,
                grp_id
            )
            output_lines.append(new_card_str)

        except Exception:
            print("hit an error on {} / {} / {}".format(card["grpid"], loc_map[card["titleId"]], card["CollectorNumber"]))
    header = """
import sys
from mtga.models.card import Card
from mtga.models.card_set import Set
import inspect
"""

    footer = """
clsmembers = [card for name, card in inspect.getmembers(sys.modules[__name__]) if isinstance(card, Card)]
{} = Set("{}", cards=clsmembers)
""".format(set_name_class_cased, set_name_snake_cased)
    with open("{}.py".format(set_name.lower()), "w") as set_file:
        set_file.write("{}\n\n{}\n\n{}".format(header, "\n".join(output_lines), footer))

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-l', '--loc_file')
    arg_parser.add_argument('-c', '--cards_file')
    arg_parser.add_argument('-e', '--enums_file')
    arg_parser.add_argument('-s', '--set')
    args = arg_parser.parse_args()

    with open(args.cards_file, "r", encoding="utf-8") as card_in:
        cards = json.load(card_in)

    with open(args.loc_file, "r", encoding="utf-8") as loc_in:
        loc = json.load(loc_in)

    with open(args.enums_file, "r", encoding="utf-8") as enums_in:
        enums = json.load(enums_in)

    generate_set_map(loc, cards, enums, args.set)