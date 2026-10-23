"""Build notes.json for the analysis map, plus to-do lists for the agent-written parts.

Reads a project's map.config.json. For every run in the catalogue it collects:
  - the catalogue entry, split into reader sections (Rationale / Technical approach / Results / Reading / Caveats / Next)
  - the run's figures: images embedded in its notebook(s) and image files under the folders its entry names
  - its pipeline row from the registry CSV, if the project has one
  - plain-language notes and figure legends already written (data_dir/plain_language.json, data_dir/legends.json)
and applies data_dir/fig_fixes.json (figures moved between runs or dropped), then removes near-duplicate images within a run.

Writes to build_dir: notes.json, figs/*.jpg (web-sized), fig_manifest.json, todo_plain.json (runs without plain-language
notes) and todo_legends.json (figures without legends, with the context an agent needs to write one).

    python build_notes.py --config path/to/map.config.json
"""
from __future__ import annotations

import argparse
import base64
import collections
import glob
import hashlib
import io
import json
import os
import re

from PIL import Image

IMG = (".png", ".jpg", ".jpeg", ".gif", ".webp")
MAIN = {"Rationale": "why", "Technical approach": "how", "Results": "found", "Reading": "means", "Caveats": "caveats", "Next": "next"}
STOP = {"with", "from", "that", "only", "than", "does", "into", "this", "they", "what", "when", "where", "which"}
PIPE = ["input_data", "preprocessing", "inputs", "target", "model", "split", "evaluation", "scripts", "outputs", "notebook",
        "leak_flag", "notes", "trace_confidence"]


def load_config(path):
    cfg = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    root = os.path.abspath(os.path.join(base, cfg.get("repo_root", ".")))
    for k in ("catalogue", "registry", "data_dir", "build_dir"):
        if cfg.get(k):
            cfg[k + "_abs"] = cfg[k] if os.path.isabs(cfg[k]) else os.path.join(root, cfg[k])
    cfg["root"] = root
    return cfg


def parse_catalogue(path, stop_heading):
    s = open(path).read()
    if stop_heading and stop_heading in s:
        s = s.split(stop_heading)[0]
    entries = {}
    for p in re.split(r"\n(?=### \d+\. )", s):
        m = re.match(r"### (\d+)\. (.*)", p)
        if m:
            entries[int(m.group(1))] = p.strip()
    return entries


def split_sections(e):
    out = collections.OrderedDict(); cur = "intro"; out[cur] = []
    for line in e.splitlines()[1:]:
        m = re.match(r"^\*\*([A-Z][A-Za-z ,()/-]{2,40}?)[.:]\*\*\s*(.*)", line)
        if m:
            lab = m.group(1); key = next((v for k, v in MAIN.items() if lab.startswith(k)), None)
            if key:
                cur = key; out.setdefault(cur, []); line = (f"*{lab}.* " if lab not in MAIN else "") + m.group(2)
        out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items() if "\n".join(v).strip()}


class FigStore:
    """Web-sized JPEG copies, named by a hash of the source bytes so legends stay attached across rebuilds."""

    def __init__(self, build):
        self.build = build; self.seen = {}
        os.makedirs(os.path.join(build, "figs"), exist_ok=True)

    def save(self, b):
        h = hashlib.sha1(b).hexdigest()[:16]
        if h in self.seen:
            return self.seen[h]
        name = f"figs/{h}.jpg"
        if not os.path.exists(os.path.join(self.build, name)):
            im = Image.open(io.BytesIO(b))
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1]); im = bg
            else:
                im = im.convert("RGB")
            if im.width > 1400:
                im = im.resize((1400, int(im.height * 1400 / im.width)), Image.LANCZOS)
            im.save(os.path.join(self.build, name), "JPEG", quality=80, optimize=True, progressive=True)
        self.seen[h] = name
        return name


def nb_parts(nb):
    """Images in a notebook grouped by its '## N. Heading' parts, each with the cell that drew it and the text around it."""
    d = json.load(open(nb)); cells = d["cells"]; cur = (0, "Introduction")
    out = collections.OrderedDict(); out[cur] = []

    def md_near(i, step):
        j = i + step
        while 0 <= j < len(cells):
            if cells[j]["cell_type"] == "markdown":
                return "".join(cells[j]["source"])[:1500]
            j += step
        return ""
    for ci, c in enumerate(cells):
        if c["cell_type"] == "markdown":
            for line in "".join(c["source"]).splitlines():
                m = re.match(r"##\s+(\d+)[.·\s]+\s*(.*)", line)
                if m:
                    cur = (int(m.group(1)), m.group(2).strip()); out.setdefault(cur, [])
                elif line.startswith("## "):
                    cur = (99, line[3:].strip()); out.setdefault(cur, [])
        for o in c.get("outputs", []):
            dd = o.get("data", {})
            for k in ("image/png", "image/jpeg"):
                if k in dd:
                    b = dd[k]; b = "".join(b) if isinstance(b, list) else b
                    out[cur].append((base64.b64decode(b), {"notebook": nb, "cell": ci, "code": "".join(c.get("source", ""))[:2500],
                                                           "md_before": md_near(ci, -1), "md_after": md_near(ci, 1)}))
                    break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    cfg = load_config(a.config)
    root, data, build = cfg["root"], cfg["data_dir_abs"], cfg["build_dir_abs"]
    os.makedirs(build, exist_ok=True)
    os.chdir(root)
    entries = parse_catalogue(cfg["catalogue_abs"], cfg.get("catalogue_stop_heading"))
    store = FigStore(build)
    hdr = {k: next((l for l in e.splitlines() if re.match(r"\*(Notebook|Code|Results)", l)), "") for k, e in entries.items()}
    tok = lambda t: {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP}

    # which runs use which notebook (with optional part hints like "(§1–7)" after the path)
    users = collections.defaultdict(list)
    for sec, h in hdr.items():
        for m in re.finditer(r"`([^`]+\.ipynb)`\s*(\(§[^)]*\))?", h):
            hint = None
            if m.group(2):
                nums = []
                for x, y in re.findall(r"(\d+)\s*(?:[–-]\s*(\d+))?", m.group(2)):
                    nums += list(range(int(x), int(y) + 1)) if y else [int(x)]
                hint = set(nums)
            if os.path.exists(m.group(1)):
                users[m.group(1)].append((sec, hint))
    # notebooks no header names: attach to the runs they mention that have no notebook of their own
    named = {sec for us in users.values() for sec, _ in us}
    for nb in sorted(glob.glob(cfg.get("notebooks_glob", "notebooks/*.ipynb"))):
        if nb in users:
            continue
        d = json.load(open(nb)); t = "".join("".join(c["source"]) for c in d["cells"] if c["cell_type"] == "markdown")
        for sec in sorted({int(x) for x in re.findall(r"§\s?(\d{1,3})", t)} & set(entries) - named):
            users[nb].append((sec, None))

    figs = collections.defaultdict(list); CTX = {}
    for nb, us in users.items():
        short = os.path.basename(nb).split("_")[0]
        for (num, head), imgs in nb_parts(nb).items():
            if not imgs:
                continue
            owners = [sec for sec, hint in us if hint and num in hint]
            if not owners:
                ment = [int(x) for x in re.findall(r"§\s?(\d{1,3})", head)]
                ids = [u[0] for u in us]; free = [sec for sec, hint in us if not hint]
                if any(m in ids for m in ment):
                    owners = [m for m in ment if m in ids]
                elif len(us) == 1:
                    owners = [us[0][0]]
                elif free:
                    sc = {sec: len(tok(head) & tok(entries[sec][:800])) for sec in free}
                    if max(sc.values()) > 0:
                        owners = [max(sc, key=sc.get)]
            cap = f"Notebook {short} · " + (f"part {num}: {head}" if 0 < num < 99 else head)
            for sec in owners:
                for b, ctx in imgs:
                    src = store.save(b); figs[sec].append({"src": src, "caption": cap})
                    CTX.setdefault(src, {**ctx, "runs": set()})["runs"].add(sec)
    fig_dirs = cfg.get("figure_dirs", ["docs/figures"])
    for sec, e in entries.items():
        files = []
        refs = re.findall(r"`([^`]+)`", hdr[sec]) + re.findall(r"`([^`]+\.(?:png|jpg|jpeg))`", e)
        for r in refs:
            r = r.rstrip("/")
            if r.lower().endswith(IMG) and os.path.isfile(r):
                files.append(r)
            elif os.path.isdir(r):
                files += sorted(f for f in glob.glob(r + "/**/*", recursive=True) if f.lower().endswith(IMG) and "/cache" not in f)
            leaf = os.path.basename(r)
            for fd in fig_dirs:
                if leaf and os.path.isdir(os.path.join(fd, leaf)):
                    files += sorted(f for f in glob.glob(os.path.join(fd, leaf, "*")) if f.lower().endswith(IMG))
        for f in dict.fromkeys(files):
            src = store.save(open(f, "rb").read()); figs[sec].append({"src": src, "caption": f})
            CTX.setdefault(src, {"file": f, "runs": set()})["runs"].add(sec)

    # fixes recorded while writing legends; then drop near-duplicates within a run
    fx_path = os.path.join(data, "fig_fixes.json")
    FIX = json.load(open(fx_path)) if os.path.exists(fx_path) else {"move": {}, "drop": []}
    for src, (frm, to) in FIX.get("move", {}).items():
        moved = [f for f in figs.get(frm, []) if f["src"] == src]
        figs[frm] = [f for f in figs.get(frm, []) if f["src"] != src]
        if moved and src not in [f["src"] for f in figs[to]]:
            figs[to].append(moved[0])
    for sec in figs:
        seen, keep = set(), []
        for f in figs[sec]:
            if f["src"] not in seen and f["src"] not in FIX.get("drop", []):
                keep.append(f); seen.add(f["src"])
        figs[sec] = keep
    HC = {}

    def ahash(p):
        im = Image.open(os.path.join(build, p)).convert("L").resize((24, 24), Image.LANCZOS); px = list(im.getdata()); mu = sum(px) / len(px)
        return [x > mu for x in px]
    ndup = 0
    for sec in figs:
        keep = []
        for f in figs[sec]:
            hsh = HC.setdefault(f["src"], ahash(f["src"]))
            if any(sum(x != y for x, y in zip(hsh, HC[k["src"]])) <= 20 for k in keep):
                ndup += 1; continue
            keep.append(f)
        figs[sec] = keep

    reg = {}
    if cfg.get("registry_abs") and os.path.exists(cfg["registry_abs"]):
        import pandas as pd
        r = pd.read_csv(cfg["registry_abs"])
        reg = {int(row["section"]): {k: ("" if k not in row or pd.isna(row[k]) else str(row[k])) for k in PIPE} for _, row in r.iterrows()}
    load = lambda n: json.load(open(os.path.join(data, n))) if os.path.exists(os.path.join(data, n)) else {}
    plain, legends = load("plain_language.json"), load("legends.json")

    notes = {}
    for sec, e in entries.items():
        first = e.splitlines()[0]
        title = first.split(". ", 1)[1] if ". " in first else first
        fl = [{**f, **({"legend": legends[f["src"]]} if f["src"] in legends else {})} for f in figs.get(sec, [])]
        notes[str(sec)] = {"title": title, "sections": split_sections(e), "figs": fl, "pipeline": reg.get(sec, {})}
        if str(sec) in plain:
            notes[str(sec)]["plain"] = plain[str(sec)]
    json.dump(notes, open(os.path.join(build, "notes.json"), "w"), ensure_ascii=False)

    used = sorted({f["src"] for v in notes.values() for f in v["figs"]})
    man = {s: {**{k: v for k, v in CTX[s].items() if k != "runs"}, "runs": sorted(CTX[s]["runs"])} for s in used}
    json.dump(man, open(os.path.join(build, "fig_manifest.json"), "w"), ensure_ascii=False)
    todo_plain = sorted((int(k) for k in notes if "plain" not in notes[k]))
    todo_leg = {s: man[s] for s in used if s not in legends}
    json.dump(todo_plain, open(os.path.join(build, "todo_plain.json"), "w"))
    json.dump(todo_leg, open(os.path.join(build, "todo_legends.json"), "w"), ensure_ascii=False)
    print(f"runs {len(notes)} | figures {len(used)} on {sum(1 for v in notes.values() if v['figs'])} runs | near-duplicates removed {ndup}")
    print(f"registry rows {len(reg)} | plain notes {len(notes) - len(todo_plain)} (to write: {len(todo_plain)}) | "
          f"legends {len(used) - len(todo_leg)} (to write: {len(todo_leg)})")


if __name__ == "__main__":
    main()
