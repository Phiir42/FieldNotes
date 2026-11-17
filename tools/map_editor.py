"""A map editor in the browser: drag where each area reaches and where each
boss stands on a dungeon's sheet, and save it straight into its definition.

    python tools/map_editor.py [slug]          (opens http://127.0.0.1:8765/)

Each area is the part of the sheet nearest one of its seed points, so its
boundaries move with the seeds: click to add a seed to the chosen area, drag a
seed to move it, right-click a seed to remove it. Pick a boss and click (or
drag its mark) to say where it stands. Save writes tools/defs/<slug>.py;
"Build and install" then rebuilds FieldNotes/Maps.lua and its textures and
copies the addon into the game's AddOns folder.
"""
import ast, glob, http.server, importlib.util, json, os, re, shutil, subprocess, sys, threading, urllib.parse, webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFS = os.path.join(ROOT, "tools", "defs")
ADDONS = r"C:\Program Files (x86)\World of Warcraft\_forever_\Interface\AddOns\FieldNotes"
PORT = 8765
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_editor.html")


def def_path(slug):
    return os.path.join(DEFS, slug.replace("-", "_") + ".py")


def load_def(slug):
    spec = importlib.util.spec_from_file_location("mapdef", def_path(slug))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MAP


def slugs():
    out = []
    for path in sorted(glob.glob(os.path.join(DEFS, "*.py"))):
        try:
            spec = importlib.util.spec_from_file_location("mapdef", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            out.append(module.MAP["slug"])
        except Exception:
            pass
    return out


def shipped_bosses(instance):
    """Where Maps.lua puts each boss now: [floor] = [(name, x, y)]."""
    text = open(os.path.join(ROOT, "FieldNotes", "Maps.lua"), encoding="utf-8").read()
    start = text.find("ns.Maps[%d] = {}" % instance)
    if start < 0:
        return {}
    end = text.find("\nns.Maps[", start + 10)
    block = text[start:end if end > 0 else len(text)]
    out = {}
    for m in re.finditer(r"floor\.bosses = \{(.*?)\}\n(?:\t[^\n]*\n)*?\tns\.Maps\[\d+\]\[(\d+)\]", block, re.S):
        out[int(m.group(2))] = [(n, int(x), int(y)) for n, x, y in
                                re.findall(r'name = "((?:[^"\\]|\\.)*)", x = (\d+), y = (\d+)', m.group(1))]
    return out


def image_of(floor):
    if "art" in floor:
        return "tools/art/%s.png" % floor["art"]
    return "refs/%s.png" % floor["ref"]


def map_info(slug):
    MAP = load_def(slug)
    pins = MAP.get("bosses", {})
    now = shipped_bosses(MAP["instance"])
    floors = []
    for f, floor in enumerate(MAP["floors"], 1):
        bosses = [{"name": n, "x": x, "y": y, "pinned": isinstance(pins.get(n), tuple)} for n, x, y in now.get(f, [])]
        for n, pin in pins.items():  # pinned on this sheet but not in Maps.lua yet
            if isinstance(pin, tuple) and pin[0] == f and not any(b["name"] == n for b in bosses):
                bosses.append({"name": n, "x": pin[1], "y": pin[2], "pinned": True})
        floors.append({
            "image": image_of(floor),
            "start": [list(p) for p in floor.get("start", [])],
            "areas": {name: [list(p) for p in pts] for name, pts in floor["areas"].items()},
            "aliases": floor.get("aliases", {}),
            "bosses": bosses,
        })
    return {"slug": slug, "instance": MAP["instance"], "floors": floors}


def seeds(pts):
    return "[%s]" % ", ".join("(%d, %d)" % (int(x), int(y)) for x, y in pts)


def patched(text, data):
    """The definition's source with the edited values written over the old
    ones in place, so its layout and comments stay as they are."""
    text = text.lstrip("﻿")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    # ast counts columns in bytes of UTF-8: positions are worked out, and the
    # text spliced, in bytes
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))

    def at(node, end=False):
        return starts[(node.end_lineno if end else node.lineno) - 1] + (node.end_col_offset if end else node.col_offset)

    edits = []  # (start, end, new text)

    def entries(d):
        return {k.value: v for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant)}

    def indent_of(node):
        line = lines[node.lineno - 1]
        return line[:len(line) - len(line.lstrip())]

    MAP = next(n.value for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == "MAP")
    top = entries(MAP)
    # A definition may add seeds in code after its literal (Blackrock Spire
    # spreads some over bare ground): those are left out of what is written,
    # or the code would add them a second time.
    run = {}
    exec(compile(text, "<definition>", "exec"), run)
    for f, (floor, edit) in enumerate(zip(top["floors"].elts, data["floors"])):
        made = run["MAP"]["floors"][f]["areas"]
        for name, node in entries(entries(floor)["areas"]).items():
            try:
                written = [tuple(p) for p in ast.literal_eval(node)]
            except ValueError:
                continue
            extra = {tuple(p) for p in made.get(name, []) if tuple(p) not in written}
            if name in edit["areas"]:
                edit["areas"][name] = [p for p in edit["areas"][name] if tuple(p) not in extra]
    for floor, edit in zip(top["floors"].elts, data["floors"]):
        fields = entries(floor)
        if "start" in fields:
            node = fields["start"]
            edits.append((at(node), at(node, True), seeds(edit["start"])))
        elif edit["start"]:
            first = floor.keys[0]
            edits.append((at(first), at(first), '"start": %s,\n%s' % (seeds(edit["start"]), indent_of(first))))
        areas = fields["areas"]
        old = entries(areas)
        if set(old) == set(edit["areas"]):
            for name, node in old.items():
                edits.append((at(node), at(node, True), seeds(edit["areas"][name])))
        else:  # areas named anew: the whole block is written again
            pad = indent_of(areas.keys[0]) if areas.keys else "    "
            body = "".join("%s%r: %s,\n" % (pad, n, seeds(p)) for n, p in edit["areas"].items())
            edits.append((at(areas), at(areas, True), "{\n" + body + pad[:-4] + "}"))
    if data.get("moved"):
        moved = {n: "(%d, %d, %d)" % tuple(int(v) for v in pin) for n, pin in data["moved"].items()}
        if "bosses" in top:
            pins = top["bosses"]
            old = entries(pins)
            for name, node in old.items():
                if name in moved:
                    edits.append((at(node), at(node, True), moved.pop(name)))
            if moved:
                last = pins.values[-1] if pins.values else None
                pad = indent_of(pins.keys[-1]) if pins.keys else "        "
                add = "".join(",\n%s%r: %s" % (pad, n, v) for n, v in moved.items())
                if last is not None:
                    edits.append((at(last, True), at(last, True), add))
                else:
                    edits.append((at(pins), at(pins, True), "{" + add.lstrip(",\n").strip() + "}"))
        else:
            key = MAP.keys[list(top).index("instance")]
            value = MAP.values[list(top).index("instance")]
            pad = indent_of(key)
            body = ", ".join("%r: %s" % (n, v) for n, v in moved.items())
            edits.append((at(value, True) + 1, at(value, True) + 1, "\n%s'bosses': {%s}," % (pad, body)))
    raw = text.encode("utf-8")
    for start, end, new in sorted(edits, reverse=True):
        raw = raw[:start] + new.encode("utf-8") + raw[end:]
    text = raw.decode("utf-8")
    ast.parse(text)  # still a definition
    return text


def save(data):
    slug = data["slug"]
    path = def_path(slug)
    text = patched(open(path, encoding="utf-8").read(), data)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return "Saved " + os.path.relpath(path, ROOT)


def build(slug):
    run = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_maps.py")], cwd=ROOT,
                         capture_output=True, text=True)
    lines = [l for l in (run.stdout + run.stderr).splitlines() if slug in l or "!!" in l or "Error" in l or "wrote" in l]
    if run.returncode != 0:
        return False, "Build failed:\n" + (run.stderr or run.stdout)[-1500:]
    try:
        shutil.copytree(os.path.join(ROOT, "FieldNotes"), ADDONS, dirs_exist_ok=True)
        lines.append("Installed: /reload in game to see it.")
    except OSError as e:
        lines.append("Built, but not installed: %s" % e)
    return True, "\n".join(lines)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, kind="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        try:
            if url.path == "/":
                self.send(200, open(PAGE, "rb").read(), "text/html; charset=utf-8")
            elif url.path == "/api/list":
                self.send(200, json.dumps({"slugs": slugs(), "first": self.server.first}))
            elif url.path == "/api/map":
                self.send(200, json.dumps(map_info(q["slug"][0])))
            elif url.path == "/img":
                rel = q["path"][0]
                full = os.path.normpath(os.path.join(ROOT, rel))
                if not full.startswith(ROOT) or not full.endswith(".png"):
                    return self.send(403, "{}")
                self.send(200, open(full, "rb").read(), "image/png")
            else:
                self.send(404, "{}")
        except Exception as e:
            self.send(500, json.dumps({"error": str(e)}))

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path == "/api/save":
                self.send(200, json.dumps({"ok": True, "message": save(body)}))
            elif self.path == "/api/build":
                ok, message = build(body["slug"])
                self.send(200, json.dumps({"ok": ok, "message": message}))
            else:
                self.send(404, "{}")
        except Exception as e:
            self.send(500, json.dumps({"ok": False, "message": str(e)}))


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.first = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    url = "http://127.0.0.1:%d/" % PORT
    print("Map editor at", url, "(Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
