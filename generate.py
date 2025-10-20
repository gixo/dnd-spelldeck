#! /usr/bin/env python3

import argparse
import sys
import textwrap
import json

MAX_TEXT_LENGTH = 690

SPELLS_TRUNCATED = 0
SPELLS_TOTAL = 0

LEVEL_STRING = {
    0: '{school} cantrip {ritual}',
    1: '1st level {school} {ritual}',
    2: '2nd level {school} {ritual}',
    3: '3rd level {school} {ritual}',
    4: '4th level {school} {ritual}',
    5: '5th level {school} {ritual}',
    6: '6th level {school} {ritual}',
    7: '7th level {school} {ritual}',
    8: '8th level {school} {ritual}',
    9: '9th level {school} {ritual}',
}

# SPELLS will be loaded in main after parsing args


def truncate_string(string, max_len=MAX_TEXT_LENGTH):
    if len(string) <= max_len:
        return string

    # remove trailing space at the point of truncation
    string = string[:max_len-3].rstrip() + "..." #add ellipsis at the point of truncation   

    # close unbalance parentheses
    open_parens = string.count('{')
    close_parens = string.count('}')
    if open_parens > close_parens:
        string += '}' * (open_parens - close_parens)

    return string


def print_spell(name, level, school, range, time, ritual, duration, components,
                material, text, source=None, source_page=None, **kwargs):
    global SPELLS_TRUNCATED, SPELLS_TOTAL
    header = LEVEL_STRING[level].format(
        school=school.lower(), ritual='ritual' if ritual else '').strip()

    if material is not None:
        text += "\n\n* - (" + material + ")"
        components = [i.replace("M", "M *") for i in components]

    # Only append page information if we actually have a source string
    if source_page is not None and source:
        source = f"{source} page {source_page}"

    new_text = truncate_string(text)

    if new_text != text:
        SPELLS_TRUNCATED += 1

    SPELLS_TOTAL += 1

    # Split text by double newlines to preserve paragraph breaks
    paragraphs = new_text.split('\n\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph.strip():  # Only process non-empty paragraphs
            formatted_paragraphs.append(textwrap.fill(paragraph.strip(), 80))
    
    formatted_text = '\n\n'.join(formatted_paragraphs)

    # Check if range contains area effect text and extract it for icon display
    display_range = range
    area_effect = "none"  # Possible values: none, cone, cube, cylinder, emanation, line, sphere

    if range:
        import re
        range_lower = range.lower()

        # List of area effect types to check
        area_types = ['cone', 'cube', 'cylinder', 'emanation', 'line', 'sphere']

        # Check for each area effect type
        for area_type in area_types:
            if area_type in range_lower:
                # Remove the area effect word and any following closing parenthesis
                display_range = re.sub(r'\s*' + area_type + r'\s*\)?', '', range, flags=re.IGNORECASE).strip()
                area_effect = area_type
                break

    # Add area effect info to the range
    range_with_icon = f"{display_range}|{area_effect}"

    # Add ritual flag to casting time
    time_with_ritual = f"{time}|RITUAL" if ritual else f"{time}|NONRITUAL"

    # Add concentration flag to duration
    duration_with_concentration = duration
    concentration = kwargs.get('concentration', False)
    if concentration or (duration and 'concentration' in duration.lower()):
        duration_with_concentration = f"{duration}|CONCENTRATION"
    else:
        duration_with_concentration = f"{duration}|NONCONCENTRATION"

    # Parse damage types from damage_effect field
    damage_effect = kwargs.get('damage_effect', 'None')
    damage_types_list = ['acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning',
                         'necrotic', 'piercing', 'poison', 'psychic', 'radiant', 'slashing', 'thunder']
    found_damage_types = []

    if damage_effect and damage_effect != 'None':
        damage_effect_lower = damage_effect.lower()
        for dtype in damage_types_list:
            if dtype in damage_effect_lower:
                found_damage_types.append(dtype)

    # Add damage types to the damage_effect string
    damage_effect_with_icons = f"{damage_effect}|{','.join(found_damage_types)}"

    print("\\begin{spell}{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}{%s}\n\n%s\n\n\\end{spell}\n" %
        (name, header, range_with_icon, time_with_ritual, duration_with_concentration, ", ".join(components), source or '',
         kwargs.get('attack_save', 'None'), damage_effect_with_icons, formatted_text))


def get_spells(classes=None, levels=None, schools=None, names=None, sort_by='name'):
    classes = {i.lower() for i in classes} if classes is not None else None
    schools = {i.lower() for i in schools} if schools is not None else None
    names = {i.lower() for i in names} if names is not None else None

    # Determine the sort key based on the sort_by parameter
    if sort_by == 'level':
        sort_key = lambda x: (x[1]['level'], x[0])  # Sort by level, then by name
    else:
        sort_key = lambda x: x[0]  # Sort by name only

    return [
        (name, spell) for name, spell in sorted(SPELLS.items(), key=sort_key) if
        (classes is None or len(classes & {i.lower() for i in spell['classes']}) > 0) and
        (schools is None or spell['school'].lower() in schools) and
        (levels is None or spell['level'] in levels) and
        (names is None or name.lower() in names)
    ]

def parse_levels(levels):
    rv = None

    if levels is not None:
        rv = set()

        for level_spec in levels:
            tmp = level_spec.split('-')
            if len(tmp) == 1:
                rv.add(int(tmp[0]))
            elif len(tmp) == 2:
                rv |= set(range(int(tmp[0]), int(tmp[1]) + 1))

    return rv

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", type=str, default="data/spells.json",
        help="input JSON file containing spells data (default: data/spells.json)"
    )
    parser.add_argument(
        "-c", "--class", type=str, action='append', dest='classes',
        help="only select spells for this class, can be used multiple times "
             "to select multiple classes."
    )
    parser.add_argument(
        "-l", "--level", type=str, action='append', dest='levels',
        help="only select spells of a certain level, can be used multiple "
             "times and can contain a range such as `1-3`."
    )
    parser.add_argument(
        "-s", "--school", type=str, action='append', dest='schools',
        help="only select spells of a school, can be used multiple times."
    )
    parser.add_argument(
        "-n", "--name", type=str, action='append', dest='names',
        help="select spells with one of several given names."
    )
    parser.add_argument(
        "--sort-by", type=str, choices=['name', 'level'], default='name',
        help="sort spells by name (default) or by level (then by name)."
    )
    args = parser.parse_args()

    # Load spells from the specified input file
    try:
        with open(args.input) as json_data:
            SPELLS = json.load(json_data)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON from '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    for name, spell in get_spells(args.classes, parse_levels(args.levels), args.schools, args.names, args.sort_by):
        print_spell(name, **spell)

    print('Had to truncate %d out of %d spells at %d characters.' % (SPELLS_TRUNCATED, SPELLS_TOTAL, MAX_TEXT_LENGTH), file=sys.stderr)
