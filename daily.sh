#!/bin/bash

cd /Users/geniusmachado/Desktop/Python\ Course\ Hari || exit

# Run Python script to fetch stats
/usr/bin/env python3 yt_stats.py

# Git commands
git add youtube_stats.json
git commit -m "Update YouTube stats on $(date)"
git push origin main

