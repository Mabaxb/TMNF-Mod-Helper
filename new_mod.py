#!/usr/bin/env python3
"""
new_mod.py - Create a new TMNF Stadium mod folder to start working from.

Copies Game_Textures_Base as it is, so the new mod gets the same layout:
  <dest>/<name>/
      (top-level files: icon, UI backgrounds, dirt marks/smoke)
      Image/            D textures + files that need manual work
      Moods/            Day, Night, Sunrise, Sunset + cloud textures

Usage:
  python new_mod.py <name> [--dest DIR] [--base DIR]

  name        Name of the mod folder to create
  --dest DIR  Where to create it (default: current folder)
  --base DIR  Base folder to copy (default: Game_Textures_Base next to this script)

Next step: edit the textures in Image/, then run
  python gen_maps.py "<dest>/<name>/Image"
to generate the N and S maps.
"""
import argparse
import shutil
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description='Create a new TMNF Stadium mod folder.')
    ap.add_argument('name')
    ap.add_argument('--dest', default='.')
    ap.add_argument('--base', default=str(Path(__file__).resolve().parent / 'Game_Textures_Base'))
    a = ap.parse_args()

    base = Path(a.base)
    if not base.is_dir():
        sys.exit(f"Base folder not found: {base}")
    mod = Path(a.dest) / a.name
    if mod.exists():
        sys.exit(f"{mod} already exists, pick another name or remove it first.")

    shutil.copytree(base, mod)

    files = [f for f in mod.rglob('*') if f.is_file()]
    print(f"Created {mod.resolve()}  ({len(files)} files copied from {base.name})")
    for d in sorted(p for p in mod.iterdir() if p.is_dir()):
        n = sum(1 for f in d.rglob('*') if f.is_file())
        subs = sorted(s.name for s in d.iterdir() if s.is_dir())
        print(f"  {d.name}/  {n} files" + (f"  ({', '.join(subs)})" if subs else ""))
    top = [f.name for f in mod.iterdir() if f.is_file()]
    if top:
        print(f"  top level: {', '.join(sorted(top))}")
    print(f'Next: edit the textures, then run  python gen_maps.py "{mod / "Image"}"')


if __name__ == '__main__':
    main()
