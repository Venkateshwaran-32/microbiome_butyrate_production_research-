# Subject-Level MICOM Script 08/09 Review

Compiled on 2026-05-15 from local repository checks on branch `full-run-with-91-100-age-bin`.

This note summarizes the questions asked about the latest branch, all-cohort age-bin subject counts, scripts `08` and `09`, and high-flux behavior in the pFBA versus no-pFBA outputs.

## 1. Branch Context

The latest local branch by commit date was:

- `full-run-with-91-100-age-bin`

This branch was already checked out when checked.

Important branch details:

- Local `main` and `full-run-with-91-100-age-bin` pointed to the same commit: `359f385`.
- Therefore, there was no committed diff between local `main` and `full-run-with-91-100-age-bin`.
- The previous distinct local branch by commit date was `pca-analysis`.
- The comparison used for committed branch changes was:

```bash
git diff pca-analysis..full-run-with-91-100-age-bin
```

The latest branch contained four commits not present in `pca-analysis`:

- `359f385` Adopt no-pFBA script 09 as canonical all-cohort subject-level run
- `9b4ede4` Validate subject MICOM outputs and remove PCA artifacts
- `2d33094` Update direct flux PCA outputs
- `3fd0d22` Add all-cohort high-fiber flux PCA outputs

The `pca-analysis` branch contained one commit not present in the latest branch:

- `26a82d6` Add PCA analysis scripts and reaction flux workbook

Committed branch diff summary:

- `53 files changed`
- `1,740,531 insertions`
- `171 deletions`

Main additions/changes in the latest branch included:

- Added all-cohort subject-level no-pFBA workflow:
  - `Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py`
  - `Results/subject_level_fba/tables/09_allcohort_subject_community_growth_high_fiber_no_pfba.csv`
  - `Results/subject_level_fba/tables/09_allcohort_subject_taxon_growth_high_fiber_no_pfba.csv`
  - `Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv`
  - `Results/subject_level_fba/reports/09_allcohort_subject_level_high_fiber_no_pfba_build_report.txt`
- Added QC scripts and outputs:
  - `Scripts/qc/PCA_QC.R`
  - `Scripts/qc/inspection_top4_flux_review.R`
  - `Scripts/qc/subject_micom_zero_bound_check.py`
  - `Results/qc/`
- Added output dictionary helpers:
  - `Scripts/modelling/00_report_output_dictionary.py`
  - `Scripts/modelling/00_backfill_report_output_dictionaries.py`
  - `Scripts/plotting_r/00_report_output_dictionary.R`
- Updated modelling scripts `02` through `08`.
- Moved PCA QC from plotting into QC:
  - Deleted `Scripts/plotting_r/PCA_QC.R`
  - Added `Scripts/qc/PCA_QC.R`
- Added documentation under `MD/`, including MICOM/pFBA findings and QC workflow notes.

At the time of inspection, the working tree also had uncommitted changes. Those included updated age-bin figures, cobrapy/MICOM tables and reports, plotting scripts, supplementary processed data, archive folders, `Scripts/plotting_r/00_taxon_utils.R`, and `Rplots.pdf`.

## 2. Subject Counts by Age Bin and Cohort

The source used for the all-cohort subject counts was:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_to_agegroup_lookup.csv
```

Only subjects with:

```text
include_in_subject_micom=True
```

were counted.

Summary:

- Total rows in lookup: `537`
- Included subjects: `516`
- Excluded subjects: `21`
- Exclusion reason for all excluded rows: `missing_from_abundance_workbook`

Age-bin/cohort breakdown:

| Age bin | Cohort breakdown | Total subjects |
|---|---:|---:|
| `21_40` | CRE: 18, T2D: 73 | 91 |
| `41_60` | CRE: 23, SPMP: 28, T2D: 89 | 140 |
| `61_70` | CRE: 28, SPMP: 20, T2D: 9 | 57 |
| `71_80` | CRE: 11, SG90: 20, SPMP: 2 | 33 |
| `81_90` | SG90: 169 | 169 |
| `91_100` | SG90: 26 | 26 |

Cohort totals across all included subjects:

| Cohort | Included subjects |
|---|---:|
| CRE | 80 |
| SG90 | 215 |
| SPMP | 50 |
| T2D | 171 |
| **Total** | **516** |

## 3. Did Scripts 08 and 09 Use the Same 516 Subjects?

Yes.

The relevant scripts were:

```text
Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py
Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py
```

Both scripts used the same all-cohort subject-level MICOM input:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_taxonomy_for_micom.csv
```

Both scripts used the same QC input:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_input_qc_summary.csv
```

Both scripts selected subjects where:

```text
include_in_subject_micom=True
```

The actual output subject IDs were compared against the included subject IDs in the lookup table.

Result:

| Check | Result |
|---|---:|
| Included subjects in lookup | 516 |
| Included subjects in QC input | 516 |
| Script `08` community output subjects | 516 |
| Script `09` community output subjects | 516 |
| Lookup IDs equal script `08` IDs | True |
| Lookup IDs equal script `09` IDs | True |
| Script `08` IDs equal script `09` IDs | True |
| Missing subjects in script `08` | 0 |
| Extra subjects in script `08` | 0 |
| Missing subjects in script `09` | 0 |
| Extra subjects in script `09` | 0 |

The age-bin/cohort breakdown in both script outputs matched the lookup exactly:

| Age bin | Cohort breakdown | Total subjects |
|---|---:|---:|
| `21_40` | CRE: 18, T2D: 73 | 91 |
| `41_60` | CRE: 23, SPMP: 28, T2D: 89 | 140 |
| `61_70` | CRE: 28, SPMP: 20, T2D: 9 | 57 |
| `71_80` | CRE: 11, SG90: 20, SPMP: 2 | 33 |
| `81_90` | SG90: 169 | 169 |
| `91_100` | SG90: 26 | 26 |

## 4. Difference Between Script 08 and Script 09

The main modelling difference is the `pfba` argument passed to MICOM's cooperative tradeoff call.

Script `08` uses pFBA:

```python
community.cooperative_tradeoff(
    high_fiber_bounds,
    TRADEOFF_FRACTION,
    fluxes=True,
    pfba=True,
)
```

Script `09` does not use pFBA:

```python
community.cooperative_tradeoff(
    high_fiber_bounds,
    TRADEOFF_FRACTION,
    fluxes=True,
    pfba=False,
)
```

Shared setup:

- Both are all-cohort subject-level MICOM runs.
- Both use the `high_fiber` diet only.
- Both use `TRADEOFF_FRACTION = 0.5`.
- Both request flux export with `fluxes=True`.
- Both use the same 516 subjects.
- Both write one community row per subject.
- Both write taxon growth rows for optimal solves.
- Both write nonzero long-format reaction flux rows.

Output/report differences:

| Item | Script 08 | Script 09 |
|---|---|---|
| Method label | pFBA | no-pFBA |
| MICOM argument | `pfba=True` | `pfba=False` |
| Community output | `08_allcohort_subject_community_growth_high_fiber_pfba.csv` | `09_allcohort_subject_community_growth_high_fiber_no_pfba.csv` |
| Taxon output | `08_allcohort_subject_taxon_growth_high_fiber_pfba.csv` | `09_allcohort_subject_taxon_growth_high_fiber_no_pfba.csv` |
| Flux output | `08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv` | `09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv` |
| Build report | `08_allcohort_subject_level_high_fiber_pfba_build_report.txt` | `09_allcohort_subject_level_high_fiber_no_pfba_build_report.txt` |
| `pfba` value written in output rows | `True` | `False` |

Additional non-modelling code differences:

- Script `09` updates output dictionary/report text to explicitly describe the no-pFBA run.
- Script `09` changes the `objective_value` documentation from `pfba=True` to `pfba=False`.
- Script `09` changes `--subject-id` CLI behavior:
  - Script `08` accepts a single `--subject-id`.
  - Script `09` uses `action="append"` and can accept multiple repeated `--subject-id` flags.
- Script `09` changes report labels from pFBA to no-pFBA.

Therefore:

- The only meaningful modelling-method difference is `pfba=True` versus `pfba=False`.
- The scripts also differ in output paths, report/documentation text, row metadata values, and multiple-subject CLI filtering.

## 5. Script 08 pFBA High-Flux Results

The script `08` pFBA flux table checked was:

```text
Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv
```

Threshold used:

```text
abs_flux > 1000
```

The table contains both signed `flux` and absolute `abs_flux`. The main high-flux count used `abs_flux > 1000`, because very large negative fluxes are also high-magnitude fluxes.

Script `08` pFBA flux summary:

| Metric | Count |
|---|---:|
| Total nonzero flux rows | 1,930,299 |
| Rows with `abs_flux > 1000` | 2,169 |
| Rows with signed `flux > 1000` | 1,099 |
| Subjects with at least one `abs_flux > 1000` | 11 |
| Unique reactions with `abs_flux > 1000` | 1,645 |
| Unique `feature_id` values with `abs_flux > 1000` | 2,020 |
| Medium rows with `abs_flux > 1000` | 98 |
| Taxon rows with `abs_flux > 1000` | 2,071 |

Largest pFBA flux observed:

| Field | Value |
|---|---|
| Subject | `MBS1232` |
| Cohort | `SG90` |
| Age bin | `81_90` |
| Compartment | `Bacteroides_xylanisolvens_XB1A` |
| Reaction | `N_OH_PHTN_GLC_GLCAASE` |
| Feature ID | `Bacteroides_xylanisolvens_XB1A__N_OH_PHTN_GLC_GLCAASE` |
| Flux | `3949247.445432582` |
| Absolute flux | `3949247.445432582` |
| Medium row | `False` |

Interpretation:

- Script `08` produced a clear high-flux issue under pFBA.
- There were 2,169 high-magnitude flux rows above 1,000.
- The issue affected 11 subjects.
- Most high-flux rows were taxon-level rows rather than medium rows.

## 6. Script 09 no-pFBA Flux Results

The script `09` no-pFBA flux table checked was:

```text
Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv
```

Threshold used:

```text
abs_flux > 1000
```

Script `09` no-pFBA flux summary:

| Metric | Count |
|---|---:|
| Total nonzero flux rows | 1,718,680 |
| Rows with `abs_flux > 1000` | 2 |
| Rows with signed `flux > 1000` | 2 |
| Subjects with at least one `abs_flux > 1000` | 2 |
| Maximum `abs_flux` | `1000.0000000000005` |

Largest no-pFBA flux observed:

| Field | Value |
|---|---|
| Subject | `MHS288` |
| Cohort | `SPMP` |
| Age bin | `41_60` |
| Compartment | `Klebsiella_pneumoniae_pneumoniae_MGH78578` |
| Reaction | `G6PI` |
| Feature ID | `Klebsiella_pneumoniae_pneumoniae_MGH78578__G6PI` |
| Flux | `1000.0000000000005` |
| Absolute flux | `1000.0000000000005` |
| Medium row | `False` |

Interpretation:

- Practically, script `09` removed the high-flux problem seen in script `08`.
- The only values technically above 1,000 were `1000.0000000000005`, which is effectively 1,000 and consistent with floating-point roundoff.
- There were no large flux outliers comparable to the pFBA run.

## 7. Script 08 vs Script 09 Output Comparison

From the build reports:

| Metric | Script 08 pFBA | Script 09 no-pFBA |
|---|---:|---:|
| Selected subjects | 516 | 516 |
| Community rows written | 516 | 516 |
| Taxon rows written | 3,025 | 3,025 |
| Flux rows written | 1,930,299 | 1,718,680 |
| pFBA enabled | True | False |
| High-flux rows with `abs_flux > 1000` | 2,169 | 2 |
| Maximum `abs_flux` | 3,949,247.445432582 | 1000.0000000000005 |

Community growth note from build reports:

| Metric | Script 08 pFBA | Script 09 no-pFBA |
|---|---:|---:|
| Subjects with community growth rate `<= 1e-09` | 101 | 0 |

The script `09` report labels this as:

```text
Optimal subjects with community_growth_rate <= 1e-09: 0
```

## 8. Overall Conclusion

Scripts `08` and `09` used the same 516 all-cohort included subjects with the same age-bin and cohort composition.

The major modelling difference is:

```text
Script 08: pfba=True
Script 09: pfba=False
```

The pFBA run in script `08` produced large high-flux outliers:

- 2,169 rows with `abs_flux > 1000`
- maximum `abs_flux` around 3.95 million

The no-pFBA run in script `09` effectively removed those high-flux outliers:

- only 2 rows technically above 1,000
- maximum `abs_flux = 1000.0000000000005`, effectively 1,000 due to floating-point precision

Based on these checks, script `09` is the cleaner all-cohort subject-level high-fiber MICOM run for avoiding the pFBA-associated high-flux artifact observed in script `08`.
