#!/usr/bin/env python
"""
Trivial script to duplicate each line on STDIN N times, so a single
prompt can be reused with multiple substitutions.
"""

import sys
import argparse

parser = argparse.ArgumentParser(
    prog='dupe',
    formatter_class = argparse.RawDescriptionHelpFormatter,
    description = 'duplication each line from STDIN N times (default 10)')
parser.add_argument('count',
    nargs = '?',
    default = 10,
    help='number of times to duplicate each line (default 10)')
args=parser.parse_args()

for line in sys.stdin:
    for count in range(args.count):
        print(line.rstrip())
