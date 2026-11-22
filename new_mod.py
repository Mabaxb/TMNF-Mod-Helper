#!/usr/bin/env python3
"""
new_mod.py - Create a new TMNF Stadium mod folder to start working from.

The new mod gets this layout:
  <dest>/<name>/
      DirtMarks.dds, DirtSmoke.dds, Icon.dds, UiBgBottomCenterRace.dds, UiBgCard.dds
      Image/            D textures + files that need manual work (no N/S maps)
      Moods/            Day, Night, Sunrise, Sunset (.tga files) + cloud textures

Files come from either:
  - a base folder (default: Game_Textures_Base next to this script), copied as it is, or
  - the game itself with --from-game, picking the same files from the game's GameData folder.
If the base folder doesn't exist, the game folder is used automatically.

Usage:
  python new_mod.py <name> [--dest DIR] [--base DIR]
  python new_mod.py <name> --from-game [GAMEDATA]

  name              Name of the mod folder to create
  --dest DIR        Where to create it (default: current folder)
  --base DIR        Base folder to copy (default: Game_Textures_Base next to this script)
  --from-game [DIR] Take the files from the game (default:
                    C:\\Program Files (x86)\\TmNationsForever\\GameData)

Tip: python new_mod.py Game_Textures_Base --from-game --dest <script folder>
     (re)creates the base folder from your game install.

Next step: edit the textures in Image/, then run
  python gen_maps.py "<dest>/<name>/Image"
to generate the N and S maps.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

DEFAULT_GAMEDATA = r'C:\Program Files (x86)\TmNationsForever\GameData'
MOODS = ['Day', 'Night', 'Sunrise', 'Sunset']
# top-level mod files: name -> location inside GameData
TOP_FILES = {
    'DirtMarks.dds': 'Vehicles/Media/Texture/Image/DirtMarks.dds',
    'DirtSmoke.dds': 'Vehicles/Media/Texture/Image/DirtSmoke.dds',
    'Icon.dds': 'Stadium/Media/Texture Icon/Image/IconEnvStadium.dds',
    'UiBgBottomCenterRace.dds': 'Interface/Media/Texture/Image/UiBgBottomCenterRace.dds',
    'UiBgCard.dds': 'Interface/Media/Texture/Image/UiBgCard.dds',
}
GAME_IMAGE = 'Stadium/Media/Texture/Image'
GAME_MOODS = 'Stadium/Media/Moods'
# S files that are kept in Image/ (they need manual work, not generated)
KEEP_S = {'stadiumairships', 'stadiumcontrolauvent2s', 'stadiumroaddirttoroads',
          'stadiumroadtodirts'}
FLAG_RE = re.compile(r'^StadiumWarpFlag[A-X]$', re.I)


def wanted_image(f: Path) -> bool:
    """Same selection as Game_Textures_Base: .dds, no N maps, no S maps except KEEP_S."""
    if f.suffix.lower() != '.dds' or f.name.lower() == 'loadscreen.dds':
        return False
    stem = f.stem
    if FLAG_RE.match(stem):
        return True
    if stem.endswith('N'):
        return False
    if stem.endswith('S') and stem.lower() not in KEEP_S:
        return False
    return True


def copy_from_game(gamedata: Path, mod: Path):
    """Build the mod folder from the game's GameData folder."""
    plan = []
    for name, rel in TOP_FILES.items():
        plan.append((gamedata / rel, mod / name))
    for f in sorted((gamedata / GAME_IMAGE).iterdir()):
        if f.is_file() and wanted_image(f):
            plan.append((f, mod / 'Image' / f.name))
    moods = gamedata / GAME_MOODS
    for f in sorted(moods.iterdir()):
        if f.is_file() and f.suffix.lower() == '.dds':          # StadiumFXClouds*.dds
            plan.append((f, mod / 'Moods' / f.name))
    for mood in MOODS:
        for f in sorted((moods / mood).iterdir()):
            if f.is_file() and f.suffix.lower() == '.tga':
                plan.append((f, mod / 'Moods' / mood / f.name))
    missing = [str(src) for src, _ in plan if not src.is_file()]
    if missing:
        sys.exit("Missing in the game folder:\n  " + "\n  ".join(missing))
    for src, dst in plan:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser(description='Create a new TMNF Stadium mod folder.')
    ap.add_argument('name')
    ap.add_argument('--dest', default='.')
    ap.add_argument('--base', default=str(Path(__file__).resolve().parent / 'Game_Textures_Base'))
    ap.add_argument('--from-game', nargs='?', const=DEFAULT_GAMEDATA, metavar='GAMEDATA')
    a = ap.parse_args()

    mod = Path(a.dest) / a.name
    if mod.exists():
        sys.exit(f"{mod} already exists, pick another name or remove it first.")

    base = Path(a.base)
    gamedata = Path(a.from_game) if a.from_game else None
    if gamedata is None and not base.is_dir():
        if Path(DEFAULT_GAMEDATA).is_dir():
            print(f"{base.name} not found, taking the files from the game instead.")
            gamedata = Path(DEFAULT_GAMEDATA)
        else:
            sys.exit(f"Base folder not found: {base}\n"
                     f"Use --base DIR, or --from-game PATH_TO_GAMEDATA.")

    if gamedata is not None:
        if not (gamedata / GAME_IMAGE).is_dir():
            sys.exit(f"Not a TMNF GameData folder (no {GAME_IMAGE}): {gamedata}")
        copy_from_game(gamedata, mod)
        source = str(gamedata)
    else:
        shutil.copytree(base, mod)
        source = base.name

    files = [f for f in mod.rglob('*') if f.is_file()]
    print(f"Created {mod.resolve()}  ({len(files)} files from {source})")
    for d in sorted(p for p in mod.iterdir() if p.is_dir()):
        n = sum(1 for f in d.rglob('*') if f.is_file())
        subs = sorted(s.name for s in d.iterdir() if s.is_dir())
        print(f"  {d.name}/  {n} files" + (f"  ({', '.join(subs)})" if subs else ""))
    top = sorted(f.name for f in mod.iterdir() if f.is_file())
    if top:
        print(f"  top level: {', '.join(top)}")
    print(f'Next: edit the textures, then run  python gen_maps.py "{mod / "Image"}"')


if __name__ == '__main__':
    main()
