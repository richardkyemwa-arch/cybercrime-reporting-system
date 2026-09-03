#!/usr/bin/env bash
# build.sh – Render build script
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Initialising database and seeding data ==="
python seed_data.py

echo "=== Build complete ==="