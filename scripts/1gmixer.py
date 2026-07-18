#!/usr/bin/env python
"""
Given N input lines containing JSON records in the standard schema,
select one top-level field from each in turn and create a composite
record, producing N//4 output lines
"""

import sys
import json

keys = ( 'style', 'setting', 'composition', 'subject' )

result = {}
for line in sys.stdin:
    if 'subject' in result:
        print(json.dumps(result))
        result = {}
    record = json.loads(line)
    for key in keys:
        if key not in result:
            result[key] = record[key]
            break
if 'subject' in result:
    print(json.dumps(result))
