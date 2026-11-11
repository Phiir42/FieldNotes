"""Build the release zip: dist/FieldNotes-<version>.zip, holding one folder,
FieldNotes/, ready to unzip into Interface/AddOns.

    python tools/package.py
"""
import io
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(ROOT, "FieldNotes")
EXTRA = ["README.md", "CHANGELOG.md", "LICENSE"]  # copied into the addon folder of the zip


def main():
    toc = io.open(os.path.join(ADDON, "FieldNotes.toc"), encoding="utf-8").read()
    version = re.search(r"^## Version: *(\S+)", toc, re.M).group(1)
    # every file the TOC names must be there, and every map texture Maps.lua names
    for name in [l.strip() for l in toc.splitlines() if l.strip() and not l.startswith("#")]:
        if not os.path.exists(os.path.join(ADDON, name)):
            sys.exit("missing file named in the TOC: " + name)
    maps = io.open(os.path.join(ADDON, "Maps.lua"), encoding="utf-8").read()
    have = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ADDON, "Maps"))}
    named = set(re.findall(r'DIR \.\. "([^"]+)"', maps))
    if named - have:
        sys.exit("map textures named but missing: " + ", ".join(sorted(named - have)[:10]))
    if have - named:
        print("note: %d map textures are not used by Maps.lua" % len(have - named))

    out = os.path.join(ROOT, "dist")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "FieldNotes-%s.zip" % version)
    n = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for folder, _, files in sorted(os.walk(ADDON)):
            for f in sorted(files):
                full = os.path.join(folder, f)
                z.write(full, "FieldNotes/" + os.path.relpath(full, ADDON).replace(os.sep, "/"))
                n += 1
        for f in EXTRA:
            z.write(os.path.join(ROOT, f), "FieldNotes/" + f)
            n += 1
    print("%s  (%d files, %.1f MB)" % (path, n, os.path.getsize(path) / 1e6))


if __name__ == "__main__":
    main()
