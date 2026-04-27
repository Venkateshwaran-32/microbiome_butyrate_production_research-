# Repository Reorganization Proposal

## Purpose

This note proposes a cleaner repository structure for expanding this project from:

- COBRApy single-species and community work
- MICOM baseline and age-bin work
- subject-level MICOM analysis

The goal is not to make the repository look "software-engineered" for its own sake. The goal is to make it:

- easier to navigate
- easier to rerun
- easier to extend without mixing outputs from different branches
- safer when new subject-level analyses produce many more intermediate and final files

## Short Answer

There is no single universal microbiome folder SOP that everyone follows.

What does exist across reproducible research and bioinformatics practice is a strong recurring pattern:

- separate data from code
- separate raw inputs from processed inputs
- separate scripts from outputs
- keep figures separate from tables
- keep run metadata and QC reports with the outputs they describe
- keep enough provenance so a result can be traced back to a script, input set, and parameter choice

That pattern is more important than any exact folder names.

## What Is Messy In The Current Repository

The current repository is still workable for a small project, but it will become harder to manage as subject-level MICOM grows.

Main issues:

- `Modelling_scripts/` mixes executable scripts, result CSVs, and build reports in the same folder.
- `Scripts/plotting_r/` has a trailing space in the folder name and several file names also contain extra spaces.
- `Suplementary_Data/` contains both original inputs and processed outputs.
- There is no clean separation between:
  - source data
  - derived data
  - analysis code
  - result tables
  - figures
  - run metadata
- Current numbering works for a small linear workflow, but it will get awkward once you add:
  - subject-level MICOM preparation
  - subject-level growth summaries
  - pathway summaries
  - provenance sub-analyses
  - sensitivity runs
- Environment folders are in the project root.
- A few names are inconsistent or hard to scan:
  - `Suplementary_Data` should be `supplementary_data`
  - `Medium_files` vs `Models` vs `Modelling_scripts`
  - mixed capitalization across folders
  - `04_micom_basline_comm_trial.py` looks like an ad hoc experiment file that should not sit beside official scripts

## Design Principles For The Next Structure

The next structure should follow these rules:

1. One place for raw inputs.
2. One place for processed inputs.
3. One place for executable analysis code.
4. One place for outputs.
5. One place for documentation and SOP notes.
6. One naming system across COBRApy, MICOM, and subject-level MICOM.
7. A result file should tell you:
   - method family
   - analysis level
   - content type
   - whether it is a table, report, or figure
8. Subject-level MICOM should be added as a new branch, not by dumping more files into the current script folder.

## Recommended Top-Level Layout

```text
microbiome_butyrate_production_research/
├── README.md
├── pyproject.toml                      <- or requirements/environment files
├── .gitignore
├── docs/
│   ├── sop/
│   ├── notes/
│   ├── references/
│   └── proposals/
├── data/
│   ├── raw/
│   │   ├── supplementary/
│   │   ├── media/
│   │   └── model_archives/
│   ├── external/
│   │   └── agora/
│   ├── interim/
│   │   ├── age_bin/
│   │   └── subject_level/
│   └── processed/
│       ├── cobrapy/
│       ├── micom/
│       │   ├── age_bin/
│       │   └── subject_level/
│       └── shared/
├── models/
│   ├── agora1_03/
│   └── agora2/
├── workflows/
│   ├── cobrapy/
│   ├── micom/
│   └── shared/
├── scripts/
│   ├── data_prep/
│   ├── cobrapy/
│   ├── micom/
│   ├── plotting/
│   └── qc/
├── results/
│   ├── tables/
│   │   ├── cobrapy/
│   │   ├── micom/
│   │   │   ├── baseline/
│   │   │   ├── age_bin/
│   │   │   └── subject_level/
│   │   └── comparisons/
│   ├── reports/
│   │   ├── build/
│   │   ├── qc/
│   │   └── run_logs/
│   └── figures/
│       ├── cobrapy/
│       ├── micom/
│       └── comparisons/
├── tests/
└── archive/
    └── exploratory/
```

## Why This Is Better

This structure fixes the scaling problem by separating objects by role instead of by historical accident.

Examples:

- A script lives in `scripts/` even if it produces five different outputs.
- A processed taxonomy input for subject-level MICOM lives in `data/processed/micom/subject_level/`.
- A build report never sits next to a Python script; it lives in `results/reports/build/`.
- A comparison figure between COBRApy and MICOM lives in `results/figures/comparisons/`.
- Old exploratory or trial files are kept in `archive/exploratory/` instead of sitting next to official analysis code.

## Recommended Folder Semantics

### `docs/`

Use this for human-readable project documentation.

Suggested subfolders:

- `docs/sop/`: official workflow rules
- `docs/notes/`: explanatory notes
- `docs/references/`: paper notes, PDFs, summaries
- `docs/proposals/`: planned future expansions

Current mapping:

- `MD/project_sop.md` -> `docs/sop/project_sop.md`
- `MD/micom_practices.md` -> `docs/sop/micom_practices.md`
- `PDF/` -> `docs/references/`

### `data/`

This should contain inputs and derived inputs, not final scientific results.

Recommended meanings:

- `data/raw/`: original files that should not be edited
- `data/external/`: downloaded third-party assets
- `data/interim/`: temporary or partially transformed files
- `data/processed/`: canonical analysis-ready inputs

Current mapping:

- `Suplementary_Data/Metadata_by_cohort.xlsx` -> `data/raw/supplementary/metadata_by_cohort.xlsx`
- `Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx` -> `data/raw/supplementary/subject_level_taxonomic_relative_abundance_values.xlsx`
- `Medium_files/diet.csv` -> `data/raw/media/diet.csv`
- `Suplementary_Data/processed_data/` -> `data/processed/shared/` or `data/processed/micom/age_bin/` depending on file role

### `models/`

Keep actual SBML model files here only.

Recommended:

- `models/agora1_03/`
- `models/agora2/`

This is clearer than keeping model assets under a mixed `Models/` folder with inconsistent version styling.

### `scripts/`

This should contain executable code only.

Recommended subfolders:

- `scripts/data_prep/`
- `scripts/cobrapy/`
- `scripts/micom/`
- `scripts/plotting/`
- `scripts/qc/`

If utility modules become stable, move them to:

- `workflows/shared/`
- `workflows/cobrapy/`
- `workflows/micom/`

That lets scripts stay thin while reusable logic lives in importable modules.

### `results/`

This should contain all generated outputs.

Recommended:

- `results/tables/`: CSV/TSV summaries
- `results/reports/`: build reports, QC reports, run manifests
- `results/figures/`: PNG/PDF/SVG plots

Within each of those, organize first by method family and then by analysis level.

That is the key move that keeps subject-level MICOM manageable.

## Recommended Structure For Subject-Level MICOM

Subject-level MICOM will produce many more files than age-bin median MICOM. It needs a stable home now.

Recommended shape:

```text
results/
├── tables/
│   └── micom/
│       ├── baseline/
│       ├── age_bin/
│       └── subject_level/
│           ├── growth/
│           ├── pathway_flux/
│           ├── tradeoff_sensitivity/
│           ├── provenance/
│           └── summaries/
├── reports/
│   ├── build/
│   │   └── micom/
│   │       ├── baseline/
│   │       ├── age_bin/
│   │       └── subject_level/
│   ├── qc/
│   │   └── micom/
│   │       └── subject_level/
│   └── run_logs/
└── figures/
    └── micom/
        ├── baseline/
        ├── age_bin/
        └── subject_level/
            ├── growth/
            ├── pathway_flux/
            └── provenance/
```

And the matching processed inputs:

```text
data/processed/micom/
├── age_bin/
│   ├── age_bin_taxonomy.csv
│   ├── age_bin_taxonomy_wide.csv
│   └── age_bin_input_qc_summary.csv
└── subject_level/
    ├── subject_taxonomy.csv
    ├── subject_to_age_bin.csv
    ├── subject_input_qc_summary.csv
    ├── subject_filtering_summary.csv
    └── subject_taxon_presence_matrix.csv
```

This gives subject-level MICOM a dedicated namespace instead of forcing it into the same flat result space as age-bin MICOM.

## Naming Convention Recommendation

## Folder Names

Use:

- lowercase
- underscores
- no spaces
- no trailing spaces
- no mixed singular/plural style unless there is a reason

Examples:

- `data/raw/`
- `data/processed/`
- `results/tables/`
- `results/reports/`
- `results/figures/`
- `scripts/micom/`

Avoid:

- `R_for_plotting `
- `Medium_files`
- `Suplementary_Data`

## Script Names

For scripts, keep stage numbering if you like it, but make the scope explicit.

Recommended pattern:

```text
<stage>_<method>_<analysis_level>_<purpose>.py
```

Examples:

- `01_shared_prepare_age_bin_inputs.py`
- `10_cobrapy_single_species_growth.py`
- `20_cobrapy_baseline_community.py`
- `21_cobrapy_age_bin_community.py`
- `30_micom_baseline_community.py`
- `31_micom_age_bin_community.py`
- `40_micom_subject_level_inputs.py`
- `41_micom_subject_level_community.py`
- `42_micom_subject_level_growth_summary.py`
- `43_micom_subject_level_pathway_summary.py`
- `44_micom_subject_level_tradeoff_sensitivity.py`
- `50_compare_cobrapy_vs_micom_age_bin.py`

Why this is better:

- numbering still preserves execution order
- method family is visible immediately
- subject-level MICOM has room to expand without awkward suffixes like `19b`, `19c`, `20b`

## Output File Names

Use a stable pattern:

```text
<method>_<analysis_level>_<content>_<grain>.csv
```

Examples:

- `cobrapy_baseline_species_growth_long.csv`
- `cobrapy_age_bin_species_growth_wide.csv`
- `micom_baseline_taxon_growth_long.csv`
- `micom_age_bin_taxon_growth_wide.csv`
- `micom_subject_level_community_growth_long.csv`
- `micom_subject_level_taxon_growth_long.csv`
- `micom_subject_level_top_grower_summary.csv`
- `micom_subject_level_tradeoff_sensitivity_summary.csv`

For reports:

```text
<method>_<analysis_level>_<report_type>.txt
```

Examples:

- `micom_baseline_build_report.txt`
- `micom_age_bin_build_report.txt`
- `micom_subject_level_build_report.txt`
- `micom_subject_level_input_qc_report.txt`

## Figure Names

Use:

```text
<method>_<analysis_level>_<message>.png
```

Examples:

- `micom_subject_level_growth_rate_distribution.png`
- `micom_subject_level_top_grower_prevalence.png`
- `comparison_cobrapy_vs_micom_age_bin_growth.png`

## How To Handle Official Vs Exploratory Work

You need a hard separation between official pipeline code and trial code.

Recommended rule:

- official scripts stay in `scripts/`
- ad hoc tests go in `archive/exploratory/` or `notebooks/`
- do not keep files like `*_trial.py` in the same folder as official scripts

That single rule will reduce confusion a lot.

## Recommended Migration Of Current Repository

This can be done in phases. Do not try to redesign everything in one move.

### Phase 1: Safe Renaming And Separation

Do first:

- create `docs/`, `data/`, `scripts/`, `results/`, `models/`, `archive/`
- move current markdown notes from `MD/` into `docs/`
- move PDFs into `docs/references/`
- move all generated CSV/TXT outputs out of `Modelling_scripts/` into `results/`
- move plot images out of script folders into `results/figures/`
- rename `Suplementary_Data` to `data/raw/supplementary/` plus `data/processed/...`
- rename `Medium_files` to `data/raw/media/`
- rename `Models` to `models/`

### Phase 2: Script Reorganization

Then:

- move executable Python scripts into `scripts/data_prep/`, `scripts/cobrapy/`, `scripts/micom/`
- move R plotting scripts into `scripts/plotting/`
- move helper utilities into `workflows/shared/`, `workflows/cobrapy/`, or `workflows/micom/`

### Phase 3: Subject-Level MICOM Expansion

Before adding subject-level MICOM:

- create `data/processed/micom/subject_level/`
- create `results/tables/micom/subject_level/`
- create `results/reports/build/micom/subject_level/`
- create `results/reports/qc/micom/subject_level/`
- create `results/figures/micom/subject_level/`

This prevents the new subject-level branch from inheriting the old flat layout.

## Minimal Structure If You Want Less Change

If you want a smaller reorganization that keeps most names familiar, this is the minimum version I would still recommend:

```text
README.md
docs/
data/
  raw/
  processed/
models/
scripts/
  data_prep/
  cobrapy/
  micom/
  plotting/
results/
  tables/
  reports/
  figures/
archive/
```

That already solves most of the scaling problem.

## My Recommendation For This Project

The best fit here is not a giant workflow framework yet.

The best next step is:

1. adopt the top-level `docs/data/models/scripts/results/archive` structure
2. separate scripts from outputs immediately
3. reserve `subject_level` as a first-class branch under both `data/processed/micom/` and `results/.../micom/`
4. replace the current flat numbering style with grouped numbering by method family
5. move exploratory files out of the official analysis path

That gives you a structure that still feels like a scientist-managed project, but will scale much better once subject-level MICOM starts generating many tables, reports, and figures.

## Scientific-Practice Basis

This proposal is consistent with common reproducible-research guidance rather than a single microbiome-only rulebook.

Relevant examples:

- The Turing Way recommends separating input data, methods, and outputs and documenting repository navigation.
- Cookiecutter Data Science promotes a standardized split across data, source code, and results-oriented folders.
- Microbiome reproducibility commentary emphasizes keeping data, metadata, and analytical resources available and clearly connected.
- QIIME 2's reproducibility model is a good reminder that provenance should travel with results, which supports keeping run logs, QC summaries, and build reports near outputs.

## Suggested Next Documentation File

After restructuring, the next useful document would be:

- `docs/sop/repository_layout_sop.md`

That SOP should define:

- what belongs in each top-level folder
- where official outputs go
- how to name scripts
- how to name result files
- how to version protocol changes
- where exploratory work is allowed to live

## Bottom Line

Your instinct is correct.

The current repository is not broken, but it is already starting to mix pipeline code, generated outputs, and exploratory artifacts in ways that will become painful once subject-level MICOM expands.

The cleanest fix is not a fancy system. It is a disciplined separation of:

- data
- scripts
- results
- docs
- models

with `subject_level` treated as a dedicated MICOM branch from the start.
