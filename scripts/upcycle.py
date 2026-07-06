#!/usr/bin/env python
"""
cat jsonprompts.txt | upcycle [-d wildcard_dir] \
    age=young_adult sex=female body=skinny race=race/euro \
    face=faces/female expression=happy style=var/scifi

If a value matches a known wildcard file, use it for lookup, otherwise
it's literal. Optional value prefixes followed by colon (unique
substring of function (sort|rand|shuf); using "!" instead of ":" sets
it once per prompt and reuses it, instead of looking up a new value
for each subject.

TODO: add support for simple YAML lookups to reuse my libraries.
Can either pull all keys from wc/default.yaml or top-level elements
from wc/$val.yaml; not going to reimplement more dynamicprompts features.

TODO: before treating val as literal, attempt word-by-word wildcard
replacement. So, "rand:a young female species" will first look up the
entire string, then each word in turn, inserting them as literals if
not found.

TODO: come up with a simple way to support sets, where multiple
key/val combinations can be inserted together from a single wildcard
lookup (like dark skin|dark hair|african or blonde|blue eyes|scandinavian).

"""

import os
import sys
import json
import argparse
import random
import re
from pathlib import Path


def init():
    parser = argparse.ArgumentParser(
        prog='upcycle',
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description = """
            upcycle JSON prompts by replacing/inserting dynamicprompt-like values
        """
    )
    parser.add_argument('-d', '--directory',
        type=str,
        default='wc',
        help='directory containing wildcard files (default "./wc"'
    )
    parser.add_argument('-l', '--list-wildcards',
        action='store_true',
        help='list wildcard files located in --directory')
    parser.add_argument('-D', '--debug',
        action='store_true',
        help='upcase replacements so they stand out')
    parser.add_argument('-f', '--file',
        type=str,
        help='''
            JSON file containing key/val pairs to substitute into prompts
            (processed before arguments)
    ''')
    parser.add_argument('-x', '--exclude-keys',
        type=str,
        help='comma-separated list of keys to delete from all subjects')
    parser.add_argument('keyvals',
        nargs = '*',
        help='''
            key=value pairs to guide the replacement. Values will always
            be looked up as wildcards first, then inserted literally.
            keys will be replaced wherever they appear. Can also be supplied
            as a JSON file with the --file option, which will be read before
            any arguments.

            Each time a key is found in the JSON, it is replaced by the next
            value in that wildcard, wrapping around. By default, the values
            are used sequentially. If the value is of the form "order[!:]wildcard",
            order is one of sort|rand|shuf, overriding the order. Sort orders
            the list, rand selects completely at random, and shuf does a
            perfect shuffle and reshuffles when it wraps around. If the "!"
            is present instead of ":", each key is looked up only once per 
            prompt (for instance, eye_color=shuf!colors will shuffle the list of
            possible eye colors, and assign the same color to every subject
            present in the prompt, and a different color to every subject in
            the next prompt.
        '''
    )
    args = parser.parse_args()

    if args.list_wildcards and os.path.isdir(args.directory):
        wclist = []
        for file in os.listdir(args.directory):
            base, ext = os.path.splitext(file)
            wclist.append(base)
        wclist.sort()
        for wc in wclist:
            print(wc)
        sys.exit()

    if args.exclude_keys:
        for key in args.exclude_keys.split(','):
            exclude.append(key)
    keyvals = {}
    # read key/val pairs from file first, override with arguments
    if args.file and os.path.exists(args.file):
        with open(args.file) as f:
            keyvals = json.load(f)
    for keyval in args.keyvals:
        if '=' not in keyval:
            print(f"ERROR arguments must be key=val")
            sys.exit()
        key, val = keyval.split('=',1)
        keyvals[key] = val

    for key in keyvals:
        val = keyvals[key] 
        save_val = False
        mode = 'seq'
        if ':' in val:
            mode, val = val.split(':', 1)
        elif '!' in val:
            mode, val = val.split('!', 1)
            save_val = True
        if mode == '':
            mode = 'seq'
        file = os.path.join(args.directory, f"{val}.txt")
        if os.path.exists(file):
            with open(file) as f:
                data = []
                weights = []
                for line in f:
                    if re.search(r'^#|^ *$', line):
                        continue
                    if match := re.match(r'(^[0-9.]*)x +', line):
                        weights.append(float(match.group(1)))
                        line = line[match.end():]
                    else:
                        weights.append(1.0)
                    data.append(line.rstrip())
        else:
            file = ''
            data = [val]
            weights = []
        if mode == 'sort':
            data.sort()
        elif mode == 'shuf':
            random.shuffle(data)
        wildcards[key] = {
            "file": file,
            "mode": mode,
            "i": 0,
            "save": save_val,
            "data": data,
            "weights": weights
        }
    return args.debug


def nextval(wildcard, saved_val, debug):
    result = ''
    if wildcard not in wildcards:
        print(f"ERROR: unknown wildcard string '{wc}'")
        sys.exit()
    wc = wildcards[wildcard]
    if wildcard in saved_val and wc['save']:
        return saved_val[wildcard]
    if len(wc['data']) == 1:
        result = wc['data'][0]
    elif wc['mode'] == 'rand':
        if len(wc['weights']) > 0:
            result = random.choices(wc['data'], wc['weights'])[0]
        else:
            result = random.choice(wc['data'])
    elif wc['i'] >= len(wc['data']):
        if wc['mode'] == 'shuf':
            random.shuffle(wc['data'])
        wc['i'] = 0
    if result == '':
        result = wc['data'][wc['i']]
        wc['i'] += 1
    saved_val[wildcard] = result
    if debug:
        return result.upper()
    else:
        return result



wildcards = {}
exclude = []
DEBUG = init()

# Note: assumes my JSON-prompt structure
for line in sys.stdin:
    saved_val = {}
    data = json.loads(line)
    for key in wildcards:    
        if key in ['style', 'setting', 'composition']:
            data[key] = nextval(key, saved_val, DEBUG)
        else:
            if 'subject' in data:
                for subject in data['subject']:
                    subject[key] = nextval(key, saved_val, DEBUG)
    for key in exclude:
        for subject in data['subject']:
            del subject[key]
    print(json.dumps(data))
