"""Load the addon into real Lua 5.1 against a mock of the game client and play
a dungeon run through it (tools/test_run.lua). No game needed.

    pip install lupa
    python tools/test_addon.py [-v]
"""
import io
import os
import sys

try:
    from lupa import lua51 as lupa
except ImportError:
    sys.exit("needs lupa (pip install lupa)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(ROOT, "FieldNotes")


def read(path):
    return io.open(path, encoding="utf-8").read()


def main():
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    load = lua.eval("function(src, name) local f, err = loadstring(src, name) if not f then error(err) end return f end")
    mock = load(read(os.path.join(ROOT, "tools", "wowmock.lua")), "@wowmock.lua")()
    ns = lua.table()
    files = [l.strip() for l in read(os.path.join(ADDON, "FieldNotes.toc")).splitlines()
             if l.strip() and not l.startswith("#")]
    for name in files:
        load(read(os.path.join(ADDON, name)), "@" + name)("FieldNotes", ns)
    checks, fails, missing, chat = load(read(os.path.join(ROOT, "tools", "test_run.lua")), "@test_run.lua")(mock, ns)
    if "-v" in sys.argv:
        for line in chat.values():
            print("   ", line.encode("ascii", "replace").decode())
    # globals the addon looked for that the mock lacks: fine if the addon
    # guards for their absence, but worth a look when something new appears
    optional = {"GetSpellInfo", "GetSpellTexture", "GetSpellDescription", "ChatFrameUtil", "GameFontNormal",
                "QuestFont", "QuestTitleFont", "GameFontNormalLarge", "GameFontNormalSmall", "GameFontHighlight",
                "YES", "NO", "FieldNotesDB"}
    new = [k for k in missing.values() if k not in optional]
    if new:
        print("globals the mock does not have:", ", ".join(new))
    for f in fails.values():
        print("FAIL", f)
    print("%d checks, %d failed" % (checks, len(fails)))
    return 1 if len(fails) else 0


if __name__ == "__main__":
    sys.exit(main())
