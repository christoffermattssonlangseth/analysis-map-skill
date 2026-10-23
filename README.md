# analysis-map

A Claude skill that turns a research project's analyses into an **interactive analysis map**: a radial mind map with
the project's central question in the middle, analysis goals on the inner ring, approach groups on the middle ring and
every run on the outer ring, coloured by status. Each run opens into full notes: why it was run, how it was done in
plain words, the traced pipeline, results explained, every figure with a legend, caveats, and the code and files behind it.

Built from one real project (111 runs, 421 figures) and generalised. See `examples/minimal/` for a three-run toy project.

## Install

Clone this repo and link it into your Claude skills folder:

```bash
git clone <this repo> ~/work/analysis-map-skill
ln -s ~/work/analysis-map-skill ~/.claude/skills/analysis-map
```

Then ask Claude Code something like "make an analysis map of this project" or "refresh the analysis map with the new runs".

## What a project needs

- A **run catalogue** in markdown (`### N. Title` entries with Rationale / Technical approach / Results / Caveats).
  If the project has none, the skill builds one with agents from the code, notebooks and outputs.
- A **data folder** (e.g. `docs/analysis-map/`) holding `map.config.json`, `runs_table.csv`, `goals.json` and, once
  written, `plain_language.json`, `legends.json`, `fig_fixes.json`. These are versioned, so rebuilds are incremental.

Formats: `references/inputs.md`. Agent briefs for the written parts: `references/briefs.md`.
Lessons from the first build: `references/gotchas.md`.

## Build by hand

```bash
python scripts/build_notes.py --config path/to/map.config.json   # notes.json + to-do lists for missing text
python scripts/build_page.py  --config path/to/map.config.json   # map.html, standalone/ folder and a zip
```

Requirements: Python 3.9+ with `pillow` and `pandas`; `node` (optional, checks the page script parses). The page loads
D3 7.8.5 and marked 4.3.0 from cdnjs and DM Sans from Google Fonts.

## Try the example

```bash
python scripts/build_notes.py --config examples/minimal/docs/analysis-map/map.config.json
python scripts/build_page.py  --config examples/minimal/docs/analysis-map/map.config.json
open examples/minimal/build/standalone/index.html
```
