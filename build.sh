#!/bin/bash
# Install dependencies if not present (requires pip)
# pip install -r requirements.txt nuitka zstandard patchelf

# Compile the tool
python3 -m nuitka --onefile --standalone --follow-imports src/god_tool.py
