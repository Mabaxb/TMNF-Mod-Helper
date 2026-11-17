# TMNF Stadium texture types

Auto generated from game textures (Might have some errors). L/O (lightmap/occlusion) files are listed but ignored.

## Map types

- **N**: Normal map, DXT5nm (R=0, G=Y, B=Z, A=X)
- **S**: Specular colour (RGB) + shininess (A)
- **S_tint**: Constant colour tint (RGB), shininess varies (A)
- **S_dxt1**: Specular colour only, DXT1 (no shininess channel)

## Textures with D / N / S

| Texture | D | N | S | Script generates |
|---|---|---|---|---|
| StadiumAirship | DXT1 1024x1024 | N (DXT5 1024x1024) | S_tint (DXT5 1024x1024) | nothing (left alone) |
| StadiumCircuit | DXT1 2048x1024 | N (DXT5 2048x1024) | S (DXT5 2048x1024) | N, S |
| StadiumCircuitLogo | DXT1 1024x128 | - | S (DXT5 1024x128) | S |
| StadiumControlAuvent2 | - | - | S_tint (DXT5 512x512) | S (needs a D you supply) |
| StadiumControlGlass | DXT5 128x512 | N (DXT5 128x512) | S (DXT5 128x512) | N, S |
| StadiumControlInterior | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumDirtPub2x1 | - | - | S_tint (DXT5 512x256) | nothing by default (generic banner cloth for PubNvidiaWorldcup/WarpLogos; `--banners` = from WarpLogosD) |
| StadiumDirtRoadBorder | DXT5 1024x1024 | - | - | nothing |
| StadiumFabric | DXT1 1024x512 | N (DXT5 1024x512) | S_tint (DXT5 1024x512) | N, S |
| StadiumFabricFloor | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumFabricPool | DXT1 1024x512 | shared: FabricN | shared: FabricS | nothing (uses Fabric N/S) |
| StadiumFabricStructure | DXT1 1024x512 | N (DXT5 1024x512) | S_tint (DXT5 1024x512) | N, S |
| StadiumGrassFence | DXT5 2048x256 | - | - | nothing |
| StadiumInflatable | DXT1 512x1024 | N (DXT5 512x1024) | S_dxt1 (DXT1 128x128) | N, S (transparent) |
| StadiumInflatable2 | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S (transparent) |
| StadiumInflatableCactus | DXT1 256x512 | - | - | nothing |
| StadiumInflatableCastle | DXT1 512x512 | - | - | nothing |
| StadiumInflatablePalmTree | DXT1 512x512 | - | - | nothing |
| StadiumInflatableSnowTree | DXT1 256x256 | - | - | nothing |
| StadiumPillar | DXT1 128x512 | N (DXT5 128x512) | S (DXT5 128x512) | N, S |
| StadiumPlatform | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumPlatformFloor | DXT1 1024x512 | N (DXT5 1024x512) | S (DXT5 1024x512) | N, S |
| StadiumRaceSignsRubber | DXT1 256x512 | N (DXT5 256x512) | S (DXT5 256x512) | N, S |
| StadiumRoad | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumRoadBorder | DXT1 1024x512 | N (DXT5 1024x512) | S (DXT5 1024x512) | N, S |
| StadiumRoadCircuitBorder | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumRoadDetails | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumRoadDirtToRoad | DXT5 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumRoadDirtTurbo | DXT1 1024x512 | N (DXT5 1024x512) | S (DXT5 1024x512) | N, S |
| StadiumRoadFreeWheeling | DXT1 1024x512 | shared: RoadTurboN | S (DXT5 1024x512) | S |
| StadiumRoadGrid | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumRoadRace | DXT1 256x1024 | N (DXT5 256x1024) | S (DXT5 256x1024) | N, S |
| StadiumRoadToDirt | DXT1 1024x512 | N (DXT5 1024x512) | S (DXT5 1024x512) | N (S left alone: needs manual work) |
| StadiumRoadTurbo | DXT1 1024x512 | N (DXT5 1024x512) | S (DXT5 1024x512) | N (shared with TurboRoulette + FreeWheeling, made from bottom of StadiumRoadD), S |
| StadiumRoadTurboRoulette | DXT5 1024x512 | shared: RoadTurboN | S (DXT5 1024x512) | S |
| StadiumSculpt | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumSculpt2 | DXT1 1024x256 | N (DXT5 1024x256) | S_dxt1 (DXT1 1024x256) | N, S |
| StadiumSoundSystem | DXT1 1024x128 | N (DXT5 1024x128) | S (DXT5 1024x128) | N, S |
| StadiumStartLogo | DXT1 1024x128 | - | uses WarpPub8X1 N/S | nothing (banner cloth kept, see below) |
| StadiumStartSign | DXT1 128x256 | N (DXT5 128x256) | S (DXT5 128x256) | N, S |
| StadiumStructureAlpha | DXT1 512x1024 | N (DXT5 512x1024) | S_tint (DXT5 512x1024) | N, S |
| StadiumStructureGeneric | DXT1 1024x1024 | N (DXT5 1024x1024) | S_tint (DXT5 512x512) | N, S |
| StadiumWarpAuvent | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumWarpAuvent2 | DXT1 512x512 | TGA 15x16 (flat placeholder, no bumps; not generated) | S_tint (DXT5 512x512) | S |
| StadiumWarpAuventAlpha | DXT3 1024x1024 | N (DXT5 1024x1024) | S_tint (DXT5 1024x1024) | N, S |
| StadiumWarpGlass | DXT5 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumWarpLogos | DXT1 512x512 | N (DXT5 256x256) | S_tint (DXT5 128x128) | nothing by default (generic banner cloth, shared with PubNvidiaWorldcup; `--banners` = from WarpLogosD) |
| StadiumWarpParking | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumWarpParvis | DXT1 512x512 | TGA 15x16 (flat placeholder, no bumps; not generated) | S_tint (DXT5 1024x1024) | S |
| StadiumWarpPub8X1 | - | N (DXT5 1024x128) | S_tint (DXT5 256x32) | nothing by default (generic banner cloth; `--banners` = from StartLogoD) |
| StadiumWarpRoute | DXT1 256x256 | TGA 15x16 (flat placeholder, no bumps; not generated) | S (DXT5 256x256) | S |
| StadiumWarpSpots | DXT1 128x128 | N (DXT5 128x128) | S (DXT5 128x128) | N, S |
| StadiumWarpStands | DXT1 1024x1024 | N (DXT5 1024x1024) | S (DXT5 1024x1024) | N, S |
| StadiumWarpStands2 | DXT1 512x512 | N (DXT5 512x512) | S (DXT5 512x512) | N, S |
| StadiumWarpStands3 | DXT1 512x512 | - | - | nothing |

## Left alone

- All StadiumAirship textures.
- StadiumRoadToDirtS (special texture, needs manual work).

## Shared maps

- **StadiumRoadTurboN** is used by RoadTurbo, RoadTurboRoulette and RoadFreeWheeling. Made from the bottom half of StadiumRoadD by default; `--turbo-n turbo|roulette|freewheeling` to use one of those instead.
- **StadiumFabricN / FabricS** are used by Fabric and FabricPool (made from FabricD; falls back to FabricPoolD).
- **StadiumStartLogo** uses StadiumWarpPub8X1 N/S (StartLogoS is not used, so it isn't generated).
- **StadiumPubNvidiaWorldcup** and **StadiumWarpLogos** share WarpLogos N and S, and in some cases use StadiumDirtPub2x1S.
- The WarpPub8X1, WarpLogos and DirtPub2x1 maps are generic banner-cloth wrinkles with no logo detail, so they work with any logo and are kept as the game's originals unless you pass `--banners`.

## Other textures (no N/S, not generated)

| File | Format | Type |
|---|---|---|
| StadiumCircuitScreen.dds | DXT1 1024x256 | Screen (solid black) |
| StadiumCircuitScreenMask.dds | DXT5 512x512 | Screen mask (alpha) |
| StadiumDirt1.dds | DXT1 1024x1024 | Tiling ground texture |
| StadiumDirt2.dds | DXT1 1024x1024 | Tiling ground texture |
| StadiumDirtGrid.dds | DXT5 256x256 | Overlay with alpha |
| StadiumDirtMask.dds | DXT1 1024x1024 | Blend mask (grayscale) |
| StadiumDirtRoad.dds | DXT5 2048x2048 | Diffuse with alpha (dirt road) |
| StadiumFan.dds | DXT5 128x128 | Alpha-only (crowd/fan cutout) |
| StadiumGrass1.dds | DXT1 1024x1024 | Tiling ground texture |
| StadiumGrass2.dds | DXT1 1024x1024 | Tiling ground texture |
| StadiumGrassMask.dds | DXT1 1024x1024 | Blend mask (grayscale) |
| StadiumGrassStripe.dds | DXT1 2048x2048 | Tiling ground texture |
| StadiumPubNvidiaWorldcup.dds | DXT1 512x512 | Advert (diffuse) - uses WarpLogos N/S |
| StadiumStartSignGlow.dds | DXT1 64x64 | Glow / emissive |
| StadiumWarpScreenMask.dds | DXT5 256x256 | Screen mask (alpha) |
| StadiumWarpSpotsGlow.dds | DXT1 512x512 | Glow / emissive |

## Flags (`--flag`)

StadiumWarpFlagA–X, all DXT1 128x128 except: K, L, Q, W, X = DXT1 128x64; V = DXT5 128x128. `--flag` writes all of them from one image, skipping S (Norway).

## Ignored (L / O)

StadiumAirshipL.dds, StadiumAirshipO.dds, StadiumControlL.dds, StadiumControlO.dds, StadiumFabricL.dds, StadiumFabricO.dds, StadiumGrassL.dds, StadiumGrassO.dds, StadiumInflatableCactusL.dds, StadiumInflatableCactusO.dds, StadiumInflatablePalmTreeO.dds, StadiumLoopL.dds, StadiumLoopO.dds, StadiumRoadL.dds, StadiumRoadL2.dds, StadiumRoadO.dds, StadiumRoadO2.dds, StadiumWarpGlassO.dds, StadiumWarpL.dds, StadiumWarpL2.dds, StadiumWarpL3.dds, StadiumWarpO.dds, StadiumWarpO2.dds
