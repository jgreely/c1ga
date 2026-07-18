#!/usr/bin/env python
"""
Convert the dataset JSON schema into a single "paragraph" of
"keyword: value" text. Basically the exact same prompt without
the JSON chartjunk.
"""

import os
import sys
import json
import argparse

parser = argparse.ArgumentParser(
    prog='json2txt', formatter_class = argparse.RawDescriptionHelpFormatter)
parser.add_argument('datasets', nargs = '*', 
    help='JSONL dataset files (output will be written as $path.txt)')
args = parser.parse_args()

if len(args.datasets) == 0:
    args.datasets = [ 'stdin' ]    
for infile in args.datasets:
    if infile == 'stdin':
        infile = sys.stdin.fileno()
        outfile = sys.stdout
    else:
        outfile = open(f"{os.path.splitext(infile)[0]}.txt", "w")
    with open(infile) as jsonl:
        for line in jsonl:
            output = []
            data = json.loads(line)
            for key in ('style', 'setting', 'composition'):
                output.append(f"{key.capitalize()}: {data[key]}")
            n = 1
            for subject in data['subject']:
                subject_output = []
                for key in subject:
                    subject_output.append(f"{key}: {subject[key]}")
                output.append(f"Subject {n} = {'; '.join(subject_output)}")
                n += 1
            if 'comment' not in data:
                data['comment'] = ''
            print(data['comment'], f"{'. '.join(output)}.", file=outfile)
