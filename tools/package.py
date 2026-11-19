"""Assemble a Tacitus eight-player content release.

Inputs are this repository plus a build directory holding the compiled streams
that need the RA3 MOD SDK (manifest, bin, imp, relo). Nothing is compiled here.

Expected build directory:
    data/aptui/<page>.8pv1.{manifest,bin,imp,relo}        build_page.py package output
    data/maps/official/<map>/map.{manifest,bin,imp,relo}  BinaryAssetBuilder output
    data/tacitus8p/mapmetadata_tacitus[_corona].{manifest,bin,imp,relo}

The zip root is the Tacitus content root, to be unpacked into the game's
Data/Tacitus folder.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent / "aptui"))
from check_release import EIGHT_PLAYER_STREAMS, STREAM_EXTENSIONS, check_stream  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VERSION_BYTES = b".8pv1\r\n"
POOLS = {
    "vanilla": "mapmetadata_tacitus",
    "corona": "mapmetadata_tacitus_corona",
}
MAP_SOURCE_SUFFIXES = (".map", "_art.tga")


def fail(message):
    raise SystemExit(f"package failed: {message}")


def pool_maps(pool):
    """Directory names registered in one metadata pool."""
    path = ROOT / "Data/additionalmaps" / (POOLS[pool] + ".xml")
    names = []
    for element in ET.parse(path).getroot().iter("{uri:ea.com:eala:asset}MapMetaData"):
        filename = element.get("FileName")
        if filename:
            names.append(filename.replace("\\", "/").split("/")[-2])
    if not names:
        fail(f"{path.name} has no maps")
    return names


def require_streams(base, stem, label):
    for extension in STREAM_EXTENSIONS:
        if not (base / f"{stem}.{extension}").is_file():
            fail(f"missing {label}: {stem}.{extension}")


def stage(build, staging, pools):
    # priority files must be byte exact or the engine rejects the version
    for page in EIGHT_PLAYER_STREAMS:
        source = ROOT / "priority/data/aptui" / (page + ".version")
        if source.read_bytes() != VERSION_BYTES:
            fail(f"{source} must contain exactly {VERSION_BYTES!r}")
        target = staging / "priority/data/aptui" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    aptui = build / "data/aptui"
    for page in EIGHT_PLAYER_STREAMS:
        require_streams(aptui, page + ".8pv1", "ui stream")
        try:
            check_stream(aptui / (page + ".8pv1.manifest"))
        except ValueError as error:
            fail(str(error))
        for extension in STREAM_EXTENSIONS:
            name = f"{page}.8pv1.{extension}"
            target = staging / "data/aptui" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(aptui / name, target)
        cdata = aptui.glob(page + ".8pv1*.cdata")
        for sidecar in cdata:
            shutil.copyfile(sidecar, staging / "data/aptui" / sidecar.name)

    maps = []
    for pool in pools:
        for name in pool_maps(pool):
            if name not in maps:
                maps.append(name)
        require_streams(build / "data/tacitus8p", POOLS[pool], "map metadata")
        for extension in STREAM_EXTENSIONS:
            name = f"{POOLS[pool]}.{extension}"
            target = staging / "data/tacitus8p" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(build / "data/tacitus8p" / name, target)

    for name in maps:
        source = ROOT / "Additional/Data/maps/official" / name
        compiled = build / "data/maps/official" / name
        target = staging / "data/maps/official" / name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "map.str", target / "map.str")
        for suffix in MAP_SOURCE_SUFFIXES:
            shutil.copyfile(source / (name + suffix), target / (name + suffix))
        require_streams(compiled, "map", f"map {name}")
        for extension in STREAM_EXTENSIONS:
            shutil.copyfile(compiled / f"map.{extension}", target / f"map.{extension}")
        version = compiled / "map.version"
        if version.is_file():
            shutil.copyfile(version, target / "map.version")
    return maps


def manifest(staging, version, pools, maps):
    files = {}
    for path in sorted(p for p in staging.rglob("*") if p.is_file()):
        files[path.relative_to(staging).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (staging / "content.json").write_text(
        json.dumps({"format": 1, "version": version, "pools": pools, "maps": maps, "files": files},
                   indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", type=Path, required=True, help="Directory of compiled streams")
    parser.add_argument("--version", required=True, help="Release version, e.g. 1.0.0")
    parser.add_argument("--pool", choices=("vanilla", "corona", "all"), default="all")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        fail("version must look like 1.0.0")
    pools = list(POOLS) if args.pool == "all" else [args.pool]
    if not args.build.is_dir():
        fail(f"build directory not found: {args.build}")

    staging = ROOT / "staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    maps = stage(args.build, staging, pools)
    manifest(staging, args.version, pools, maps)

    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.out / f"tacitus-content-{args.version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            zipped.write(path, path.relative_to(staging).as_posix())
    shutil.rmtree(staging)
    print(f"Wrote {archive} ({len(maps)} maps, pools: {', '.join(pools)})")


if __name__ == "__main__":
    main()
