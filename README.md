# Tacitus Content

> # ⚠️ NONE OF THIS DOES ANYTHING YET
>
> **Do not install this. It will not give you eight player games.**
>
> This repo is work in progress source material. There is no release, nothing here has been run in game, and the compiled files the game needs have not been built or packaged. The Tacitus code that would load this content is also unreleased and off by default.
>
> See [Current state](#current-state) for exactly what exists and what is missing.

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
| UI page streams (`manifest`, `bin`, `imp`, `relo`) | Build with `tools/build_content.py`; the offline checks pass. Not tested in game |
| Map registration streams | Build with `tools/build_content.py`. Not tested in game |
| **Map streams** (`map.manifest` and friends) | **4 of the 6 base game maps exported and compiled** (Battlebase Sigma, Fallout Fortress, Island Adventure, Joint Operations). Winter Showdown and Magmagma do not load in World Builder yet. The four Corona-only maps are parked. Streams not yet packaged |
| Release packager | Works, including a `--ui-only` mode for testing without the maps |
| Drop-in maps zip | Works (`tools/package_maps.py`), all six base game maps, not tested in game |
| Tacitus support for loading this content | Written (priority provider, content folder, map registrations) and builds, but untested and not released |
| In-game testing | Not done |
| Corona | **Parked.** The Corona-only maps and map registration stay in the repo but are not built, packaged or supported for now |
| Licence | Not chosen yet |

A full release is blocked on the map streams. The UI and the registrations can already be built and packaged with `--ui-only`, which is enough to try the lobby screens but not to play an eight-player map.

## What is here

| Path | Contents |
| --- | --- |
| `Data/aptui/` | Editable sources for the seven `.8pv1` UI pages and their build entry XMLs |
| `Additional/Data/maps/official/` | The eight-player maps (`.map`, minimap, `map.str`) |
| `Data/additionalmaps/` | Map registration, one file per pool: `mapmetadata_tacitus.xml` (base game and Corona) and `mapmetadata_tacitus_corona.xml` (Corona only) |
| `priority/data/aptui/` | The seven `.version` files that make the game use the `.8pv1` pages |
| `tools/aptui/` | `build_page.py` builds one page, `check_release.py` checks sources and compiled streams |
| `tools/maps/` | `update_crc.py` keeps map CRCs in the metadata in step with the map files |
| `tools/build_content.py` | Compiles the UI pages and map registrations into a build directory |
| `tools/build_maps.py` | Compiles the World Builder `map.xml` exports into map streams |
| `tools/package_maps.py` | Zips the eight-player maps as drop-in custom maps for `%APPDATA%\Red Alert 3\Maps` |
| `tools/package.py` | Assembles the release zip from this repo and a build directory |
| `docs/` | The `.8pv1` UI guide, provenance and validation records, map notes |

### Pages

`fe_m_assetsGameSetup`, `fem_m_gameSetup`, `fes_m_skirmishGameSetup`, `feg_m_disconnect`, `fem_m_load`, `fem_m_postgameRoundup` and `igm_pauseMenu`.

### Maps

Base game and Corona: Battlebase Sigma, Fallout Fortress, Island Adventure, Joint Operations, Winter Showdown, Magmagma.
Corona only: 22442 (8p and RandomTeams), Winter Showdown RandomTeams, Magmagma RandomTeams.

## Content root

A release zip unpacks into the `Tacitus` folder inside the game's `Data` folder (the one that holds `Tacitus.ini`):

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

1. Build the pages and map registrations:
   `python tools/build_content.py --sdk "<RA3 MOD SDK>" --aptxmlai <AptXmlAI clone> --work <short work dir> --build <build dir>`
   Keep the work path short. `BinaryAssetBuilder.exe` crashes on 64-bit Windows because it loads a 32-bit texture compiler, so the script builds a 32-bit copy of the SDK tools in the work directory and leaves your SDK untouched.
2. Map streams. Each map needs a `map.xml` that World Builder writes:
   1. Open the map in World Builder straight from its folder under `Additional/Data/maps/official/`.
   2. Wait for it to finish loading, then save with Ctrl+S. No edit is needed: `map.xml` appears next to the `.map`, and the `.map` itself is rewritten.
   3. Opening is slow for big maps. Wait until the title bar and the status bar both show the new map.
   4. Check the object count in World Builder's status bar before saving. `Objs: 0` means the map did not load, and saving it writes an empty export and damages the `.map`. If that happens, `git checkout` the map.
   5. When you are done, restore the rewritten `.map` files with `git checkout -- Additional/Data/maps`. The `map.xml` files are ignored by git and kept locally.
   6. Run `python tools/build_maps.py --sdk "<RA3 MOD SDK>" --work <short work dir> --build <build dir>`. It compiles every `map.xml` into `<build dir>/data/maps/official/<map>/map.*`.
3. If you do change a `.map` for real, run `python tools/maps/update_crc.py --write`, then `--check`, and rebuild the registrations with step 1.
4. Package: `python tools/package.py --build <build dir> --version 1.0.0`, or add `--ui-only` while the map streams are missing.

To work on a single page, use `tools/aptui/build_page.py` directly, as described in [docs/aptui/8pv1-guide.en.md](docs/aptui/8pv1-guide.en.md).

`tools/package.py` refuses to produce a zip if any stream, map file or `.version` file is missing or wrong.

## Playing the maps without a release

Custom maps do not need compiled streams or registration. A folder with the `.map`, its `_art.tga` and `map.str` is enough. `python tools/package_maps.py --version 0.1.0` zips the six base game maps so players can unpack them into `%APPDATA%\Red Alert 3\Maps`. Online rooms transfer a custom map from the host, so the download is a convenience. This is the quickest way to test the lobby, since it does not depend on the map streams.

## Adding a map

Put the map under `Additional/Data/maps/official/` and register it in `mapmetadata_tacitus.xml` (or the Corona file) with `NumPlayers="8"`, `IsMultiplayer="true"`, `IsOfficial="true"` and all eight start positions. Then update the CRCs. The guide in `docs/` covers the details; it was written for RA3BattleNet, so read its file names as the Tacitus ones.

## Differences from RA3BattleNet's Content repo

- Only the eight-player pages and maps were imported, with their history. The RA3BattleNet-only streams (`ra3battlenet.swf`, the splash, the connection panel and the rest) and the other map pools are not here.
- The map registration files are renamed so they cannot clash with RA3BattleNet's.
- `check_release.py` no longer expects the RA3BattleNet streams or the development button.
- `tools/package.py` and the `priority` folder are new here.

## Licence

No licence has been chosen yet. The content is used with the written permission of begosik and RA3BattleNet, described in [NOTICE.md](NOTICE.md). Ask before reusing it elsewhere.
