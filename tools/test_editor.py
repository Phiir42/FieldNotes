"""Checks that the map editor (tools/map_editor.py) saves a definition without
harm: unchanged, every definition comes back with the same values and all
its comments; an area's seeds and a boss's pin, edited, come back as edited.

    python tools/test_editor.py
"""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map_editor as me

def run(text):
    g = {}
    exec(text, g)
    return g["MAP"]

def comments(text):
    return [l.strip() for l in text.splitlines() if l.strip().startswith("#")]

bad = 0
for path in sorted(glob.glob(os.path.join(me.DEFS, "*.py"))):
    text = open(path, encoding="utf-8-sig").read()
    MAP = run(text)
    data = {"slug": MAP["slug"], "floors": [{"start": [list(p) for p in f.get("start", [])],
             "areas": {n: [list(p) for p in pts] for n, pts in f["areas"].items()}} for f in MAP["floors"]]}
    new = me.patched(text, data)
    if run(new) != MAP or comments(new) != comments(text):
        print("round trip changed", os.path.basename(path)); bad += 1
    # a moved boss: replaced, appended, or a new pins block
    data["moved"] = {"Zz Test": [1, 10, 20]}
    first = next(iter(MAP.get("bosses", {})), None)
    if first and isinstance(MAP["bosses"][first], tuple):
        data["moved"][first] = [1, 11, 22]
    got = run(me.patched(text, data))
    want = dict(MAP.get("bosses", {})); want.update({k: tuple(v) for k, v in data["moved"].items()})
    if got.get("bosses") != want or {k: v for k, v in got.items() if k != "bosses"} != {k: v for k, v in MAP.items() if k != "bosses"}:
        print("pins wrong", os.path.basename(path), got.get("bosses")); bad += 1
    # one seed moved and one area's seeds changed
    data.pop("moved")
    f0 = data["floors"][0]
    if f0["areas"]:
        n = next(iter(f0["areas"]))
        f0["areas"][n] = f0["areas"][n][:1] + [[1, 2]]
        got = run(me.patched(text, data))
        if [list(p) for p in got["floors"][0]["areas"][n]][:len(f0["areas"][n])] != f0["areas"][n]:
            print("area edit lost", os.path.basename(path)); bad += 1
print("%d definitions saved by the editor, %d problems" % (len(glob.glob(os.path.join(me.DEFS, "*.py"))), bad))
sys.exit(1 if bad else 0)
