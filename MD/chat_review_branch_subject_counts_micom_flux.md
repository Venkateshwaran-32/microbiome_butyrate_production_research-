# Chat Review: Branch Changes, Subject Counts, MICOM Scripts, and Flux Checks

Compiled on 2026-05-15 from the current local repository state on branch `full-run-with-91-100-age-bin`.

This document records the full set of questions asked in the chat and the results that were checked from the repository. It is written as a traceable review, with the source files and exact counts used wherever possible.

## 1. Latest Branch and Previous Branch Comparison

### Question

Check out the latest branch, compare it to the previous branch, and report the changes.

### Branch state found

The newest local branch by commit date was:

```text
full-run-with-91-100-age-bin
```

It was already checked out.

The local branch order by commit date was:

```text
2026-05-13 full-run-with-91-100-age-bin
2026-05-13 main
2026-04-30 pca-analysis
2026-04-30 inspection-top-4
```

After fetching remote refs, the remote branches were:

```text
origin/main
origin/inspection-top-4
origin/afte-08
```

No newer remote branch was found.

### Important branch caveat

Local `main` and `full-run-with-91-100-age-bin` pointed to the same commit:

```text
359f385 Adopt no-pFBA script 09 as canonical all-cohort subject-level run
```

Therefore, there was no committed diff between local `main` and `full-run-with-91-100-age-bin`.

The previous distinct local branch was:

```text
pca-analysis
```

So the meaningful committed branch comparison was:

```bash
git diff pca-analysis..full-run-with-91-100-age-bin
```

### Commits in latest branch not in `pca-analysis`

```text
359f385 Adopt no-pFBA script 09 as canonical all-cohort subject-level run
9b4ede4 Validate subject MICOM outputs and remove PCA artifacts
2d33094 Update direct flux PCA outputs
3fd0d22 Add all-cohort high-fiber flux PCA outputs
```

### Commit in `pca-analysis` not in latest branch

```text
26a82d6 Add PCA analysis scripts and reaction flux workbook
```

### Committed diff summary

```text
53 files changed
1,740,531 insertions
171 deletions
```

Most of the insertion count came from large result tables, especially subject-level flux outputs.

### Main changes found in latest branch

Added all-cohort subject-level no-pFBA workflow:

```text
Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py
Results/subject_level_fba/reports/09_allcohort_subject_level_high_fiber_no_pfba_build_report.txt
Results/subject_level_fba/tables/09_allcohort_subject_community_growth_high_fiber_no_pfba.csv
Results/subject_level_fba/tables/09_allcohort_subject_taxon_growth_high_fiber_no_pfba.csv
Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv
```

Added QC scripts and outputs:

```text
Scripts/qc/PCA_QC.R
Scripts/qc/inspection_top4_flux_review.R
Scripts/qc/subject_micom_zero_bound_check.py
Results/qc/
```

Added output dictionary helpers:

```text
Scripts/modelling/00_report_output_dictionary.py
Scripts/modelling/00_backfill_report_output_dictionaries.py
Scripts/plotting_r/00_report_output_dictionary.R
```

Updated modelling scripts:

```text
Scripts/modelling/02_community_shared_environment.py
Scripts/modelling/03_agebin_weighted_community.py
Scripts/modelling/04_micom_baseline_community.py
Scripts/modelling/05_micom_agebin_weighted_community.py
Scripts/modelling/06_micom_subject_level_sg90.py
Scripts/modelling/06c_review_sg90_subject_level_micom_abnormalities.py
Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py
```

Moved PCA QC work from plotting into QC:

```text
Deleted: Scripts/plotting_r/PCA_QC.R
Added:   Scripts/qc/PCA_QC.R
```

Added documentation:

```text
MD/inspection_top4_note.md
MD/micom_pfba_research_findings.md
MD/micom_pfba_research_findings.html
MD/micom_pfba_research_findings.pdf
MD/qc_and_charting_workflow.md
```

### Working tree caveat

At the time of the branch check, the working tree had uncommitted changes. These were not part of the committed branch comparison.

The uncommitted changes included:

- updated cobrapy age-bin figures, tables, and reports;
- updated MICOM age-bin figures, tables, and reports;
- updated plotting R scripts;
- updated supplementary processed age-bin data;
- new archive folders under cobrapy, MICOM, and supplementary processed data;
- `Scripts/plotting_r/00_taxon_utils.R`;
- `Results/micom_fba/figures/micom_multispecies_agebin_growth_v2.png`;
- `Rplots.pdf`.

Uncommitted working-tree diff summary:

```text
30 files changed
698 insertions
417 deletions
```

## 2. Number of Subjects in Each Age Bin and Which Cohort They Come From

### Question

List the number of subjects in each age bin and which cohort they come from.

### Source file used

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_to_agegroup_lookup.csv
```

Only rows with the following flag were counted:

```text
include_in_subject_micom=True
```

### Lookup table totals

```text
Total rows: 537
Included subjects: 516
Excluded rows: 21
```

All 21 excluded rows had:

```text
exclusion_reason=missing_from_abundance_workbook
```

### Age-bin and cohort breakdown

| Age bin | Cohort breakdown | Total subjects |
|---|---:|---:|
| `21_40` | CRE: 18, T2D: 73 | 91 |
| `41_60` | CRE: 23, SPMP: 28, T2D: 89 | 140 |
| `61_70` | CRE: 28, SPMP: 20, T2D: 9 | 57 |
| `71_80` | CRE: 11, SG90: 20, SPMP: 2 | 33 |
| `81_90` | SG90: 169 | 169 |
| `91_100` | SG90: 26 | 26 |

### Cohort totals across all included subjects

| Cohort | Subjects |
|---|---:|
| CRE | 80 |
| SG90 | 215 |
| SPMP | 50 |
| T2D | 171 |
| **Total** | **516** |

## 3. Whether Scripts 08 and 09 Ran Subject-Level MICOM on the Same 516 Subjects

### Question

For scripts `08` and `09`, did we do subject-level MICOM on all 516 subjects, and are they all the same as in the lookup?

### Scripts checked

```text
Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py
Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py
```

### Inputs used by both scripts

Both scripts use the same subject-level taxonomy input:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_taxonomy_for_micom.csv
```

Both scripts use the same QC input:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_input_qc_summary.csv
```

Both scripts select rows where:

```text
include_in_subject_micom=True
```

### Output files checked

Script `08` community output:

```text
Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv
```

Script `09` community output:

```text
Results/subject_level_fba/tables/09_allcohort_subject_community_growth_high_fiber_no_pfba.csv
```

### Subject ID set comparison

| Check | Result |
|---|---:|
| Included subjects in lookup | 516 |
| Included subjects in QC input | 516 |
| Script `08` output subjects | 516 |
| Script `09` output subjects | 516 |
| Lookup IDs equal QC IDs | True |
| Lookup IDs equal script `08` IDs | True |
| Lookup IDs equal script `09` IDs | True |
| Script `08` IDs equal script `09` IDs | True |
| Missing in script `08` | 0 |
| Extra in script `08` | 0 |
| Missing in script `09` | 0 |
| Extra in script `09` | 0 |

### Conclusion

Yes. Scripts `08` and `09` both ran on exactly the same 516 included all-cohort subjects.

The age-bin/cohort composition was also identical in the lookup, script `08` output, and script `09` output:

| Age bin | Cohort breakdown | Total subjects |
|---|---:|---:|
| `21_40` | CRE: 18, T2D: 73 | 91 |
| `41_60` | CRE: 23, SPMP: 28, T2D: 89 | 140 |
| `61_70` | CRE: 28, SPMP: 20, T2D: 9 | 57 |
| `71_80` | CRE: 11, SG90: 20, SPMP: 2 | 33 |
| `81_90` | SG90: 169 | 169 |
| `91_100` | SG90: 26 | 26 |

## 4. Difference Between Script 08 and Script 09

### Question

What was the difference between script `08` and script `09`?

### Main modelling difference

The central modelling difference is the `pfba` argument passed into MICOM's cooperative tradeoff call.

Script `08`:

```python
community.cooperative_tradeoff(
    high_fiber_bounds,
    TRADEOFF_FRACTION,
    fluxes=True,
    pfba=True,
)
```

Script `09`:

```python
community.cooperative_tradeoff(
    high_fiber_bounds,
    TRADEOFF_FRACTION,
    fluxes=True,
    pfba=False,
)
```

### Shared behaviour

Both scripts:

- run all-cohort subject-level MICOM;
- use the same 516 subjects;
- use the same subject taxonomy input;
- use the same QC input;
- use the `high_fiber` diet only;
- use `TRADEOFF_FRACTION = 0.5`;
- use `fluxes=True`;
- write one community row per subject;
- write taxon growth rows;
- write long-format nonzero reaction flux rows.

### Output and report differences

| Item | Script 08 | Script 09 |
|---|---|---|
| Method | pFBA | no-pFBA |
| MICOM argument | `pfba=True` | `pfba=False` |
| Community output | `08_allcohort_subject_community_growth_high_fiber_pfba.csv` | `09_allcohort_subject_community_growth_high_fiber_no_pfba.csv` |
| Taxon output | `08_allcohort_subject_taxon_growth_high_fiber_pfba.csv` | `09_allcohort_subject_taxon_growth_high_fiber_no_pfba.csv` |
| Flux output | `08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv` | `09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv` |
| Build report | `08_allcohort_subject_level_high_fiber_pfba_build_report.txt` | `09_allcohort_subject_level_high_fiber_no_pfba_build_report.txt` |
| `pfba` column value | `True` | `False` |

### Build report results

| Metric | Script 08 pFBA | Script 09 no-pFBA |
|---|---:|---:|
| Selected subjects | 516 | 516 |
| Community rows written | 516 | 516 |
| Taxon rows written | 3,025 | 3,025 |
| Flux rows written | 1,930,299 | 1,718,680 |
| pFBA enabled | True | False |
| Subjects with community growth rate `<= 1e-09` | 101 | 0 |

The script `09` build report labels the last metric as:

```text
Optimal subjects with community_growth_rate <= 1e-09: 0
```

## 5. Whether `pfba=True` vs `pfba=False` Was the Only Code Difference

### Question

Is `pfba=True` versus `pfba=False` the only line of code that is different between script `08` and script `09`, or is there more?

### Result

No, it is not only one changed line.

The only meaningful modelling-method difference is:

```text
Script 08: pfba=True
Script 09: pfba=False
```

However, a direct file comparison showed additional support differences:

1. Output paths differ.
   - Script `08` writes files with `08_*_pfba` names.
   - Script `09` writes files with `09_*_no_pfba` names.

2. CSV output dictionary text differs.
   - Script `09` explicitly documents the run as no-pFBA.
   - The `objective_value` description changes from `pfba=True` to `pfba=False`.

3. CLI subject filtering differs.
   - Script `08` accepts one `--subject-id`.
   - Script `09` uses `action="append"`, so repeated `--subject-id` flags can include multiple subjects.

4. Report text differs.
   - Script `08`: high-fiber pFBA build report.
   - Script `09`: high-fiber no-pFBA build report.
   - Script `08`: `pFBA enabled: True`.
   - Script `09`: `pFBA enabled: False`.

5. Output row metadata differs.
   - Script `08` writes `pfba=True` in output rows.
   - Script `09` writes `pfba=False` in output rows.

### Conclusion

The modelling-method change is one line, but the scripts also differ in output naming, report text, documentation, metadata values, and command-line subject filtering.

## 6. Script 08 pFBA High-Flux Count Above 1,000

### Question

For the results from script `08`, how many high fluxes were above 1k?

### Source file used

```text
Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv
```

### Threshold used

The main count used:

```text
abs_flux > 1000
```

This was used because the table includes both signed `flux` and absolute `abs_flux`, and high-magnitude negative flux values should also count as high fluxes.

### Results

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

### Largest high-flux row in script 08

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

### Conclusion

Script `08` produced a clear high-flux issue under pFBA:

- 2,169 rows had `abs_flux > 1000`.
- 11 subjects had at least one high-flux row.
- The maximum flux magnitude was about 3.95 million.

## 7. Script 09 no-pFBA Fluxes Above 1,000

### Question

When we ran `pfba=False` in script `09`, were the fluxes all under 1k?

### Source file used

```text
Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv
```

### Threshold used

```text
abs_flux > 1000
```

Signed positive flux was also checked with:

```text
flux > 1000
```

### Results

| Metric | Count |
|---|---:|
| Total nonzero flux rows | 1,718,680 |
| Rows with `abs_flux > 1000` | 2 |
| Rows with signed `flux > 1000` | 2 |
| Subjects with at least one `abs_flux > 1000` | 2 |
| Maximum `abs_flux` | `1000.0000000000005` |

### Largest no-pFBA flux row

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

### Conclusion

Practically, yes: the script `09` no-pFBA run removed the high-flux problem.

There were technically 2 rows with values slightly above 1,000, but the maximum was:

```text
1000.0000000000005
```

This is effectively 1,000 and is consistent with floating-point precision. There were no large flux outliers like those seen in the script `08` pFBA output.

## 8. Overall Chat Conclusions

1. The latest local branch was `full-run-with-91-100-age-bin`.

2. Local `main` and `full-run-with-91-100-age-bin` pointed to the same commit, so the useful branch comparison was against `pca-analysis`.

3. The latest branch added the no-pFBA all-cohort subject-level MICOM workflow, QC outputs, output dictionaries, and updated modelling/reporting files.

4. The all-cohort subject set contained 516 included subjects and 21 excluded metadata rows missing from the abundance workbook.

5. The included 516 subjects were distributed across age bins and cohorts as follows:

| Age bin | Cohort breakdown | Total subjects |
|---|---:|---:|
| `21_40` | CRE: 18, T2D: 73 | 91 |
| `41_60` | CRE: 23, SPMP: 28, T2D: 89 | 140 |
| `61_70` | CRE: 28, SPMP: 20, T2D: 9 | 57 |
| `71_80` | CRE: 11, SG90: 20, SPMP: 2 | 33 |
| `81_90` | SG90: 169 | 169 |
| `91_100` | SG90: 26 | 26 |

6. Scripts `08` and `09` both ran on exactly those same 516 subjects.

7. The key modelling difference was pFBA:

```text
Script 08: pfba=True
Script 09: pfba=False
```

8. Script `08` pFBA produced high-flux outliers:

```text
2,169 rows with abs_flux > 1000
maximum abs_flux = 3949247.445432582
```

9. Script `09` no-pFBA effectively removed the high-flux outliers:

```text
2 rows with abs_flux > 1000
maximum abs_flux = 1000.0000000000005
```

10. The remaining values above 1,000 in script `09` are effectively at the 1,000 bound and appear to be floating-point precision, not true high-flux artifacts.

## 9. Files Referenced in This Review

Branch and documentation files:

```text
MD/
Scripts/modelling/
Scripts/qc/
Results/qc/
```

Subject lookup and QC:

```text
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_to_agegroup_lookup.csv
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_input_qc_summary.csv
Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_taxonomy_for_micom.csv
```

Scripts:

```text
Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py
Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py
```

Script `08` outputs:

```text
Results/subject_level_fba/reports/08_allcohort_subject_level_high_fiber_pfba_build_report.txt
Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv
Results/subject_level_fba/tables/08_allcohort_subject_taxon_growth_high_fiber_pfba.csv
Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv
```

Script `09` outputs:

```text
Results/subject_level_fba/reports/09_allcohort_subject_level_high_fiber_no_pfba_build_report.txt
Results/subject_level_fba/tables/09_allcohort_subject_community_growth_high_fiber_no_pfba.csv
Results/subject_level_fba/tables/09_allcohort_subject_taxon_growth_high_fiber_no_pfba.csv
Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv
```
