#!/usr/bin/env bash
#
# The lmstudio Python SDK keeps going into loops with various
# models, so I'm doing this by hand with the supplied `lms` CLI.

sysprompt=$(cat sysprompts/tagging.txt)

infile="$1"

while read -r prompt; do
    echo "$prompt" | lms chat -s "$sysprompt" qwen/qwen3-vl-4b
done < $infile
