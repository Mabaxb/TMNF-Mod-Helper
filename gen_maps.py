#!/usr/bin/env python3
"""
gen_maps.py - Generate TrackMania Nations Forever (Stadium) N and S maps from D textures.

Only creates files that exist in the base game, in the same format as the game's file
(DXT1/DXT5, size relative to the D texture, full mipmaps). Each file is calibrated
against the game's original:
  N: DXT5nm swizzle (R=0, G=Y, B=Z, A=X), bump strength and height direction per texture
  S: per-channel level/contrast per texture; constant-tint S files keep their tint
  Inflatable* S: fully transparent (0 specular, 0 shininess)
  Left alone (never written): StadiumAirship*, StadiumRoadToDirtS
Shared maps: RoadTurboN serves Turbo, TurboRoulette and FreeWheeling (made from the
bottom half of StadiumRoadD by default). Fabric and
FabricPool share FabricN/FabricS. StartLogo uses the
WarpPub8X1 N/S; WarpLogos and PubNvidiaWorldcup share WarpLogos N/S (and DirtPub2x1S).

Usage:
  python gen_maps.py <D file or folder> [...] [options]
  python gen_maps.py --flag MyFlag.png [-o OUTDIR]     # writes StadiumWarpFlagA..X (not S)
  python gen_maps.py --clean <folder> [-y] [-r]          # delete every file that isn't a base game texture
  python gen_maps.py --glass-fix <folder or D file> [--glass-amount 0.1]  # counter in-game green on glass
  python gen_maps.py --clear-flags <folder>            # flags A..X (not S) -> fully transparent
  python gen_maps.py --list                            # show what the game has per texture

Options:
  -o, --out DIR        Output folder (default: next to the source file)
  --strength-mul F     Bumpiness multiplier (default 0.6; 1.0 = same as the game's maps)
  --turbo-n SRC        Source for the shared RoadTurboN: road (bottom half of StadiumRoadD,
                       default), turbo, roulette or freewheeling
  --spec-level F       Specular brightness (RGB) multiplier (default 0.5; 1.0 = game level)
  --spec-color F       How much the S takes the D's own colour instead of white
                       (default 0.6; 0 = game amount, 1 = fully coloured)
  --spec-mul F         Multiply specular contrast (default 1.0)
  --banners            Also generate the generic banner-cloth N/S (WarpLogos, WarpPub8X1, DirtPub2x1S)
                       from the logo D. Off by default: the game's cloth works for any logo.
  --glass-amount F     For --glass-fix: how much green to remove (default 0.1 = 10%).
                       Only ever applied to StadiumControlGlassD. In place, the original is
                       kept as <name>.dds.bak and re-runs always start from that backup.
  --overwrite          Overwrite existing files
  --uncompressed       Write uncompressed RGBA (no DXT, no mipmaps)
  -r, --recursive      Recurse into subfolders

Requires: pip install pillow numpy   (Pillow >= 11.2 for DXT output)
"""
import argparse
import io
import re
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# --- Game reference (from Stadium base files). D size is the game's D texture size. ---
# N:      (type, fmt, N size, game D size, strength, invert_height)
# S/S_dxt1: (type, fmt, S size, game D size, [(mean, std, corr) for brightness, alpha], colour)
#           brightness = max(R,G,B); colour = how much of the D's own colour the spec takes
# S_tint: (type, fmt, S size, game D size, [(mean, std, corr) per channel]) - constant tint
# N_flat: game uses a flat placeholder -> not generated
TABLE = {
    'StadiumAirshipN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 3.32, False),
    'StadiumAirshipS': ('S_tint', 'DXT5', (1024, 1024), (1024, 1024), [(0.906, 0.0, 0), (0.89, 0.0, 0), (0.906, 0.0, 0), (0.46, 0.044, 0.02)]),
    'StadiumCircuitLogoS': ('S', 'DXT5', (1024, 128), (1024, 128), [(1.0, 0.002, 0.0), (0.157, 0.0, 0)], 0.18),
    'StadiumCircuitN': ('N', 'DXT5', (2048, 1024), (2048, 1024), 10.35, False),
    'StadiumCircuitS': ('S', 'DXT5', (2048, 1024), (2048, 1024), [(0.944, 0.051, 0.21), (0.353, 0.185, 0.83)], 0.23),
    'StadiumControlAuvent2S': ('S_tint', 'DXT5', (512, 512), None, [(1.0, 0.0, 0), (1.0, 0.0, 0), (1.0, 0.0, 0), (0.886, 0.023, 0.5)]),
    'StadiumControlGlassN': ('N', 'DXT5', (128, 512), (128, 512), 3.57, True),
    'StadiumControlGlassS': ('S', 'DXT5', (128, 512), (128, 512), [(1.0, 0.0, 0.0), (0.767, 0.338, 0.75)], 0.0),
    'StadiumControlInteriorN': ('N', 'DXT5', (512, 512), (512, 512), 3.1, False),
    'StadiumControlInteriorS': ('S', 'DXT5', (512, 512), (512, 512), [(0.989, 0.034, 0.63), (0.539, 0.23, 0.92)], 0.04),
    'StadiumDirtPub2x1S': ('S_tint', 'DXT5', (512, 256), (512, 512), [(0.969, 0.0, 0), (0.953, 0.0, 0), (0.969, 0.0, 0), (0.295, 0.038, 0.5)]),
    'StadiumFabricFloorN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 18.44, False),
    'StadiumFabricFloorS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.901, 0.014, 0.52), (0.166, 0.025, 0.89)], 0.62),
    'StadiumFabricN': ('N', 'DXT5', (1024, 512), (1024, 512), 14.99, False),
    'StadiumFabricS': ('S_tint', 'DXT5', (1024, 512), (1024, 512), [(0.937, 0.0, 0), (0.984, 0.0, 0), (1.0, 0.0, 0), (0.098, 0.06, 0.33)]),
    'StadiumFabricStructureN': ('N', 'DXT5', (1024, 512), (1024, 512), 5.59, False),
    'StadiumFabricStructureS': ('S_tint', 'DXT5', (1024, 512), (1024, 512), [(1.0, 0.0, 0), (1.0, 0.0, 0), (1.0, 0.0, 0), (0.249, 0.042, 0.89)]),
    'StadiumInflatable2N': ('N', 'DXT5', (512, 512), (512, 512), 8.19, True),
    'StadiumInflatable2S': ('S', 'DXT5', (512, 512), (512, 512), [(0.26, 0.077, 0.84), (0.811, 0.095, -0.85)], 0.17),
    'StadiumInflatableN': ('N', 'DXT5', (512, 1024), (512, 1024), 3.29, False),
    'StadiumInflatableS': ('S_dxt1', 'DXT1', (128, 128), (512, 1024), [(0.937, 0.0, 0.0)], 0.0),
    'StadiumPillarN': ('N', 'DXT5', (128, 512), (128, 512), 4.0, False),  # game file is flat; typical strength
    'StadiumPillarS': ('S', 'DXT5', (128, 512), (128, 512), [(0.91, 0.037, 0.25), (0.816, 0.105, 0.6)], 0.12),
    'StadiumPlatformFloorN': ('N', 'DXT5', (1024, 512), (1024, 512), 20.92, False),
    'StadiumPlatformFloorS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.881, 0.02, 0.18), (0.702, 0.059, -0.07)], 0.07),
    'StadiumPlatformN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 10.38, False),
    'StadiumPlatformS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.888, 0.023, 0.7), (0.249, 0.09, -0.95)], 0.17),
    'StadiumRaceSignsRubberN': ('N', 'DXT5', (256, 512), (256, 512), 3.42, False),
    'StadiumRaceSignsRubberS': ('S', 'DXT5', (256, 512), (256, 512), [(0.945, 0.127, 0.21), (0.554, 0.38, 0.67)], 0.24),
    'StadiumRoadBorderN': ('N', 'DXT5', (1024, 512), (1024, 512), 8.06, False),
    'StadiumRoadBorderS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.986, 0.039, 0.38), (0.438, 0.253, 0.23)], 0.63),
    'StadiumRoadCircuitBorderN': ('N', 'DXT5', (512, 512), (512, 512), 3.96, False),
    'StadiumRoadCircuitBorderS': ('S', 'DXT5', (512, 512), (512, 512), [(0.992, 0.023, 0.37), (0.315, 0.126, 0.38)], 0.16),
    'StadiumRoadDetailsN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 5.77, False),
    'StadiumRoadDetailsS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.989, 0.03, 0.33), (0.567, 0.332, 0.91)], 0.02),
    'StadiumRoadDirtToRoadN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 4.96, False),
    'StadiumRoadDirtToRoadS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.184, 0.316, 0.05), (0.027, 0.055, 0.21)], 0.03),
    'StadiumRoadDirtTurboN': ('N', 'DXT5', (1024, 512), (1024, 512), 3.36, False),
    'StadiumRoadDirtTurboS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.474, 0.393, 0.21), (0.188, 0.209, 0.54)], 1.0),
    'StadiumRoadFreeWheelingS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.926, 0.161, 0.17), (0.464, 0.151, 0.81)], 0.46),
    'StadiumRoadGridN': ('N', 'DXT5', (512, 512), (512, 512), 4.78, False),
    'StadiumRoadGridS': ('S', 'DXT5', (512, 512), (512, 512), [(0.949, 0.06, 0.48), (0.435, 0.213, 0.61)], 0.06),
    'StadiumRoadN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 2.35, False),
    'StadiumRoadRaceN': ('N', 'DXT5', (256, 1024), (256, 1024), 3.34, False),
    'StadiumRoadRaceS': ('S', 'DXT5', (256, 1024), (256, 1024), [(0.917, 0.096, 0.4), (0.549, 0.151, 0.77)], 0.67),
    'StadiumRoadS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.996, 0.014, 0.33), (0.374, 0.223, -0.29)], 0.14),
    'StadiumRoadToDirtN': ('N', 'DXT5', (1024, 512), (1024, 512), 4.43, False),
    'StadiumRoadToDirtS': ('S', 'DXT5', (1024, 512), (1024, 512), [(1.0, 0.002, 0.0), (0.142, 0.12, 0.59)], 0.26),
    'StadiumRoadTurboN': ('N', 'DXT5', (1024, 512), (1024, 512), 3.82, False),
    'StadiumRoadTurboRouletteS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.956, 0.052, -0.46), (0.552, 0.21, -0.24)], 0.51),
    'StadiumRoadTurboS': ('S', 'DXT5', (1024, 512), (1024, 512), [(0.956, 0.052, 0.0), (0.552, 0.21, 0.13)], 0.91),
    'StadiumSculpt2N': ('N', 'DXT5', (1024, 256), (1024, 256), 4.65, True),
    'StadiumSculpt2S': ('S_dxt1', 'DXT1', (1024, 256), (1024, 256), [(0.95, 0.038, 0.95)], 0.02),
    'StadiumSculptN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 2.13, False),
    'StadiumSculptS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.995, 0.027, 0.43), (0.862, 0.064, 0.99)], 0.01),
    'StadiumSoundSystemN': ('N', 'DXT5', (1024, 128), (1024, 128), 4.76, False),
    'StadiumSoundSystemS': ('S', 'DXT5', (1024, 128), (1024, 128), [(0.907, 0.014, 0.77), (0.146, 0.108, 0.9)], 0.03),
    'StadiumStartSignN': ('N', 'DXT5', (128, 256), (128, 256), 23.0, False),
    'StadiumStartSignS': ('S', 'DXT5', (128, 256), (128, 256), [(0.97, 0.025, -0.79), (0.494, 0.25, 0.87)], 0.08),
    'StadiumStructureAlphaN': ('N', 'DXT5', (512, 1024), (512, 1024), 3.92, False),
    'StadiumStructureAlphaS': ('S_tint', 'DXT5', (512, 1024), (512, 1024), [(1.0, 0.0, 0), (1.0, 0.0, 0), (1.0, 0.0, 0), (0.434, 0.03, 0.11)]),
    'StadiumStructureGenericN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 3.03, False),
    'StadiumStructureGenericS': ('S_tint', 'DXT5', (512, 512), (1024, 1024), [(0.969, 0.0, 0), (0.969, 0.0, 0), (0.969, 0.0, 0), (0.391, 0.045, 0.91)]),
    'StadiumWarpAuvent2N': ('N_flat', 'TGA', (15, 16), (512, 512)),
    'StadiumWarpAuvent2S': ('S_tint', 'DXT5', (512, 512), (512, 512), [(0.937, 0.0, 0), (0.984, 0.0, 0), (1.0, 0.0, 0), (0.897, 0.059, 0.87)]),
    'StadiumWarpAuventAlphaN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 13.36, False),
    'StadiumWarpAuventAlphaS': ('S_tint', 'DXT5', (1024, 1024), (1024, 1024), [(0.937, 0.0, 0), (0.984, 0.0, 0), (1.0, 0.0, 0), (0.302, 0.176, 0.98)]),
    'StadiumWarpAuventN': ('N', 'DXT5', (512, 512), (512, 512), 3.27, False),
    'StadiumWarpAuventS': ('S', 'DXT5', (512, 512), (512, 512), [(0.994, 0.011, 0.29), (0.222, 0.123, 0.51)], 0.11),
    'StadiumWarpGlassN': ('N', 'DXT5', (512, 512), (512, 512), 4.27, False),
    'StadiumWarpGlassS': ('S', 'DXT5', (512, 512), (512, 512), [(1.0, 0.0, 0.0), (0.639, 0.348, 0.69)], 0.07),
    'StadiumWarpLogosN': ('N', 'DXT5', (256, 256), (512, 512), 1.0, False),
    'StadiumWarpLogosS': ('S_tint', 'DXT5', (128, 128), (512, 512), [(1.0, 0.0, 0), (1.0, 0.0, 0), (1.0, 0.0, 0), (0.989, 0.052, 0.08)]),
    'StadiumWarpParkingN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 1.77, False),
    'StadiumWarpParkingS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(1.0, 0.0, 0.0), (0.595, 0.109, 0.69)], 0.64),
    'StadiumWarpParvisN': ('N_flat', 'TGA', (15, 16), (512, 512)),
    'StadiumWarpParvisS': ('S_tint', 'DXT5', (1024, 1024), (512, 512), [(0.969, 0.0, 0), (0.953, 0.0, 0), (0.906, 0.0, 0), (0.228, 0.063, 0.67)]),
    'StadiumWarpPub8X1N': ('N', 'DXT5', (1024, 128), (1024, 128), 1.0, False),
    'StadiumWarpPub8X1S': ('S_tint', 'DXT5', (256, 32), (1024, 128), [(1.0, 0.0, 0), (1.0, 0.0, 0), (1.0, 0.0, 0), (0.983, 0.065, 0.5)]),
    'StadiumWarpRouteN': ('N_flat', 'TGA', (15, 16), (256, 256)),
    'StadiumWarpRouteS': ('S', 'DXT5', (256, 256), (256, 256), [(0.954, 0.028, 0.91), (0.188, 0.113, 0.25)], 0.26),
    'StadiumWarpSpotsN': ('N', 'DXT5', (128, 128), (128, 128), 3.17, False),
    'StadiumWarpSpotsS': ('S', 'DXT5', (128, 128), (128, 128), [(1.0, 0.001, 0.0), (0.474, 0.25, 0.82)], 0.03),
    'StadiumWarpStands2N': ('N', 'DXT5', (512, 512), (512, 512), 25.0, False),
    'StadiumWarpStands2S': ('S', 'DXT5', (512, 512), (512, 512), [(1.0, 0.0, 0.0), (0.223, 0.109, 0.74)], 0.22),
    'StadiumWarpStandsN': ('N', 'DXT5', (1024, 1024), (1024, 1024), 4.32, False),
    'StadiumWarpStandsS': ('S', 'DXT5', (1024, 1024), (1024, 1024), [(0.798, 0.36, 0.17), (0.217, 0.216, -0.16)], 0.2),}

# Which D texture(s) each map is made from, in priority order (first one found is used).
# Anything not listed uses its own <name>D.
SOURCES = {
    # Turbo N: bottom half of StadiumRoadD (plain road) unless --turbo-n says otherwise
    'StadiumRoadTurboN': ['StadiumRoadD:bottom', 'StadiumRoadTurboD', 'StadiumRoadTurboRouletteD',
                          'StadiumRoadFreeWheelingD'],
    'StadiumWarpPub8X1N': ['StadiumStartLogoD'],
    'StadiumWarpPub8X1S': ['StadiumStartLogoD'],
    'StadiumFabricN': ['StadiumFabricD', 'StadiumFabricPoolD'],
    'StadiumFabricS': ['StadiumFabricD', 'StadiumFabricPoolD'],
    'StadiumWarpLogosN': ['StadiumWarpLogosD', 'StadiumPubNvidiaWorldcup'],
    'StadiumWarpLogosS': ['StadiumWarpLogosD', 'StadiumPubNvidiaWorldcup'],
    'StadiumDirtPub2x1S': ['StadiumWarpLogosD', 'StadiumPubNvidiaWorldcup'],
}
# Bump strength when a shared N is made from a fallback D (calibrated per source)
SRC_STRENGTH = {('StadiumRoadTurboN', 'stadiumroadd'): 2.35,
                ('StadiumRoadTurboN', 'stadiumroadturborouletted'): 6.65,
                ('StadiumFabricN', 'stadiumfabricpoold'): 25.0}
# Game D size of a cropped source (scale reference)
CROP_DSIZE = {'bottom': lambda w, h: (w, h // 2)}
TURBO_N = {'road': 'StadiumRoadD:bottom', 'turbo': 'StadiumRoadTurboD',
           'roulette': 'StadiumRoadTurboRouletteD', 'freewheeling': 'StadiumRoadFreeWheelingD'}
# Never touched (need manual work / left as they are)
LEAVE_ALONE = {'StadiumRoadToDirtS'}
LEAVE_ALONE_MATCH = ('airship',)
# Generic banner-cloth maps (wrinkles, independent of the logo on them): only with --banners
BANNERS = {'StadiumWarpPub8X1N', 'StadiumWarpPub8X1S', 'StadiumWarpLogosN', 'StadiumWarpLogosS',
           'StadiumDirtPub2x1S'}

# Every texture file in the base game (Stadium), lowercase. Used by --clean.
BASE_FILES = {
    'stadiumairshipd.dds', 'stadiumairshipl.dds', 'stadiumairshipn.dds',
    'stadiumairshipo.dds', 'stadiumairships.dds', 'stadiumcircuitd.dds',
    'stadiumcircuitlogod.dds', 'stadiumcircuitlogos.dds', 'stadiumcircuitn.dds',
    'stadiumcircuits.dds', 'stadiumcircuitscreen.dds', 'stadiumcircuitscreenmask.dds',
    'stadiumcontrolauvent2s.dds', 'stadiumcontrolglassd.dds', 'stadiumcontrolglassn.dds',
    'stadiumcontrolglasss.dds', 'stadiumcontrolinteriord.dds', 'stadiumcontrolinteriorn.dds',
    'stadiumcontrolinteriors.dds', 'stadiumcontroll.dds', 'stadiumcontrolo.dds',
    'stadiumdirt1.dds', 'stadiumdirt2.dds', 'stadiumdirtgrid.dds',
    'stadiumdirtmask.dds', 'stadiumdirtpub2x1s.dds', 'stadiumdirtroad.dds',
    'stadiumdirtroadborderd.dds', 'stadiumfabricd.dds', 'stadiumfabricfloord.dds',
    'stadiumfabricfloorn.dds', 'stadiumfabricfloors.dds', 'stadiumfabricl.dds',
    'stadiumfabricn.dds', 'stadiumfabrico.dds', 'stadiumfabricpoold.dds',
    'stadiumfabrics.dds', 'stadiumfabricstructured.dds', 'stadiumfabricstructuren.dds',
    'stadiumfabricstructures.dds', 'stadiumfan.dds', 'stadiumgrass1.dds',
    'stadiumgrass2.dds', 'stadiumgrassfenced.dds', 'stadiumgrassl.dds',
    'stadiumgrassmask.dds', 'stadiumgrasso.dds', 'stadiumgrassstripe.dds',
    'stadiuminflatable2d.dds', 'stadiuminflatable2n.dds', 'stadiuminflatable2s.dds',
    'stadiuminflatablecactusd.dds', 'stadiuminflatablecactusl.dds', 'stadiuminflatablecactuso.dds',
    'stadiuminflatablecastled.dds', 'stadiuminflatabled.dds', 'stadiuminflatablen.dds',
    'stadiuminflatablepalmtreed.dds', 'stadiuminflatablepalmtreeo.dds', 'stadiuminflatables.dds',
    'stadiuminflatablesnowtreed.dds', 'stadiumloopl.dds', 'stadiumloopo.dds',
    'stadiumpillard.dds', 'stadiumpillarn.dds', 'stadiumpillars.dds',
    'stadiumplatformd.dds', 'stadiumplatformfloord.dds', 'stadiumplatformfloorn.dds',
    'stadiumplatformfloors.dds', 'stadiumplatformn.dds', 'stadiumplatforms.dds',
    'stadiumpubnvidiaworldcup.dds', 'stadiumracesignsrubberd.dds', 'stadiumracesignsrubbern.dds',
    'stadiumracesignsrubbers.dds', 'stadiumroadborderd.dds', 'stadiumroadbordern.dds',
    'stadiumroadborders.dds', 'stadiumroadcircuitborderd.dds', 'stadiumroadcircuitbordern.dds',
    'stadiumroadcircuitborders.dds', 'stadiumroadd.dds', 'stadiumroaddetailsd.dds',
    'stadiumroaddetailsn.dds', 'stadiumroaddetailss.dds', 'stadiumroaddirttoroadd.dds',
    'stadiumroaddirttoroadn.dds', 'stadiumroaddirttoroads.dds', 'stadiumroaddirtturbod.dds',
    'stadiumroaddirtturbon.dds', 'stadiumroaddirtturbos.dds', 'stadiumroadfreewheelingd.dds',
    'stadiumroadfreewheelings.dds', 'stadiumroadgridd.dds', 'stadiumroadgridn.dds',
    'stadiumroadgrids.dds', 'stadiumroadl.dds', 'stadiumroadl2.dds',
    'stadiumroadn.dds', 'stadiumroado.dds', 'stadiumroado2.dds',
    'stadiumroadraced.dds', 'stadiumroadracen.dds', 'stadiumroadraces.dds',
    'stadiumroads.dds', 'stadiumroadtodirtd.dds', 'stadiumroadtodirtn.dds',
    'stadiumroadtodirts.dds', 'stadiumroadturbod.dds', 'stadiumroadturbon.dds',
    'stadiumroadturborouletted.dds', 'stadiumroadturboroulettes.dds', 'stadiumroadturbos.dds',
    'stadiumsculpt2d.dds', 'stadiumsculpt2n.dds', 'stadiumsculpt2s.dds',
    'stadiumsculptd.dds', 'stadiumsculptn.dds', 'stadiumsculpts.dds',
    'stadiumsoundsystemd.dds', 'stadiumsoundsystemn.dds', 'stadiumsoundsystems.dds',
    'stadiumstartlogod.dds', 'stadiumstartlogos.dds', 'stadiumstartsignd.dds',
    'stadiumstartsignglow.dds', 'stadiumstartsignn.dds', 'stadiumstartsigns.dds',
    'stadiumstructurealphad.dds', 'stadiumstructurealphan.dds', 'stadiumstructurealphas.dds',
    'stadiumstructuregenericd.dds', 'stadiumstructuregenericn.dds', 'stadiumstructuregenerics.dds',
    'stadiumwarpauvent2d.dds', 'stadiumwarpauvent2n.tga', 'stadiumwarpauvent2s.dds',
    'stadiumwarpauventalphad.dds', 'stadiumwarpauventalphan.dds', 'stadiumwarpauventalphas.dds',
    'stadiumwarpauventd.dds', 'stadiumwarpauventn.dds', 'stadiumwarpauvents.dds',
    'stadiumwarpflaga.dds', 'stadiumwarpflagb.dds', 'stadiumwarpflagc.dds',
    'stadiumwarpflagd.dds', 'stadiumwarpflage.dds', 'stadiumwarpflagf.dds',
    'stadiumwarpflagg.dds', 'stadiumwarpflagh.dds', 'stadiumwarpflagi.dds',
    'stadiumwarpflagj.dds', 'stadiumwarpflagk.dds', 'stadiumwarpflagl.dds',
    'stadiumwarpflagm.dds', 'stadiumwarpflagn.dds', 'stadiumwarpflago.dds',
    'stadiumwarpflagp.dds', 'stadiumwarpflagq.dds', 'stadiumwarpflagr.dds',
    'stadiumwarpflags.dds', 'stadiumwarpflagt.dds', 'stadiumwarpflagu.dds',
    'stadiumwarpflagv.dds', 'stadiumwarpflagw.dds', 'stadiumwarpflagx.dds',
    'stadiumwarpglassd.dds', 'stadiumwarpglassn.dds', 'stadiumwarpglasso.dds',
    'stadiumwarpglasss.dds', 'stadiumwarpl.dds', 'stadiumwarpl2.dds',
    'stadiumwarpl3.dds', 'stadiumwarplogosd.dds', 'stadiumwarplogosn.dds',
    'stadiumwarplogoss.dds', 'stadiumwarpo.dds', 'stadiumwarpo2.dds',
    'stadiumwarpparkingd.dds', 'stadiumwarpparkingn.dds', 'stadiumwarpparkings.dds',
    'stadiumwarpparvisd.dds', 'stadiumwarpparvisn.tga', 'stadiumwarpparviss.dds',
    'stadiumwarppub8x1n.dds', 'stadiumwarppub8x1s.dds', 'stadiumwarprouted.dds',
    'stadiumwarprouten.tga', 'stadiumwarproutes.dds', 'stadiumwarpscreenmask.dds',
    'stadiumwarpspotsd.dds', 'stadiumwarpspotsglow.dds', 'stadiumwarpspotsn.dds',
    'stadiumwarpspotss.dds', 'stadiumwarpstands2d.dds', 'stadiumwarpstands2n.dds',
    'stadiumwarpstands2s.dds', 'stadiumwarpstands3d.dds', 'stadiumwarpstandsd.dds',
    'stadiumwarpstandsn.dds', 'stadiumwarpstandss.dds',
}

# Flags: letter -> (fmt, size). S (Norway) is never written.
FLAGS = {'A': ('DXT1', (128, 128)), 'B': ('DXT1', (128, 128)), 'C': ('DXT1', (128, 128)),
         'D': ('DXT1', (128, 128)), 'E': ('DXT1', (128, 128)), 'F': ('DXT1', (128, 128)),
         'G': ('DXT1', (128, 128)), 'H': ('DXT1', (128, 128)), 'I': ('DXT1', (128, 128)),
         'J': ('DXT1', (128, 128)), 'K': ('DXT1', (128, 64)), 'L': ('DXT1', (128, 64)),
         'M': ('DXT1', (128, 128)), 'N': ('DXT1', (128, 128)), 'O': ('DXT1', (128, 128)),
         'P': ('DXT1', (128, 128)), 'Q': ('DXT1', (128, 64)), 'R': ('DXT1', (128, 128)),
         'T': ('DXT1', (128, 128)), 'U': ('DXT1', (128, 128)), 'V': ('DXT5', (128, 128)),
         'W': ('DXT1', (128, 64)), 'X': ('DXT1', (128, 64))}
FLAG_RE = re.compile(r'^StadiumWarpFlag[A-X]$', re.I)
NO_SHINE = ('inflatable', 'airship')
TABLE_LC = {k.lower(): k for k in TABLE}


# ---------------------------------------------------------------- image helpers
def gblur(h, sigma):
    if sigma <= 0:
        return h
    fy = np.fft.fftfreq(h.shape[0])[:, None]
    fx = np.fft.fftfreq(h.shape[1])[None, :]
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(h) * k)).astype(np.float32)


def lum_at(img, size):
    g = img.convert('L')
    if g.size != size:
        g = g.resize(size, Image.BOX if size[0] < g.size[0] else Image.BICUBIC)
    return np.asarray(g, np.float32) / 255.0


def make_normal(lum, strength, invert):
    h = gblur(1.0 - lum if invert else lum, 1.0)
    p = lambda dy, dx: np.roll(np.roll(h, dy, 0), dx, 1)
    nx = -(p(0, -1) - p(0, 1)) * strength
    ny = (p(-1, 0) - p(1, 0)) * strength
    ln = np.sqrt(nx * nx + ny * ny + 1.0)
    to8 = lambda v: ((v / ln * 0.5 + 0.5) * 255).round().clip(0, 255).astype(np.uint8)
    X, Y, Z = to8(nx), to8(ny), to8(np.ones_like(nx))
    return np.dstack([np.zeros_like(X), Y, Z, X])          # DXT5nm


def _z(lum):
    sd = lum.std()
    return (lum - lum.mean()) / sd if sd > 1e-4 else np.zeros_like(lum)


def _level(z, stats, spec_mul):
    mean, std, corr = stats
    return (mean + corr * std * spec_mul * z).clip(0, 1)


def make_spec(lum, rgb, e, spec_mul, spec_level=1.0, spec_color=0.0):
    """S: brightness calibrated per texture, colour taken from the D itself.
    spec_color pushes every S further toward its D's own colour (0 = game amount, 1 = full)."""
    z = _z(lum)
    hue = rgb / np.maximum(rgb.max(-1, keepdims=True), 1e-3)
    if e[0] == 'S_tint':                                   # constant tint + alpha
        ch = [_level(z, c, spec_mul) for c in e[4]]
        k = spec_color
        ch = [ch[i] * ((1 - k) + k * hue[..., i]) for i in range(3)] + ch[3:]
    else:
        v = _level(z, e[4][0], spec_mul)
        k = e[5] + (1 - e[5]) * spec_color
        col = (1 - k) + k * hue
        ch = [v * col[..., i] for i in range(3)]
        ch.append(_level(z, e[4][1], spec_mul) if len(e[4]) > 1 else np.ones_like(v))
    if len(ch) == 3:
        ch.append(np.ones_like(ch[0]))
    ch = [c * spec_level for c in ch[:3]] + ch[3:]          # specular brightness (RGB only)
    return np.dstack([(c * 255).round().clip(0, 255).astype(np.uint8) for c in ch])


# ---------------------------------------------------------------- DDS writing
def _dxt(img, fmt):
    buf = io.BytesIO()
    img.save(buf, format='DDS', pixel_format=fmt)
    return buf.getvalue()


def save_dds(arr, path, fmt, uncompressed=False):
    img = Image.fromarray(arr, 'RGBA')
    if uncompressed:
        img.save(path, format='DDS')
        return
    try:
        first = _dxt(img, fmt)
    except Exception:
        sys.exit("Your Pillow can't write DXT. Run: python -m pip install -U pillow "
                 "(or use --uncompressed)")
    header, data = bytearray(first[:128]), [first[128:]]
    w, h = img.size
    levels = 1
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        data.append(_dxt(img.resize((w, h), Image.BOX), fmt)[128:])
        levels += 1
    # spec-correct header like the game's: CAPS|HEIGHT|WIDTH|PIXELFORMAT|MIPMAPCOUNT|LINEARSIZE
    h0, w0 = struct.unpack_from('<II', header, 12)
    block = 8 if fmt == 'DXT1' else 16
    struct.pack_into('<I', header, 8, 0xA1007)
    struct.pack_into('<I', header, 20, max(1, (w0 + 3) // 4) * max(1, (h0 + 3) // 4) * block)
    struct.pack_into('<I', header, 88, 0)              # no RGB bit count for compressed formats
    struct.pack_into('<I', header, 28, levels)
    struct.pack_into('<I', header, 108, struct.unpack_from('<I', header, 108)[0] | 0x401008)
    path.write_bytes(bytes(header) + b''.join(data))


# ---------------------------------------------------------------- generation
def scaled(size, scale):
    return tuple(max(4, int(round(s * scale / 4)) * 4) for s in size)


def sources_for(name, a=None):
    if name == 'StadiumRoadTurboN' and a is not None and a.turbo_n:
        return [TURBO_N[a.turbo_n]]
    return SOURCES.get(name, [name[:-1] + 'D'])


def open_source(src, crop):
    img = Image.open(src)
    img.load()
    if crop == 'bottom':
        img = img.crop((0, img.size[1] // 2, img.size[0], img.size[1]))
    return img


def generate(name, src, a, crop=None):
    e = TABLE[name]
    kind, fmt, size, dsize = e[0], e[1], e[2], e[3]
    outdir = Path(a.out) if a.out else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{name}.dds"
    if path.exists() and not a.overwrite:
        print(f"skip  {path.name} (exists)")
        return
    img = open_source(src, crop)
    if crop:
        dsize = (1024, 512)                      # game StadiumRoadD bottom half
    scale = img.size[0] / dsize[0] if dsize else 1.0
    osize = scaled(size, scale)
    lum = lum_at(img, osize)
    rgb = img.convert('RGB')
    if rgb.size != osize:
        rgb = rgb.resize(osize, Image.BOX if osize[0] < rgb.size[0] else Image.BICUBIC)
    rgb = np.asarray(rgb, np.float32) / 255.0
    if kind == 'N':
        st = SRC_STRENGTH.get((name, src.stem.lower()), e[4])
        arr = make_normal(lum, st * scale * a.strength_mul, e[5])
    elif any(s in name.lower() for s in NO_SHINE):
        arr = np.zeros((osize[1], osize[0], 4), np.uint8)       # fully transparent
    else:
        arr = make_spec(lum, rgb, e, a.spec_mul, a.spec_level, a.spec_color)
    save_dds(arr, path, fmt, a.uncompressed)
    print(f"ok    {src.name} -> {path.name} ({fmt} {osize[0]}x{osize[1]})")


def run(files, a):
    avail = {}
    for f in files:
        if not FLAG_RE.match(f.stem):
            avail.setdefault(f.stem.lower(), f)
    for name, e in TABLE.items():
        srcs = sources_for(name, a)
        found = []
        for sname in srcs:
            stem, _, crop = sname.partition(':')
            if stem.lower() in avail:
                found.append((avail[stem.lower()], crop or None))
        if not found:
            continue
        if name in LEAVE_ALONE or any(m in name.lower() for m in LEAVE_ALONE_MATCH):
            print(f"      {name}: left alone")
            continue
        if e[0] == 'N_flat':
            print(f"      {name}: game file is a flat placeholder, skipped")
            continue
        if name in BANNERS and not a.banners:
            print(f"      {name}: generic banner cloth, kept as game original (--banners to generate)")
            continue
        src, crop = found[0]
        if len(found) > 1 or crop:
            print(f"      {name}: using {src.name}" + (f" ({crop} half)" if crop else ""))
        try:
            generate(name, src, a, crop)
        except Exception as ex:
            print(f"FAIL  {name}: {ex}")


def write_flags(flag_file, a):
    img = Image.open(flag_file).convert('RGBA')
    img.load()
    outdir = Path(a.out) if a.out else Path(flag_file).parent
    outdir.mkdir(parents=True, exist_ok=True)
    for letter, (fmt, size) in FLAGS.items():
        path = outdir / f"StadiumWarpFlag{letter}.dds"
        if path.exists() and not a.overwrite:
            print(f"skip  {path.name} (exists)")
            continue
        arr = np.asarray(img.resize(size, Image.LANCZOS)).copy()
        if fmt == 'DXT1':
            arr[..., 3] = 255
        save_dds(arr, path, fmt, a.uncompressed)
    print(f"ok    flags A-X (except S) written to {outdir}")


def clean(folder, a):
    folder = Path(folder)
    me = Path(__file__).resolve()
    files = sorted(folder.rglob('*') if a.recursive else folder.glob('*'))
    junk = [f for f in files if f.is_file() and f.name.lower() not in BASE_FILES
            and f.resolve() != me]
    if not junk:
        print(f"Nothing to delete: {folder} only has base game files.")
        return
    for f in junk:
        print(f"  {f.relative_to(folder)}")
    print(f"{len(junk)} non-base file(s) in {folder}.")
    if not a.yes and input("Delete them? [y/N] ").strip().lower() != 'y':
        print("Cancelled, nothing deleted.")
        return
    for f in junk:
        f.unlink()
    print(f"Deleted {len(junk)} file(s).")


GLASS_FIX_FILES = {'stadiumcontrolglassd.dds'}       # WarpGlassD doesn't need it


def glass_files(paths):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.glob('*') if f.name.lower() in GLASS_FIX_FILES)
        elif p.name.lower() in GLASS_FIX_FILES:
            yield p
        else:
            print(f"skip  {p.name} (green fix only applies to StadiumControlGlassD)")


def glass_fix(paths, a):
    """Counter the game's green tint on glass: less green, more red/blue, same brightness."""
    amt = a.glass_amount
    k = amt * 0.59 / 0.41                       # keeps luminance (0.3R + 0.59G + 0.11B) unchanged
    gain = np.array([1 + k, 1 - amt, 1 + k], np.float32)
    files = list(glass_files(paths))
    if not files:
        print("No glass D textures found.")
    for p in files:
        raw = p.read_bytes()
        fourcc = raw[84:88].decode('latin1') if raw[:4] == b'DDS ' else ''
        fmt = fourcc if fourcc in ('DXT1', 'DXT3', 'DXT5') else 'DXT5'
        arr = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
        arr[..., :3] = (arr[..., :3] * gain).clip(0, 255)
        out = (Path(a.out) if a.out else p.parent) / p.name
        if out.resolve() == p.resolve():
            bak = p.with_name(p.name + '.bak')
            if not bak.exists():
                bak.write_bytes(raw)
            else:
                raw = bak.read_bytes()          # always start from the original, never stack fixes
                arr = np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA')).astype(np.float32)
                arr[..., :3] = (arr[..., :3] * gain).clip(0, 255)
        elif out.exists() and not a.overwrite:
            print(f"skip  {out.name} (exists)")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        save_dds(arr.round().astype(np.uint8), out, fmt, a.uncompressed)
        # keep the original alpha exactly: copy the alpha half of every DXT3/DXT5 block
        new = bytearray(out.read_bytes())
        if fmt in ('DXT3', 'DXT5') and not a.uncompressed and len(new) == len(raw) \
                and new[84:88] == raw[84:88]:
            for i in range(128, len(new) - 15, 16):
                new[i:i + 8] = raw[i:i + 8]
            out.write_bytes(bytes(new))
        print(f"ok    {p.name}: green -{amt:.0%}, red/blue +{k:.0%} ({fmt})")


def clear_flags(folder, a):
    """Replace StadiumWarpFlagA-X (not S) with fully transparent textures."""
    outdir = Path(a.out) if a.out else Path(folder)
    outdir.mkdir(parents=True, exist_ok=True)
    for letter, (fmt, (w, h)) in FLAGS.items():
        save_dds(np.zeros((h, w, 4), np.uint8), outdir / f"StadiumWarpFlag{letter}.dds", fmt,
                 a.uncompressed)
    print(f"ok    flags A-X (except S) replaced with transparent textures in {outdir}")


def list_table():
    for k, e in TABLE.items():
        print(f"{k:32} {e[0]:7} {e[1]:5} {e[2][0]}x{e[2][1]}")


def collect(paths, recursive):
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob('*') if recursive else p.glob('*')):
                if f.suffix.lower() == '.dds':
                    yield f
        elif p.suffix.lower() == '.dds':
            yield p


def main():
    ap = argparse.ArgumentParser(description='Generate TMNF N and S maps from D textures.')
    ap.add_argument('inputs', nargs='*')
    ap.add_argument('-o', '--out')
    ap.add_argument('--strength-mul', type=float, default=0.6)
    ap.add_argument('--spec-mul', type=float, default=1.0)
    ap.add_argument('--spec-level', type=float, default=0.5)
    ap.add_argument('--spec-color', type=float, default=0.6)
    ap.add_argument('--flag')
    ap.add_argument('--clear-flags', metavar='DIR')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--glass-fix', nargs='+', metavar='PATH')
    ap.add_argument('--glass-amount', type=float, default=0.1)
    ap.add_argument('--clean', metavar='DIR')
    ap.add_argument('-y', '--yes', action='store_true')
    ap.add_argument('--banners', action='store_true')
    ap.add_argument('--turbo-n', choices=list(TURBO_N))
    ap.add_argument('--overwrite', action='store_true')
    ap.add_argument('--uncompressed', action='store_true')
    ap.add_argument('-r', '--recursive', action='store_true')
    a = ap.parse_args()
    if a.list:
        return list_table()
    if a.clean:
        return clean(a.clean, a)
    if a.glass_fix:
        return glass_fix(a.glass_fix, a)
    if a.clear_flags:
        return clear_flags(a.clear_flags, a)
    if a.flag:
        write_flags(a.flag, a)
    if not a.inputs:
        if not a.flag:
            ap.print_help()
        return
    run(list(collect(a.inputs, a.recursive)), a)


if __name__ == '__main__':
    main()
