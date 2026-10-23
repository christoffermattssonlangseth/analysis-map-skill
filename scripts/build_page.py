"""Assemble the analysis map page from a project's map.config.json.

Inputs: data_dir/goals.json, data_dir/runs_table.csv, build_dir/notes.json (from build_notes.py), assets/template.html.
Outputs in build_dir:
  map.html           the page body for publishing as a claude.ai Artifact (the publisher adds the document skeleton);
                     publish it with build_dir as `root` and the figures as `files`
  publish_batches.json  figure paths split into batches of at most 250 (one Artifact publish accepts 255 files)
  standalone/        index.html (full document) + figs/, opens from disk; zipped to <project>-analysis-map.zip
Checks: every run in runs_table has a goal (its group is listed under a goal), and the script in the page parses (node).

    python build_page.py --config path/to/map.config.json [--test-open N]   # N: also write standalone/_test.html opening run N
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_notes import load_config  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["section", "short_title", "group", "method", "unit", "validation", "data", "key_result", "status"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--test-open", type=int, default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    data, build = cfg["data_dir_abs"], cfg["build_dir_abs"]
    goals = json.load(open(os.path.join(data, "goals.json")))
    runs = pd.read_csv(os.path.join(data, "runs_table.csv"))
    missing = [c for c in FIELDS if c not in runs.columns]
    if missing:
        sys.exit(f"runs_table.csv lacks columns {missing}")
    grouped = {g for x in goals for g in x["groups"]}
    orphans = sorted(set(runs.group) - grouped)
    if orphans:
        sys.exit(f"groups with no goal in goals.json: {orphans}")
    notes = json.load(open(os.path.join(build, "notes.json")))
    no_notes = [int(s) for s in runs.section if str(int(s)) not in notes]
    if no_notes:
        print(f"warning: runs in runs_table with no catalogue entry: {no_notes}")
    rows = [{k: (int(v) if k == "section" else str(v)) for k, v in r.items() if k in FIELDS} for r in runs.to_dict("records")]
    conf = {k: cfg.get(k) for k in ("project", "question", "question_long", "intro", "centre_label", "catalogue", "statuses") if cfg.get(k) is not None}
    esc = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    t = open(os.path.join(HERE, "..", "assets", "template.html")).read()
    page = (t.replace("__PAGE_TITLE__", cfg.get("page_title", cfg["project"] + " Analysis Map"))
             .replace("const DATA = __DATA__;", "const DATA = " + esc({"goals": goals, "runs": rows}) + ";")
             .replace("const NOTES = __NOTES__;", "const NOTES = " + esc(notes) + ";")
             .replace("const CONFIG = __CONFIG__;", "const CONFIG = " + esc(conf) + ";"))
    open(os.path.join(build, "map.html"), "w").write(page)
    js = page.split("<script>")[-1].split("</script>")[0]
    open(os.path.join(build, "_check.js"), "w").write(js)
    if shutil.which("node"):
        r = subprocess.run(["node", "--check", os.path.join(build, "_check.js")], capture_output=True, text=True)
        if r.returncode:
            sys.exit("page script does not parse:\n" + r.stderr)
    used = sorted({f["src"] for v in notes.values() for f in v["figs"]})
    json.dump([used[i:i + 250] for i in range(0, len(used), 250)], open(os.path.join(build, "publish_batches.json"), "w"))
    # standalone copy: full document + only the figures in use
    te = page.index("</title>") + 8; se = page.index("</style>") + 8
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + page[:te] + page[te:se].replace('<meta name="claude:viewport-fit-sides" content="cover">', '')
            + '\n<style>html,body{margin:0}</style>\n</head>\n<body>\n' + page[se:] + '\n</body>\n</html>\n')
    sa = os.path.join(build, "standalone")
    if os.path.isdir(sa):
        shutil.rmtree(sa)
    os.makedirs(os.path.join(sa, "figs"))
    for u in used:
        shutil.copy(os.path.join(build, u), os.path.join(sa, u))
    open(os.path.join(sa, "index.html"), "w").write(html)
    if a.test_open is not None:
        hook = "refresh(); card(h); flyTo(h.descendants(), 40, 0);"
        open(os.path.join(sa, "_test.html"), "w").write(html.replace(hook, hook + f" openNotes({a.test_open});"))
    zname = cfg["project"].replace(" ", "-") + "-analysis-map"
    shutil.make_archive(os.path.join(build, zname), "zip", build, "standalone")
    print(f"page {len(page) // 1000} KB | {len(rows)} runs, {len(goals)} goals | {len(used)} figures in "
          f"{-(-len(used) // 250)} publish batch(es) | zip {os.path.join(build, zname)}.zip")


if __name__ == "__main__":
    main()
