#!/usr/bin/env python
"""
Make release tarball incorporating LLM-enhanced prompts.

TODO: error-checking (matching jsonl/prompt files, etc)
TODO: incorporate tagfiles
"""

import os
import sys
import json
import gzip

version = '1.0'

jsonfiles = []
for jsonfile in os.listdir('data'):
    if os.path.splitext(jsonfile)[1] == '.jsonl':
        jsonfiles.append(jsonfile)
jsonfiles.sort()

version = f"{version}.{len(jsonfiles)}"

with gzip.open(f"c1ga-{version}.jsonl.gz", "wt", encoding="utf-8") as z:
    for file in jsonfiles:
        base = os.path.splitext(file)[0]
        promptfile = f"data/{base}-prompt.txt"
        if not os.path.exists(promptfile):
            print(f"Warning: '{promptfile}' not found, skipping")
            continue
        with open(promptfile) as p:
            prompts = [ x.rstrip() for x in p ]
        with open(f"data/{file}") as f:
            for line in f:
                json_record = json.loads(line)                
                uuid = json_record['comment']
                del(json_record['comment'])
                z.write(json.dumps({
                    'prompt': prompts.pop(0),
                    'uuid': uuid,
                    'json': json.dumps(json_record)
                }) + '\n')
