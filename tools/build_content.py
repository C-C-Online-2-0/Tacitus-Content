"""Compile the Tacitus Content UI pages and map registrations into a build directory.

Needs the RA3 MOD SDK and a clone of AptXmlAI. The output feeds tools/package.py.

BinaryAssetBuilder.exe is an AnyCPU program but loads a 32-bit texture compiler,
so on 64-bit Windows it fails with BadImageFormatException. This script builds a
32-bit copy of the SDK tools next to the work directory (the installed SDK is
only read, never changed) and uses that.

Map streams are not built here: they need a World Builder map.xml per map.
"""

import argparse
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PAGES = (
    "fe_m_assetsGameSetup",
    "fem_m_gameSetup",
    "fes_m_skirmishGameSetup",
    "feg_m_disconnect",
    "fem_m_load",
    "fem_m_postgameRoundup",
    "igm_pauseMenu",
)
POOLS = ("mapmetadata_tacitus", "mapmetadata_tacitus_corona")
EXTENSIONS = ("manifest", "bin", "imp", "relo")


def fail(message):
    raise SystemExit(f"build failed: {message}")


def make_x86_sdk(sdk, target):
    """Copy SDK tools with BinaryAssetBuilder forced to 32-bit, link the data folders."""
    if (target / "tools" / "BinaryAssetBuilder.exe").is_file():
        return
    shutil.copytree(sdk / "tools", target / "tools")
    exe = target / "tools" / "BinaryAssetBuilder.exe"
    data = bytearray(exe.read_bytes())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if struct.unpack_from("<H", data, pe + 24)[0] != 0x10B:
        fail("BinaryAssetBuilder.exe is not a PE32 file")
    rva = struct.unpack_from("<I", data, pe + 24 + 96 + 14 * 8)[0]
    sections = struct.unpack_from("<H", data, pe + 6)[0]
    optional = struct.unpack_from("<H", data, pe + 20)[0]
    for index in range(sections):
        offset = pe + 24 + optional + index * 40
        size, address, _, raw = struct.unpack_from("<IIII", data, offset + 8)
        if address <= rva < address + size:
            header = raw + rva - address
            break
    else:
        fail("BinaryAssetBuilder.exe has no CLR header")
    flags = struct.unpack_from("<I", data, header + 16)[0]
    struct.pack_into("<I", data, header + 16, flags | 0x2)  # 32BITREQUIRED
    exe.write_bytes(bytes(data))
    for name in ("Schemas", "SageXml"):
        link = target / name
        if not link.exists():
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f'New-Item -ItemType Junction -Path "{link}" -Target "{sdk / name}" | Out-Null'])
            if result.returncode:
                fail(f"could not link {name}")


def run(arguments, label):
    result = subprocess.run([str(a) for a in arguments])
    if result.returncode:
        fail(f"{label} exited with {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sdk", type=Path, required=True, help="RA3 MOD SDK root")
    parser.add_argument("--aptxmlai", type=Path, required=True, help="Cloned AptXmlAI root")
    parser.add_argument("--work", type=Path, required=True, help="Work directory; keep the path short")
    parser.add_argument("--build", type=Path, required=True, help="Output directory for tools/package.py")
    parser.add_argument("--corona", action="store_true", help="Also compile the Corona map registration (parked)")
    args = parser.parse_args()

    sdk = args.sdk.resolve()
    work = args.work.resolve()
    build = args.build.resolve()
    work.mkdir(parents=True, exist_ok=True)
    sdk32 = work / "sdk32"
    make_x86_sdk(sdk, sdk32)

    aptui = build / "data" / "aptui"
    aptui.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        page_work = work / "pages" / page
        if page_work.exists():
            shutil.rmtree(page_work)  # build_page.py needs a fresh directory
        run([sys.executable, ROOT / "tools/aptui/build_page.py",
             "--source", ROOT / "Data/aptui" / page / "edit.xml", "--name", page,
             "--aptxmlai", args.aptxmlai, "--sdk", sdk32, "--work", page_work], page)
        for built in (page_work / "package/data/aptui").iterdir():
            shutil.copyfile(built, aptui / built.name)

    meta_work = work / "metadata"
    if meta_work.exists():
        shutil.rmtree(meta_work)
    (meta_work / "stage").mkdir(parents=True)
    (meta_work / "out").mkdir()
    target = build / "data" / "tacitus8p"
    target.mkdir(parents=True, exist_ok=True)
    pools = POOLS if args.corona else POOLS[:1]
    for pool in pools:
        shutil.copyfile(ROOT / "Data/additionalmaps" / (pool + ".xml"), meta_work / "stage" / (pool + ".xml"))
        run([sdk32 / "tools/BinaryAssetBuilder.exe", meta_work / "stage" / (pool + ".xml"),
             f"/od:{meta_work / 'out'}", f"/iod:{meta_work / 'out'}",
             "/csc:false", "/ls:true", "/osh:false", "/pc:true", "/res:true", "/slowclean:true", "/ss:true",
             f"/sp:{sdk32 / 'Schemas/xsd/CnC3Types.xsd'}",
             f"/data:{meta_work / 'stage'};{sdk32 / 'SageXml'}",
             f"/art:{meta_work / 'stage'}", f"/audio:{meta_work / 'stage'}"], pool)
        for extension in EXTENSIONS:
            shutil.copyfile(meta_work / "out" / f"{pool}.{extension}", target / f"{pool}.{extension}")
    print(f"Built {len(PAGES)} pages and {len(pools)} map registration(s) into {build}")
    print("Map streams (data/maps/official/<map>/map.*) are still needed before a full release.")


if __name__ == "__main__":
    main()
