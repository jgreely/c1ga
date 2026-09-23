#!/usr/bin/env python
"""
clean up the LLM classification tagging output, standardizing
the use of the 'nsfw' tag and using the '1girl', '2girls'
tags. All "-" and "_" are replaced with spaces for consistency,
and there are no spaces after ','.

Once I have the complete dataset processed, something like:
    clean_tags.py *-tags.txt | tr ',' '\n' | sort | uniq -c | sort -rn |
        awk '$1>10' | sed -e 's/^[ 0-9][ 0-9]* //' > ranked-tags.txt
"""

import os
import sys
import re

escape = '\033[K\033[?25h' # `lms chat` prints ANSI escape chars, sigh
re_naughty = re.compile(r'\b(pubic|panty|panties|underwear|lingerie|no clothing|no top|no bottom|bare chest|bare body|bare upper body|bare breast|bare backside|areola|visible breast|visible buttock|undergarment|nipple|décolletage|braless|nude|bra|bralette|no bottoms|bare breasts|visible breasts|visible buttocks|nipples|undergarments|bodysuit)\b')
re_garbage = re.compile(r'\b(interference pattern|variation|detail|texture|definition|transition|photo|photograph|vibrant|abstract|palette|portrait|photography|highlights|college age|textured|transitions|details|variations|patterns)\b')
re_no = re.compile(r'^no ')
re_genitals = re.compile(r'genital')
# LLM really hates the word 'beige'...
re_beige = re.compile(r'beacon |beaige ')
re_beige2 = re.compile(r'beige(?:[a-rt-z]|[a-z][a-z])')

# TODO: consolidate for classification purposes
# General-purpose regexp cleanup: (group1) .*(group2)$
#   ponytail|pony tail|pony tailed = ponytail
#   group1 - long/medium/short/shoulder/etc, group2 - hair(end)
#       add tag r'\g<1> hair'
#   no color/length words + hair = ignore
#
color_words ='red|green|blue|white|black|green|pink|turquoise|beige|yellow|gray|purple|teal|maroon|peach|grey|lavender|purple|gold|silver|tan|brown|hazel|dark|amber|pale|golden|cream'
color_items = 'shirt|blouse|dress|skirt|pants|panties|panty|bikini top|bikini bottom|bikini|lingerie|bodysuit|underwear|undergarment|shorts|top|bottom|hair|skin|eyes|bralette|bra|bracelet|iris|bottoms|stockings|stocking|shoes|thong|choker|strap|straps'
re_coloritem = re.compile(f"\\b({color_words})\\b.*\\b({color_items})\\b")

re_scrubwords = re.compile(r' *\b(visible|matching)\b *')

files = sys.argv[1:]

ranked_tags = 'ranked-tags.txt'
rank = {}
if os.path.exists(ranked_tags):
    n = 1
    with open(ranked_tags) as f:
        for line in f:
            fields = line.split(' ')
            tag = fields[1]
            rank[tag] = n
            n += 1

for file in files:
    base, ext = os.path.splitext(file)
    outfile = f"{base}-clean{ext}"
    with open(file, newline='\n') as f:
        for line in f:
            line = str(line)
            line = line.replace('\015', '')
            line = line.rstrip('\n')
            line = line.replace(escape, '')
            line = line.replace('_', ' ')
            line = line.lower()
            tags = re.split(", *", line)
            clean_tags = []
            explicit = False
            sfw = False
            nsfw = False
            count_girls = 1
            for tag in tags:
                if re_beige.search(tag):
                    tag = re.sub(re_beige, 'beige', tag)
                if re_beige2.search(tag):
                    tag = tag.replace('beige', 'beige ')
                # all these tags should be replaced
                if tag == 'solo':
                    count_girls = 1
                elif tag == 'woman' and 'solo' in tags:
                    count_girls = 1
                elif tag == 'two women':
                    count_girls = 2
                elif tag == 'three women':
                    count_girls = 3
                elif tag == 'four women':
                    count_girls = 4
                elif tag == 'second woman':
                    count_girls = 2
                elif tag == 'another woman':
                    count_girls = 2
                elif tag == 'sfw':
                    sfw = True
                elif tag == 'suggestive':
                    sfw = False
                elif tag == 'explicit':
                    sfw = False
                    nsfw = True
                elif tag == 'sfw' or tag == 'no rating':
                    sfw = True
                elif re_no.search(tag):
                    continue
                elif re_genitals.search(tag):
                    # has to go last because of "no_genital..." tags
                    nsfw = True
                elif re_garbage.search(tag):
                    continue
                else:
                    if re_naughty.search(tag):
                        nsfw = True
                    if re_scrubwords.search(tag):
                        tag = re_scrubwords.sub('', tag)
                    if match := re_coloritem.search(tag):
                        tag = f"{match.group(1)} {match.group(2)}"
                    if tag.count(' ') < 4:
                        clean_tags.append(tag)
            if rank:
                # de-dupe, sort by overall frequency, trim number
                clean_tags = list(set(clean_tags))
                clean_tags.sort(key = lambda x: rank[x] if x in rank else 999999)
                del clean_tags[20:]
            if nsfw or explicit:
                clean_tags.insert(0, 'nsfw')
            elif sfw:
                clean_tags.insert(0, 'sfw')
            if count_girls == 1:
                clean_tags.insert(0, '1girl')
            elif count_girls > 1:
                clean_tags.insert(0, f"{count_girls}girls")
            print(','.join(clean_tags))
