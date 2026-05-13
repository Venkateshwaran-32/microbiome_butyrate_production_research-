# MICOM Practices

## Why This Note Exists

This document turns the current MICOM branch of the project into a defined practice standard rather than a set of isolated scripts.

It is based on the patterns already present in:

- [00_micom_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_micom_utils.py:1)
- [04_micom_baseline_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/04_micom_baseline_community.py:1)
- [05_micom_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/05_micom_agebin_weighted_community.py:1)

## Standard MICOM Workflow In This Repo

The standard MICOM pattern is:

1. Build a taxonomy table.
2. Create a `Community`.
3. Translate diet metabolite IDs into MICOM exchange IDs.
4. Apply the medium explicitly.
5. Run `cooperative_tradeoff()`.
6. Normalize the members table for downstream export.
7. Write both summary outputs and a build report.

This is the workflow we should keep unless there is a deliberate protocol change.

## Practice 1: Taxonomy Tables Must Be Explicit

Do not build communities from informal lists.

The taxonomy table must state:

- `id`
- `species`
- `file`
- `abundance`

For baseline MICOM runs, abundance should be equal across the selected species.

For age-bin MICOM runs, abundance should come from the processed `normalized_weight` values, not from ad hoc manual edits.

## Practice 2: Medium Translation Must Be Audited

Diet input files and MICOM exchange IDs are not assumed to match perfectly.

The current utility code deliberately:

- normalizes exchange tokens
- builds an exchange lookup from the actual community
- records missing diet metabolites

That is the right habit. Missing mappings are a result, not a nuisance to hide.

## Practice 3: Tradeoff Must Stay Explicit

MICOM behavior depends strongly on the tradeoff setting.

In this repository, the current working standard is `fraction=0.5` during `cooperative_tradeoff()`.

That value should always be:

- visible in code
- written to the build report
- mentioned when interpreting results across runs

## Practice 4: Community-Level And Taxon-Level Outputs Are Both Required

A serious MICOM workflow should not stop at one scalar community growth value.

Keep both:

- community summary outputs
- taxon/member growth outputs

This is already done in the baseline and age-bin scripts and should remain mandatory.

## Practice 5: Validation Before Solve

Age-bin MICOM runs should only proceed when the processed abundance input passes basic structural checks:

- expected number of species per age group
- normalized weights sum to `1.0`
- no duplicate `model_species_id` values
- all referenced model files exist

The current implementation already enforces this and that is a strength worth protecting.

## Practice 6: Wide Outputs For Cross-Age Comparison

Long-format outputs are best for traceability and plotting pipelines.

Wide outputs are best for fast comparison across age bins.

That is why the age-bin MICOM branch should continue writing:

- a long taxon-growth table
- a wide taxon-growth table

## Practice 7: Interpretation Must Respect MICOM’s Role

MICOM is not just another way to print the same answer as the COBRApy shared-environment model.

When writing conclusions:

- do not treat MICOM and COBRApy as numerically interchangeable
- do use MICOM to study community growth allocation under abundance-weighted structure
- do interpret differences as model-framework differences first, biology second

## Practice 8: Reports Must Be Kept With Outputs

Every official MICOM run should leave behind a plain-text build report that captures:

- community ID
- input file references
- tradeoff fraction
- taxonomy abundances
- solver status
- matched diet metabolite count
- missing diet metabolite count
- a `CSV Output Dictionary` section documenting each generated CSV path, row grain, exact column names, and formulas for derived or non-obvious columns

This practice is already in place and should become non-negotiable.

## Practice 9: Separate Questions Cleanly

Use the MICOM branch to answer:

- how the community grows under a defined medium
- which taxa receive nonzero growth
- how age-bin abundance weighting changes the result

Do not use the MICOM branch by itself to overclaim:

- definitive butyrate secretion
- in vivo dominance
- causal age biology

## Practice 10: pFBA Stage 3 Infeasibility Under `cooperative_tradeoff`

`MICOM.cooperative_tradeoff(fraction=..., fluxes=True, pfba=True)` runs as a 3-stage LP:

1. **Stage 1** — maximize community growth (with L2 regularization on member growths).
2. **Stage 2** — re-solve at `fraction × max_growth`, balanced via L2.
3. **Stage 3 (pFBA polish)** — `add_pfba_objective(community, atol, rtol)` reads the *primal* member growth rates from stage 2 and pins them as lower bounds via `obj.lb = (1.0 - rtol) * rate - atol` (default `atol = rtol = 1e-6`), then minimizes Σ|flux|.

For the all-cohort high-fiber subject-level branch (script 08), stage 3 was infeasible for ~2% of subjects (11 of 516) with 8 of those 11 in SG90 `81_90`. Their stage-2 `objective_value` ranged from 66,408 to 43,949,989 — orders of magnitude above the cohort norm (<100), indicating that stage 2 sat near a degenerate vertex with tightly coupled species. When stage 3 then asked the LP to hold those member-growth rates almost-exactly while also minimizing Σ|flux|, the constraints became jointly unsatisfiable within solver tolerance.

Two trap behaviors compound the issue and must be remembered:

- When stage 3 is infeasible, MICOM does not erase `solution.fluxes`. The DataFrame holds whatever simplex-tableau values were sitting in memory — for these subjects, magnitudes up to 3.95M, not a valid flux distribution. Off-LP numerical artifacts.
- COBRApy's `solution.growth_rate` returns `0.0` for an infeasible LP. If a script does an unconditional `float(solution.growth_rate)`, the summary CSV will misleadingly show `0.0` instead of an empty cell. Always gate flux export and growth rate writing on `solver.status == "optimal"`.

### Project decision

For subject-level all-cohort high-fiber flux work, use `pfba=False` (script 09 — `Scripts/modelling/09_micom_allcohort_subject_level_high_fiber_no_pfba.py`). pFBA is unsuitable for this community/diet combination because the failure mode produces zero growth plus off-LP fluxes for a non-trivial fraction of subjects.

The 11 subjects that exposed this failure mode (stable list, useful for audit cross-references):

`MBS1232, MBS1529, MBS1262, MBS1255, MBS1539, MHS276, MBS1535, MBS1438, CON079, MBS1576, MBS1439`

These are not "outliers" in the no-pFBA results — under script 09 they solve optimally with community growth in the 0.24–0.65 range, in line with the rest of the cohort.

### Flux interpretation under no-pFBA

Without pFBA the LP returns *some* optimal vertex rather than the parsimonious one. A reaction at exactly ±1000 means it is saturated against the AGORA SBML reaction bound, not that biology demanded that magnitude. When interpreting flux tables from script 09 outputs, distinguish "saturated at bound" from "actively chosen below bound" — saturated values reflect LP flexibility, not metabolic intensity.

### Status of on-disk script 08 outputs

The 08 result tables and build report are retained on disk as audit-trail artifacts of the pFBA failure investigation:

- `Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv`
- `Results/subject_level_fba/tables/08_allcohort_subject_taxon_growth_high_fiber_pfba.csv`
- `Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv`
- `Results/subject_level_fba/reports/08_allcohort_subject_level_high_fiber_pfba_build_report.txt`

These files were written by commit `371cf94`, which lacked the `solver_status != "optimal"` gate before flux export. They contain `solver_status = infeasible` rows with `community_growth_rate = 0.0` and ~17k flux rows of off-LP simplex artifacts for the 11 subjects above. **Do not consume them in any downstream analysis** — use the script 09 outputs (`*_no_pfba.csv`) instead. The 08 files are kept for the writeup audit trail only.

## Short Review Standard

If a MICOM result is about to be used in a figure, slide, or write-up, ask:

- Which taxonomy table created this community?
- Which diet was applied?
- What was the tradeoff fraction?
- Were any diet metabolites missing from the MICOM exchange map?
- Is this baseline equal-abundance or age-bin weighted?
- Are we looking at community growth or taxon growth?

If those answers are not clear, the result is not ready to present as a final finding.
