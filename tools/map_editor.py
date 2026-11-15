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
import glob, http.server, importlib.util, json, os, pprint, re, shutil, subprocess, sys, threading, urllib.parse, webbrowser

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
    for m in re.finditer(r"floor\.bosses = \{(.*?)\}\n\tns\.Maps\[\d+\]\[(\d+)\]", block, re.S):
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


def save(data):
    slug = data["slug"]
    path = def_path(slug)
    text = open(path, encoding="utf-8").read()
    head = text[:text.index("MAP = ")]
    MAP = load_def(slug)
    for floor, edit in zip(MAP["floors"], data["floors"]):
        if edit["start"]:
            floor["start"] = [tuple(p) for p in edit["start"]]
        else:
            floor.pop("start", None)
        floor["areas"] = {name: [tuple(p) for p in pts] for name, pts in edit["areas"].items()}
    if data.get("moved"):
        pins = dict(MAP.get("bosses", {}))
        for name, (f, x, y) in data["moved"].items():
            pins[name] = (int(f), int(x), int(y))
        MAP["bosses"] = pins
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(head + "MAP = " + pprint.pformat(MAP, width=110, sort_dicts=False) + "\n")
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
