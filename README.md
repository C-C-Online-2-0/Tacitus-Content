# Tacitus Content

Game content for the eight-player support in [Tacitus](https://github.com/C-C-Online-2-0/Tacitus): the eight-player lobby UI, the eight-player maps, and the small files that make Red Alert 3 pick them up.

Tacitus holds the code. This repo holds the assets, their sources and the tools to build and package them, so the two can change on their own schedules.

Credits and permissions are in [NOTICE.md](NOTICE.md).

## Current state

This repo is a source repo. It is **not a ready-to-install package yet**, and none of it has been tested in game.

| | State |
| --- | --- |
| UI page sources (7 `.8pv1` pages) | Imported from RA3BattleNet, unchanged |
| Eight-player maps (10) | Imported, CRCs verified |
| Map registration (2 pools) | Done, validated with the CRC tool |
| `priority` version files | Done |
| Release packager | Done, tested only on synthetic input |
| **Compiled streams** (`manifest`, `bin`, `imp`, `relo`) | **Not built.** They need the RA3 MOD SDK and AptXmlAI, so there is no release zip yet |
| Tacitus support for loading this content | In development in Tacitus, not released |
| In-game testing | Not done |
| Licence | Not chosen yet |

Until the streams are built and Tacitus can load them, installing this repo does nothing.

## What is here

| Path | Contents |
| --- | --- |
| `Data/aptui/` | Editable sources for the seven `.8pv1` UI pages and their build entry XMLs |
| `Additional/Data/maps/official/` | The eight-player maps (`.map`, minimap, `map.str`) |
| `Data/additionalmaps/` | Map registration, one file per pool: `mapmetadata_tacitus.xml` (base game and Corona) and `mapmetadata_tacitus_corona.xml` (Corona only) |
| `priority/data/aptui/` | The seven `.version` files that make the game use the `.8pv1` pages |
| `tools/aptui/` | `build_page.py` builds one page, `check_release.py` checks sources and compiled streams |
| `tools/maps/` | `update_crc.py` keeps map CRCs in the metadata in step with the map files |
| `tools/package.py` | Assembles the release zip from this repo and a build directory |
| `docs/` | The `.8pv1` UI guide, provenance and validation records, map notes |

### Pages

`fe_m_assetsGameSetup`, `fem_m_gameSetup`, `fes_m_skirmishGameSetup`, `feg_m_disconnect`, `fem_m_load`, `fem_m_postgameRoundup` and `igm_pauseMenu`.

### Maps

Base game and Corona: Battlebase Sigma, Fallout Fortress, Island Adventure, Joint Operations, Winter Showdown, Magmagma.
Corona only: 22442 (8p and RandomTeams), Winter Showdown RandomTeams, Magmagma RandomTeams.

## Content root

A release zip unpacks into the game's `Data/Tacitus` folder:

```
priority/data/aptui/<page>.version        forces the .8pv1 pages
data/aptui/<page>.8pv1.{manifest,bin,imp,relo}
data/maps/official/<map>/...
data/tacitus8p/mapmetadata_tacitus[_corona].{manifest,bin,imp,relo}
content.json                              version and a hash of every file
```

The game resolves `data/...` paths against every search folder, so this folder works as one. Tacitus reads the `priority` folder itself so its `.version` files win over the stock and mod archives. Do not put UI files in it.

## Building a release

You need Windows, Python 3.9 or later, the RA3 MOD SDK (for `BinaryAssetBuilder.exe`) and [AptXmlAI](https://git.ra3battle.cn/RA3CoronaDevelopers/AptXmlAI).

1. Check the sources: `python tools/aptui/check_release.py inputs <entry xml files>`
2. Build each page with `tools/aptui/build_page.py`, as described in [docs/aptui/8pv1-guide.en.md](docs/aptui/8pv1-guide.en.md). Collect the `package/data/aptui` output of every page into one build directory.
3. Compile every map folder and both metadata XMLs with the SDK into the same build directory, laid out as described at the top of `tools/package.py`.
4. If you touched a `.map`, run `python tools/maps/update_crc.py --write`, then `--check`.
5. Package: `python tools/package.py --build <build dir> --version 1.0.0`

`tools/package.py` refuses to produce a zip if any stream, map file or `.version` file is missing or wrong.

## Adding a map

Put the map under `Additional/Data/maps/official/` and register it in `mapmetadata_tacitus.xml` (or the Corona file) with `NumPlayers="8"`, `IsMultiplayer="true"`, `IsOfficial="true"` and all eight start positions. Then update the CRCs. The guide in `docs/` covers the details; it was written for RA3BattleNet, so read its file names as the Tacitus ones.

## Differences from RA3BattleNet's Content repo

- Only the eight-player pages and maps were imported, with their history. The RA3BattleNet-only streams (`ra3battlenet.swf`, the splash, the connection panel and the rest) and the other map pools are not here.
- The map registration files are renamed so they cannot clash with RA3BattleNet's.
- `check_release.py` no longer expects the RA3BattleNet streams or the development button.
- `tools/package.py` and the `priority` folder are new here.

## Licence

No licence has been chosen yet. The content is used with the written permission of begosik and RA3BattleNet, described in [NOTICE.md](NOTICE.md). Ask before reusing it elsewhere.
