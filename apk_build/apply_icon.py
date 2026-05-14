#!/usr/bin/env python3
"""Apply app icon to Android mipmap folders."""
import os
from pathlib import Path
from PIL import Image

# Sizes: (folder_suffix, size_px)
SIZES = [
    ("mdpi", 48),
    ("hdpi", 72),
    ("xhdpi", 96),
    ("xxhdpi", 144),
    ("xxxhdpi", 192),
]

SCRIPT_DIR = Path(__file__).resolve().parent
RES_DIR = SCRIPT_DIR / "android" / "app" / "src" / "main" / "res"
ICON_SRC = SCRIPT_DIR.parent / "static" / "icon-512.png"

if not ICON_SRC.exists():
    print(f"Error: {ICON_SRC} not found")
    exit(1)

img = Image.open(ICON_SRC).convert("RGBA")
for suffix, size in SIZES:
    folder = RES_DIR / f"mipmap-{suffix}"
    folder.mkdir(parents=True, exist_ok=True)
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    for name in ["ic_launcher.png", "ic_launcher_foreground.png", "ic_launcher_round.png"]:
        out = folder / name
        resized.save(out)
        print(f"Saved {out}")

print("Icon applied successfully.")
