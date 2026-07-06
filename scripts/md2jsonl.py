#!/usr/bin/env python
# input structure
#   - Key: value
#   - Other key: value
#   (blank line separates subjects)
#   - key: val
#
# subkeys and other constructs are out of scope for now
#
import os
import sys
import re
import argparse
import json
import copy
import uuid

def multi_replace(text, replacements):
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags = re.DOTALL)
    return text


def clean_key(key):
    result = key.lower()
    result = result.rstrip(' ')
    result = multi_replace(result,[
        (' ', '_'),
        ('_/_', '/')
    ])
    return result


# TODO: maybe clean out ",? with (playful |prominent |promotional |bold )?text (element|overlay|overlaid)", and similar
# "with (stylized |Japanese )?text...", "with calendar overlay..."
# "with (stylized )?magazine layout
#
# grab all the setting/composition/style values to look for more
# text-like things to remove
#
def clean_val(val):
    val = multi_replace(val, [
        # text that is not "text"...
        (r' with (playful |prominent |promotional |bold )?text (element|overlay|overlaid).*$', ''),
        (r' with (stylized |Japanese )?text.*$', ''),
        (r' with (stylized )?magazine layout.*$', ''),
        (r' with calendar overlay.*$', ''),
        (r' with (a ?speech bubble.*$', ''),
        (r'^speech bubble.*$', ''),
        # yeah, LLMs are not good at age recognition...
        (r'young girl([., ])', r'young woman\1'),
        (r'young girls([., ])', r'young women\1'),
        (r'’', "'"),
        (r'^; ', ''),
        # shouldn't have been mentioned...
        (r'^not visible$', ''),
        # I told you not to, LLM!
        (r' \((indicated|implied) [^)]+\)', ''), 
        # remove trailing periods
        (r'\.+ *$', '')
    ])
    return val


# LLM-generated Markdown is not 100% consistent...
#
key_aliases = {
    "accessory": "accessories",
    "arm": "arms",
    "artistic_style": "style",
    "background_detail": "background_details",
    "background_object": "background_objects",
    "body_contours": "figure",
    "body_features": "figure",
    "body_posture": "pose",
    "body_shape": "figure",
    "body_type": "figure",
    "body": "figure",
    "bust": "figure",
    "bust_and_hips": "figure",
    "ear": "ears",
    "eye": "eyes",
    "facial_expression": "expression",
    "facial_features": "face",
    "facial_feature": "face",
    "foot": "feet",
    "hand": "hands",
    "hips": "figure",
    "illustration": "style",
    "leg": "legs",
    "logos": "logo",
    "overall_figure": "figure",
    "page_numbers": "page_number",
    "posture": "pose",
    "reflection": "reflections",
    "setting/background": "setting",
    "shoes": "footwear",
    "skin_tones": "skin_tone",
    "text/logo": "logo",
    "waist": "figure",
    "womans_clothing": "clothing",
    "womans_pose": "pose",
}

# strip all text from default output; this will not prevent random
# text from being invented by the model
#
textkeys_re = re.compile(r'(^font$|^font_style$|^name$|^typography$|^text$|^text_|_text$|_text_|^logo$|^logo_|_logo|_?watermark$|page_number|_labels?$|_indicator)')

# first pass at tagging any NSFW content
#
nsfw_re = re.compile(r'(nude|nudity|naked|nipples|pubic|breast|buttocks|vagina|bare butt|panty|panties)')

parser = argparse.ArgumentParser(
    prog='md2json',
    formatter_class = argparse.RawDescriptionHelpFormatter,
    description = 'parse simple markdown lists into JSON for prompting')
parser.add_argument('-d', '--debug',
    action='store_true',
    help='include debug data in output for QA')
parser.add_argument('files',
    nargs = '*',
    help='files containing Markdown dictionary lists')
args=parser.parse_args()

if len(args.files) == 0:
    files = [x.rstrip() for x in sys.stdin]
else:
    files = args.files
warnings = {}
for file in files:
    with open(file, 'r') as f:
        markdown = []
        current_subject = {}
        subjects = [ current_subject ]
        composition = ''
        setting = ''
        style = ''
        for line in f:
            line = line.rstrip()
            markdown.append(line)
            if re.search(r'^- ', line):
                match = re.search(r'^- ([^(:]+)([^:]*): *(.*)$', line)
                if match is None:
                    match = re.search(r'^- ([^(:]+)([^:]*) *(.*)$', line)
                key = clean_key(match.group(1))
                val = clean_val(match.group(3))
                if val != "":
                    if key in key_aliases:
                        orig_key = re.sub(r'^.*_', '', key)
                        key = key_aliases[key]
                        if key in current_subject:
                            val = f"{current_subject[key]}, {val} {orig_key}"
                    if key == 'subject' and len(current_subject) > 0:
                        # don't count on the blank line to separate multi
                        # TODO: rare, but happens that each line of text
                        # ends up a separate subject to skip! (4f3b8912.md)
                        # (miyako-sono10_5.md: "text block ...")
                        current_subject = {}
                        subjects.append(current_subject)
                    if key in ['facial_hair','accessories', 'age'] and re.search(r'^(none|not )', val):
                        # seriously, LLM?
                        continue
                    if key == 'setting':
                        if setting == '':
                            setting = val
                        elif val != setting:
                            if 'setting' in warnings:
                                warnings['setting'] += 1
                            else:
                                warnings['setting'] = 1
                    elif key == 'style':
                        if style == '':
                            style = val
                        elif val != style:
                            if 'style' in warnings:
                                warnings['style'] += 1
                            else:
                                warnings['style'] = 1
                    elif key == 'composition':
                        if composition == '':
                            composition = val
                        elif val != composition:
                            if 'composition' in warnings:
                                warnings['composition'] += 1
                            else:
                                warnings['composition'] = 1
                    else:
                        current_subject[key] = val
            elif re.search(r'^ *$', line) and len(current_subject) > 0:
                current_subject = {}
                subjects.append(current_subject)
            # subkeys are out of scope for now
            elif re.search(r'^ - ', line):
                print(f"REJECT_SUBKEYS {file}", file=sys.stderr)
                subjects = []
                break
            else:
                # fail out
                print(f"REJECT_BAFFLED {file}", file=sys.stderr)
                subjects = []
                break

        # empty means we broke out of inner loop
        if len(subjects) > 0:
            # strip all text-related fields
            tags = []
            multi = False
            nsfw = False
            japan = False
            if style == '':
                # caps to make the default stand out
                style = 'Natural Lifestyle Photography'
            if setting == '':
                # caps to make the default stand out
                setting = 'Intimate Boudoir Setting'
            if composition == '':
                # caps to make the default stand out
                composition = 'Centered'
            # if no age, add a default
            for subject in subjects:
                if 'age' not in subject:
                    subject['age'] = 'College-age'
            subjects_full = copy.deepcopy(subjects)
            for subject in subjects:
                textkeys = []
                for key in subject:
                    if re.search(r'(_images?$|_panels?$)', key):
                        multi = True
                    if re.search(nsfw_re, val):
                        # simple and crude, but catches many
                        nsfw = True
                    if re.search(r'Japan', key):
                        japan = True
                    if re.search(textkeys_re, key):
                        textkeys.append(key)
                for key in textkeys:
                    if 'hastext' not in tags:
                        tags.append('hastext')
                    del subject[key]

            # scrub empty subjects in with-text and textless version
            blank_i = []
            for index in reversed(range(0, len(subjects))):
                if len(subjects[index]) == 0:
                    blank_i.append(index)
            for index in blank_i:
                del subjects[index]
            blank_i = []
            for index in reversed(range(0, len(subjects_full))):
                if len(subjects_full[index]) == 0:
                    blank_i.append(index)
            for index in blank_i:
                del subjects_full[index]

            if multi:
                tags.append('multipanel')
            if len(subjects) > 1:
                tags.append('multisubject')
            if nsfw:
                tags.append('nsfw')
            if japan:
                tags.append('japan')
            id = str(uuid.uuid4())
            record = {
                "uuid": id,
                "tags": ','.join(tags),
                "json": json.dumps({
                    "style": style,
                    "setting": setting,
                    "composition": composition,
                    "subject": subjects,
                    "comment": id
                })
            }
            if args.debug:
                record['prompt'] = ''
                record['json_full'] = json.dumps({
                    "style": style,
                    "setting": setting,
                    "composition": composition,
                    "subject": subjects_full,
                    "comment": id
                })
                record['source_text'] = '\n'.join(markdown)
                record['source_file'] = file
            print(json.dumps(record))
for warning in ['setting', 'style', 'composition']:
    if warning in warnings:
        print(f"WARN_MULTIPLE_{warning.upper()}S: {warnings[warning]} files", file=sys.stderr)
