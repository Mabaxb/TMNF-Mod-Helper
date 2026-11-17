#!/usr/bin/env python3
"""
new_mod.py - Create a new TMNF Stadium mod folder to start working from.

Creates:
  <dest>/<name>/
      Image/            copy of Game_Textures_Base (D textures + files that need manual work)
      Moods/Day/
      Moods/Night/
      Moods/Sunrise/
      Moods/Sunset/     (only with --sunset)

Usage:
  python new_mod.py <name> [--dest DIR] [--base DIR] [--sunset]

  name        Name of the mod folder to create
  --dest DIR  Where to create it (default: current folder)
  --base DIR  Base texture folder (default: Game_Textures_Base next to this script)
  --sunset    Also create Moods/Sunset

Next step: put your edited textures in Image/, then run
  python gen_maps.py "<dest>/<name>/Image"
to generate the N and S maps.
"""
import argparse
import shutil
import sys
from pathlib import Path

MOODS = ['Day', 'Night', 'Sunrise']


def main():
    ap = argparse.ArgumentParser(description='Create a new TMNF Stadium mod folder.')
    ap.add_argument('name')
    ap.add_argument('--dest', default='.')
    ap.add_argument('--base', default=str(Path(__file__).resolve().parent / 'Game_Textures_Base'))
    ap.add_argument('--sunset', action='store_true')
    a = ap.parse_args()

    base = Path(a.base)
    if not base.is_dir():
        sys.exit(f"Base folder not found: {base}")
    mod = Path(a.dest) / a.name
    if mod.exists():
        sys.exit(f"{mod} already exists, pick another name or remove it first.")

    image = mod / 'Image'
    image.mkdir(parents=True)
    files = [f for f in sorted(base.iterdir()) if f.is_file()]
    for f in files:
        shutil.copy2(f, image / f.name)
    for mood in MOODS + (['Sunset'] if a.sunset else []):
        (mod / 'Moods' / mood).mkdir(parents=True)

    print(f"Created {mod.resolve()}")
    print(f"  Image/  {len(files)} textures from {base.name}")
    print(f"  Moods/  {', '.join(MOODS + (['Sunset'] if a.sunset else []))}")
    print(f'Next: edit the textures, then run  python gen_maps.py "{image}"')


if __name__ == '__main__':
    main()
