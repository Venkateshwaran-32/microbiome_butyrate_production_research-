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

## Short Review Standard

If a MICOM result is about to be used in a figure, slide, or write-up, ask:

- Which taxonomy table created this community?
- Which diet was applied?
- What was the tradeoff fraction?
- Were any diet metabolites missing from the MICOM exchange map?
- Is this baseline equal-abundance or age-bin weighted?
- Are we looking at community growth or taxon growth?

If those answers are not clear, the result is not ready to present as a final finding.
