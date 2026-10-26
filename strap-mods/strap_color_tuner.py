#!/usr/bin/env python3
"""
Strap color tuner for NewBanknotes_AddonStrapFix_P (add-on v1.2)

Changes the strap (pack band) color of EUR 5, EUR 10 and EUR 100 in the add-on's .ucas file.
Colors are normal sRGB hex codes (what a color picker shows). Only 12 bytes per strap are edited,
so the file size never changes. A backup (.bak) is made the first time you run it.

Examples (PowerShell):
  python strap_color_tuner.py --show
  python strap_color_tuner.py --eur5 "#868A90"
  python strap_color_tuner.py --eur5 9A9EA4 --eur10 C8202B --eur100 3F7D57
  python strap_color_tuner.py --restore            # put the original colors back (from the .bak)
  python strap_color_tuner.py --file "D:\\path\\to\\NewBanknotes_AddonStrapFix_P.ucas" --eur5 888888

Then restart the game (colors load at startup). If you use Vortex, run this on the file inside the
mod's Vortex staging folder (Vortex > mod > Open in File Manager) and click Deploy - or run it on the
deployed file in the game's ~mods folder for quick experiments (a later Vortex deploy/purge may revert it).
"""
import argparse, os, shutil, struct, sys

NAME = "NewBanknotes_AddonStrapFix_P.ucas"
DEFAULT_DIRS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Cash Cleaner Simulator\CashCleanerSimulator\Content\Paks\~mods",
    r"C:\Program Files\Steam\steamapps\common\Cash Cleaner Simulator\CashCleanerSimulator\Content\Paks\~mods",
    ".",
]
# file offset of the strap color (TapeColorB, 3 x float32 linear RGB) for each asset in the .ucas.
# The 4-float TapeColorA (cream tape) sits 49 bytes before it and is used as a safety check.
OFFSETS = {"eur10": 1486, "eur5": 3518, "eur100": 5560}
A_EXPECT = struct.pack("<3f", 0.921875, 0.8445, 0.4993)  # approximate; compared with tolerance below
LABEL = {"eur5": "EUR 5  ", "eur10": "EUR 10 ", "eur100": "EUR 100"}

def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def lin_to_srgb(x):
    x = max(0.0, min(1.0, x))
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
def parse_hex(s):
    s = s.strip().lstrip("#")
    if len(s) != 6:
        sys.exit(f'"{s}" is not a 6-digit hex color like #868A90')
    try:
        return [int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    except ValueError:
        sys.exit(f'"{s}" is not a valid hex color')
def find_file(arg):
    if arg:
        return arg
    for d in DEFAULT_DIRS:
        p = os.path.join(d, NAME)
        if os.path.isfile(p):
            return p
    sys.exit(f"Could not find {NAME}. Use --file \"full\\path\\to\\{NAME}\"")
def check(data, key):
    o = OFFSETS[key]
    a = struct.unpack_from("<3f", data, o - 49)
    ref = struct.unpack("<3f", A_EXPECT)
    if len(data) < o + 12 or any(abs(x - y) > 2e-3 for x, y in zip(a, ref)):
        sys.exit("This does not look like the v1.2 add-on file (safety check failed) - nothing was changed.")
def read_color(data, key):
    return struct.unpack_from("<3f", data, OFFSETS[key])
def to_hex(rgb):
    return "#%02X%02X%02X" % tuple(round(lin_to_srgb(x) * 255) for x in rgb)

def main():
    ap = argparse.ArgumentParser(description="Tune EUR 5 / 10 / 100 strap colors.")
    ap.add_argument("--file", help=f"path to {NAME} (auto-detected if omitted)")
    for k in OFFSETS:
        ap.add_argument(f"--{k}", metavar="HEX", help=f"new {LABEL[k].strip()} strap color, e.g. #868A90")
    ap.add_argument("--show", action="store_true", help="print current colors and exit")
    ap.add_argument("--restore", action="store_true", help="restore the .bak backup")
    args = ap.parse_args()
    path = find_file(args.file)
    bak = path + ".bak"
    if args.restore:
        if not os.path.isfile(bak):
            sys.exit("No .bak backup found.")
        shutil.copyfile(bak, path); print("Restored", path); return
    data = bytearray(open(path, "rb").read())
    for k in OFFSETS:
        check(data, k)
    changes = {k: getattr(args, k) for k in OFFSETS if getattr(args, k)}
    if args.show or not changes:
        print("File:", path)
        for k in OFFSETS:
            print(f"  {LABEL[k]} strap = {to_hex(read_color(data, k))}")
        if not changes:
            print("\nPass e.g. --eur5 \"#868A90\" to change a color. (See --help.)"); return
    if not os.path.isfile(bak):
        shutil.copyfile(path, bak); print("Backup written:", bak)
    for k, h in changes.items():
        rgb = [srgb_to_lin(c) for c in parse_hex(h)]
        before = to_hex(read_color(data, k))
        struct.pack_into("<3f", data, OFFSETS[k], *rgb)
        print(f"  {LABEL[k]} strap {before} -> {to_hex(rgb)}")
    open(path, "wb").write(bytes(data))
    print("Saved. Restart the game to see the new color(s).")

if __name__ == "__main__":
    main()
