# Input formats

All project-specific files live in the project's data folder (`data_dir` in the config), which is versioned.
The build folder (`build_dir`) is regenerated and should be gitignored.

## map.config.json
```json
{
  "project": "ProjectName",
  "question": "Short central question shown as the page title?",
  "question_long": "Longer version for the overview card (optional)",
  "intro": "One or two sentences on the data and how claims were tested.",
  "centre_label": "ABC",
  "repo_root": "../..",
  "catalogue": "docs/run-catalogue.md",
  "catalogue_stop_heading": "\n## Summary",
  "registry": "docs/pipeline-registry.csv",
  "notebooks_glob": "notebooks/*.ipynb",
  "figure_dirs": ["docs/figures"],
  "data_dir": "docs/analysis-map",
  "build_dir": "runs/analysis_map_build",
  "statuses": null
}
```
Paths are relative to `repo_root`, which is relative to the config file. `catalogue_stop_heading` cuts off any summary
that follows the entries. `registry` may be omitted. `centre_label` is 2-6 characters (it sits inside the centre circle).
`statuses` optionally replaces the default status vocabulary: a list of `[name, colour]` pairs, colour as hex.

## Run catalogue (markdown)
One entry per run, numbered once and never renumbered (other entries cite `§N`, which become links):
```markdown
### 12. One-sentence finding as the title
*Notebook:* `notebooks/04_x.ipynb` (§3–5) · *Code:* `analysis/x.py` · *Results:* `runs/x/` · *Figure:* `docs/figures/x/a.png`

**Rationale.** Why the run was done; what question or earlier result prompted it.

**Technical approach.** Data, unit of analysis, preprocessing, model or statistic, folds, null/controls.

**Results.** Numbers, tables.

**Reading.** What it means. (optional)

**Caveats.** Limits.

**Next.** (optional)
```
- The header line is how figures are found: notebooks (with optional `(§a–b)` hints naming the notebook's own `## N.`
  parts that belong to this run), result folders and figure files named in backticks.
- Notebooks shared by several runs are split by their `## N. Heading` markdown headings; parts go to the run named in
  the hint, else the run whose entry best matches the heading. Notebooks no header names are attached to runs they cite
  as `§N`.
- Corrections are added to the entry as dated notes (e.g. `**Corrected 2026-10-22:** …`) rather than rewriting it.

## runs_table.csv
Columns: `section, short_title, group, method, unit, validation, data, key_result, status`.
- `short_title` ≤ 12 words; `method` ≤ 12; `validation` ≤ 10; `key_result` ≤ 28 with the headline number.
- `unit` = unit of analysis/inference (animal, section, cell (AUC per animal), donor, gene × cell type, …).
- `group` = the approach group (10-15 across a project); every group must appear under a goal in goals.json.
- Default `status` vocabulary (exact strings): `Supported`, `Partly supported`, `Not supported`,
  `Method negative (simple baseline wins)`, `Declared prediction failed`, `Correction/audit`, `Infrastructure`.

## goals.json
```json
[
  {"id": "g1", "label": "When: does X record Y?", "question": "Full question?",
   "answer": "One paragraph: the answer with its key numbers.",
   "groups": ["Approach group A", "Approach group B"], "color": "#e7a9cf"}
]
```
Order = clockwise order on the map. `color` is optional (a palette is used otherwise). Keep labels short (≤ 40 chars).

## pipeline-registry.csv (optional)
One row per section. Columns used by the map: `input_data, preprocessing, inputs, target, model, split, evaluation,
scripts, outputs, notebook, leak_flag (none/possible/yes), notes, trace_confidence (high/medium/low)`.

## plain_language.json
`{"12": {"how": "markdown, 120-220 words", "results": "markdown, 120-250 words"}, …}`

## legends.json
`{"figs/<16-hex>.jpg": "**Title sentence.** 2-4 sentences.", …}` - keys are the build's figure names, which are a
hash of the source image bytes, so legends survive rebuilds as long as the image itself is unchanged.

## fig_fixes.json
`{"move": {"figs/<hash>.jpg": [from_run, to_run]}, "drop": ["figs/<hash>.jpg"]}`

## groups.json (optional)
One expandable "Summary and key figures" panel per approach group (the middle ring), shown on the group's card:
`{"<group name>": {"summary": "<90-150 words, markdown>", "figs": ["figs/<hash>.jpg", ...]}}`. Group names must match
`goals.json`; figures are 2-4 keys already used by that group's runs (so nothing extra is uploaded), most important
first. Thumbnails open in the lightbox with their run legend. Write it with the "Group summaries" brief.
