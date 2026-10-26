---
name: analysis-map
description: Build an interactive, immersive "analysis map" of a research project - a radial mind map of every analysis run, grouped by the question it answers, where each run opens into full notes (why it was run, how it was done in plain words, the traced pipeline, results explained, every figure with a legend, caveats, code and files). Use this whenever someone wants an overview, map, mind map, atlas or browsable summary of all the analyses/experiments/runs in a project, wants to show collaborators "everything we have done and how", wants per-run figures with legends in one place, or wants to refresh or extend an existing analysis map after new runs - even if they don't say "mind map". Works on any project that has (or can be given) a run catalogue in markdown.
---

# Analysis map

An analysis map turns a project's pile of runs into one page a collaborator can explore in minutes: the project's
central question in the middle, the analysis goals on the inner ring, approach groups on the middle ring, and every run
as a point on the outer ring coloured by its status. Clicking flies in; double-clicking a run opens its notes; a status
filter, search, guided tour and figure lightbox come built in.

The build is a pipeline of small, persistent steps. Expensive hand-written parts (the runs table, goals, plain-language
notes, figure legends) are stored in the project's **data folder** and reused on every rebuild, so a refresh after new
runs only writes what is new. Read `references/inputs.md` for the exact file formats before writing any input.

## The pipeline

```
run catalogue (markdown) ──┐
pipeline registry (opt.) ──┤                       ┌─> notes.json ─┐
notebooks + figure files ──┼─> build_notes.py ─────┤               ├─> build_page.py ─> map.html (Artifact)
data folder:               │                       └─> todo lists  │                    standalone/ + zip
  runs_table.csv, goals.json, plain_language.json, legends.json, fig_fixes.json,
  groups.json (optional group summaries) ──────────────────────────────────────────────┘
```

### 0. Set up the project config
Create `<data_dir>/map.config.json` (template in `references/inputs.md`): project name, the central question, an intro
line, a short centre label, paths to the catalogue, optional registry, notebooks glob, figure folders, the data folder
(versioned, e.g. `docs/analysis-map/`) and a build folder (gitignored, e.g. `runs/analysis_map_build/`). Ask the user
for the central question and intro; they set the tone of the whole map.

### 1. Make sure there is a run catalogue
The map is only as good as the catalogue. If the project has one in the expected shape (`### N. Title` entries with
`**Rationale.** / **Technical approach.** / **Results.** / **Caveats.**` and a `*Notebook:* … · *Code:* … · *Results:* …`
header line), use it. If it has run documentation in another shape, adapt it or write a thin converter. If it has none,
build one with agents using the "Catalogue" brief in `references/briefs.md` - this is the biggest job and worth doing
well, because every later step reads it. Never invent results: entries must come from code, outputs and existing docs.

### 2. Runs table and goals
- `runs_table.csv`: one row per run with section, short_title, group, method, unit, validation, data, key_result, status.
  If missing (or new runs were added), extract it with the "Runs table" brief. `status` uses the vocabulary in
  `references/inputs.md` unless the config overrides it.
- `goals.json`: 5-10 analysis goals, each a question with a one-paragraph answer and the approach groups under it.
  Draft them yourself from the runs table (group the approach groups by the question they serve, not by method), then
  show the user and adjust - the goals are the map's argument, so the user should own them.

### 3. Optional: pipeline registry
A CSV tracing each run through data → preprocessing → inputs → target → model → split → evaluation → result, read from
the code ("Registry" brief). It powers the "Traced pipeline" table in each run's notes and doubles as an audit (it found
leaked gene selections and wrong split descriptions in its first project). Skip it if the user only wants an overview.

### 4. Build notes and see what is missing
```
python <skill>/scripts/build_notes.py --config <data_dir>/map.config.json
```
This parses the catalogue, extracts figures from notebooks (grouped by `## N.` parts) and from folders the entries name,
attaches registry rows, plain notes and legends, applies `fig_fixes.json`, drops near-duplicate images, and writes
`todo_plain.json` and `todo_legends.json` in the build folder.

### 5. Write what is missing, with agents in parallel
- Plain-language notes for runs in `todo_plain.json` ("Plain language" brief): ~30 runs per agent.
- Legends for figures in `todo_legends.json` ("Legends" brief): split into ~90 figures per agent. Each agent must open
  and look at every image. Ask agents to report figures that belong to a different run; record those as `move` entries
  (and unreadable ones as `drop`) in `fig_fixes.json`.
- Give every agent its **own working folder** and its own output file; agents sharing helper files in one scratch folder
  overwrote each other's output in the first build.
- Merge the outputs into `plain_language.json` / `legends.json` in the data folder (keys: run number as a string;
  figure path `figs/<hash>.jpg`). Re-run step 4 until both to-do lists are empty.
Spot-check a few results against the catalogue before trusting a batch.
- Optional: group summary cards (`groups.json`, "Group summaries" brief): an expandable summary with 2-4 key figures on
  each approach-group card. Refresh a group's entry when its runs change.

### 6. Build the page and look at it
```
python <skill>/scripts/build_page.py --config <data_dir>/map.config.json --test-open <run number>
```
It validates the inputs (every group has a goal, the page script parses) and writes `map.html`, `publish_batches.json`,
`standalone/` and a zip. Render `standalone/index.html` and `standalone/_test.html` (headless Chrome:
`--headless=new --screenshot --virtual-time-budget=6000`) and look at both: overview and one run's notes.

### 7. Publish and share
- **claude.ai Artifact:** publish `map.html` with `root` = the build folder and the first batch of
  `publish_batches.json` as `files` (list form `[{"path": "figs/…jpg"}, …]`); publish again with the same file path for
  each further batch (one publish accepts at most 255 files). Republishing the same file path keeps the URL.
- **Outside claude.ai:** send the zip; the recipient unzips and opens `index.html` (needs internet only for the font and
  two CDN libraries). Institutional OneDrive/SharePoint links make outside people log in - email the zip or use a
  public link.
- Commit the data folder (not the build folder).

## Updating an existing map
New runs: add catalogue entries → add rows to `runs_table.csv` (and a goal/group if needed) → step 4 → write only the
to-do items → step 6 → republish (only new figures need uploading). A run whose entry changed materially should have
its plain notes rewritten: delete its key from `plain_language.json` and it reappears in `todo_plain.json`.

## Things that went wrong before (read before changing the template)
See `references/gotchas.md` - especially the D3 `.call(fn).text()` trap that silently erased every node, and why the
figures must be keyed by a hash of their source bytes.
