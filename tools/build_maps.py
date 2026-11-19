"""Compile the eight-player map streams from World Builder exports.

Each map folder under Additional/Data/maps/official needs a map.xml that World
Builder wrote next to the .map file (open the map, make a trivial change such as
adding then deleting a script, and save). This turns every map.xml into
map.manifest, map.bin, map.imp and map.relo in the build directory.

Re-saving also rewrites the .map. Restore it afterwards with git checkout: the
streams only need map.xml, and the maps then stay byte-identical to the originals
so their registered CRCs remain valid.
"""

import argparse
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_content import EXTENSIONS, ROOT, fail, make_x86_sdk, run  # noqa: E402
from package import POOLS, pool_maps  # noqa: E402


def expected_maps(corona):
    names = []
    for pool in (POOLS if corona else ("vanilla",)):
        for name in pool_maps(pool):
            if name not in names:
                names.append(name)
    return names


_SCRIPT_LIST = re.compile(r'[ \t]*<GameScriptList\s+id="[^"]*">.*?</GameScriptList>\s*?\n?', re.S)


def drop_duplicate_script_lists(text):
    """World Builder sometimes writes the same empty script list twice, which
    BinaryAssetBuilder rejects as a duplicate instance. Only exact repeats go."""
    seen = set()
    removed = []

    def keep(match):
        block = match.group(0)
        if block in seen:
            removed.append(re.search(r'id="([^"]*)"', block).group(1))
            return ""
        seen.add(block)
        return block

    result = _SCRIPT_LIST.sub(keep, text)
    return result, removed


def check_export(name, export):
    head = export.read_text(encoding="utf-8", errors="replace")[:400000]
    found = re.search(r'<GameMap\s+id="([^"]+)"', head)
    if not found:
        fail(f"{export} has no GameMap element, is it a World Builder export?")
    if found.group(1).casefold() != name.casefold():
        fail(f"{export} describes {found.group(1)}, expected {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sdk", type=Path, required=True, help="RA3 MOD SDK root")
    parser.add_argument("--work", type=Path, required=True, help="Work directory; keep the path short")
    parser.add_argument("--build", type=Path, required=True, help="Output directory for tools/package.py")
    parser.add_argument("--maps", type=Path, default=ROOT / "Additional/Data/maps/official",
                        help="Folder of map folders, each holding map.xml")
    parser.add_argument("--only", action="append", default=[], help="Build just this map (repeatable)")
    parser.add_argument("--corona", action="store_true", help="Also build the Corona-only maps (parked)")
    args = parser.parse_args()

    sdk = args.sdk.resolve()
    work = args.work.resolve()
    sdk32 = work / "sdk32"
    work.mkdir(parents=True, exist_ok=True)
    make_x86_sdk(sdk, sdk32)

    names = args.only or expected_maps(args.corona)
    missing = [n for n in names if not (args.maps / n / "map.xml").is_file()]
    if missing:
        fail("no map.xml for: " + ", ".join(missing))

    for name in names:
        export = args.maps / name / "map.xml"
        check_export(name, export)
        stage = work / "maps" / name / "stage"
        out = work / "maps" / name / "out"
        if stage.parent.exists():
            shutil.rmtree(stage.parent)
        stage.mkdir(parents=True)
        out.mkdir()
        text, removed = drop_duplicate_script_lists(export.read_text(encoding="utf-8"))
        (stage / "map.xml").write_text(text, encoding="utf-8", newline="")
        if removed:
            print(f"{name}: dropped duplicate script lists {', '.join(removed)}")
        run([sdk32 / "tools/BinaryAssetBuilder.exe", stage / "map.xml",
             f"/od:{out}", f"/iod:{out}",
             "/csc:false", "/ls:true", "/osh:false", "/pc:true", "/res:true", "/slowclean:true", "/ss:true",
             f"/sp:{sdk32 / 'Schemas/xsd/CnC3Types.xsd'}",
             f"/data:{stage};{sdk32 / 'SageXml'}",
             f"/art:{stage};{sdk / 'Art'}", f"/audio:{stage};{sdk / 'audio'}"], name)
        target = args.build.resolve() / "data" / "maps" / "official" / name
        target.mkdir(parents=True, exist_ok=True)
        for extension in EXTENSIONS:
            built = out / f"map.{extension}"
            if not built.is_file():
                fail(f"{name}: BinaryAssetBuilder produced no map.{extension}")
            shutil.copyfile(built, target / built.name)
        print(f"Built {name}")


if __name__ == "__main__":
    main()
