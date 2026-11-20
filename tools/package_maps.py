"""Zip the eight-player maps so players can drop them into their own Maps folder.

Custom maps need no compiled streams: a folder holding the .map, its _art.tga
and map.str is enough. The zip root holds one folder per map, to be unpacked into
%APPDATA%\\Red Alert 3\\Maps. Online rooms transfer a custom map from the host,
so this download is a convenience, not a requirement.
"""

import argparse
from pathlib import Path
import re
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package import POOLS, ROOT, fail, pool_maps  # noqa: E402

MAPS = ROOT / "Additional/Data/maps/official"
INSTALL = """Tacitus eight-player maps

Unzip the folders in this archive into:

    %APPDATA%\\Red Alert 3\\Maps

so that you end up with, for example:

    %APPDATA%\\Red Alert 3\\Maps\\RA3BN_Magmagma_1_0\\RA3BN_Magmagma_1_0.map

The maps then show up under custom maps in Red Alert 3. They are for the
eight-player support in Tacitus and need it enabled to use all eight slots.

The maps were made for RA3BattleNet. See
https://github.com/C-C-Online-2-0/Tacitus-Content for credits and permissions.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, e.g. 0.1.0")
    parser.add_argument("--corona", action="store_true", help="Also include the Corona-only maps (parked)")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        fail("version must look like 1.0.0")

    names = []
    for pool in (POOLS if args.corona else ("vanilla",)):
        for name in pool_maps(pool):
            if name not in names:
                names.append(name)

    files = []
    for name in names:
        folder = MAPS / name
        for needed in (f"{name}.map", f"{name}_art.tga", "map.str"):
            if not (folder / needed).is_file():
                fail(f"{name} is missing {needed}")
            files.append((folder / needed, f"{name}/{needed}"))

    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.out / f"tacitus-8p-maps-{args.version}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("INSTALL.txt", INSTALL)
        for source, arcname in files:
            zipped.write(source, arcname)
    print(f"Wrote {archive} ({len(names)} maps)")


if __name__ == "__main__":
    main()
