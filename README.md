# TMNF Mod helpers

Notes and tools for making TrackMania Nations Forever (Stadium) mods.
(Only for the Image folder. Nothing outside or the moods)

## Mod making notes

### Texture sizes (for resizing textures so they match up)

| Texture | Size |
|---|---|
| StadiumRoadToDirtD.dds ||
| Dirt to road border (StadiumRoadBorderD) | Scale the height to 317 and palce it 423px from the bottom | 
| Dirt to road road (StadiumRoadD) | Scale by 665 |
| Loading screen | Scale from 768 to the black borders to avoid the image looking squished |
| Dirt booster | Scale the height of the dirt texture to 789 if you want it as the base (looks kinda bad still) |

### BIK files

- Under 100k bytes
- 3 seconds 

### DDS files

| Map | Format |
|---|---|
| D (diffuse) | BC1, or BC3 for transparency |
| N (normal) | BC3 (DXT5), swizzled: R=0, G=Y, B=Z, A=X |
| S (specular) | BC3 (DXT5): RGB = specular colour, A = shininess |

### TGA files

- Origin bottom left
- No RLE compression

## Links

- [TMNF Mod Filelist](https://tmnf.exchange/threadshow/604690)
- [TMNF Mods (vinummusik.de)](http://www.vinummusik.de/Trackmania/)
- [Stadium mods on ManiaPark](https://maniapark.com/search/mods?q=environment%3A+stadium+game%3A+trackmania1)

## gen_maps.py

Generates N (normal) and S (specular/shininess) maps from D textures, calibrated against the
base game's own files. It only creates N/S files that exist in the base game, in the same
format and size.

Requires Python 3 and `pip install pillow numpy` (Pillow 11.2 or newer for DXT output).

```
python gen_maps.py <mod Image folder> [--overwrite]
```

| Option | What it does |
|---|---|
| `-o DIR` | Write output to another folder |
| `--overwrite` | Replace existing N/S files |
| `--strength-mul F` | Bumpiness (default 0.6, 1.0 = game level) |
| `--spec-level F` | Specular brightness (default 0.5, 1.0 = game level) |
| `--spec-color F` | How much the S takes the D's colour instead of white (default 0.6) |
| `--turbo-n SRC` | Source for the shared turbo N: `road` (bottom of StadiumRoadD, default), `turbo`, `roulette`, `freewheeling` |
| `--banners` | Also generate the generic banner-cloth N/S (WarpLogos, WarpPub8X1, DirtPub2x1S) |
| `--flag IMAGE` | Write StadiumWarpFlagA–X (not S) from one image |
| `--clear-flags DIR` | Replace StadiumWarpFlagA–X (not S) with transparent textures |
| `--glass-fix PATH` | Counter the game's green tint on StadiumControlGlassD |
| `--clean DIR` | Delete every file that isn't a base game texture (asks first) |
| `--list` | Show what the game has per texture |

Behaviour worth knowing:

- Never touches StadiumAirship textures or StadiumRoadToDirtS.
- Inflatable S maps are written fully transparent.
- RoadTurboN is by default created using the bottom half of the road texture
- Shared maps: RoadTurboN covers Turbo, TurboRoulette and FreeWheeling; Fabric and FabricPool share FabricN/FabricS; 
  Unsure shared textures: StartLogo uses the WarpPub8X1 N/S; WarpLogos and PubNvidiaWorldcup share the WarpLogos N/S.
- The red ropes on castle blocks use one of the sign textures.
- Flag files (StadiumWarpFlagA–X) are never treated as D textures.

See [TEXTURE_TYPES.md](TEXTURE_TYPES.md) for the type and format of every Stadium texture.
