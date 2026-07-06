#!/usr/bin/env bash

echo "sequential"
upcycle color=colors < test1.jsonl 
echo
echo "sequential, one per prompt" 
upcycle color=!colors < test1.jsonl 
echo

echo "random"
upcycle color=rand:colors < test1.jsonl 
echo
echo "random, one per prompt"
upcycle color=rand!colors < test1.jsonl 
echo

echo "shuffled"
upcycle color=shuf:colors < test1.jsonl 
echo
echo "shuffled, one per prompt"
upcycle color=shuf!colors < test1.jsonl 
echo

echo "sorted"
upcycle color=sort:colors < test1.jsonl 
echo
echo "sorted, one per prompt"
upcycle color=sort!colors < test1.jsonl 
echo

echo "weighted random (more orange, less blue)"
upcycle color=rand:wcolors < test1.jsonl
