# Project SOP

## Purpose

This SOP defines the standard way to run, validate, and interpret the microbiome butyrate community-modeling workflow in this repository.

The intent is to make the project:

- reproducible
- auditable
- easier to extend without breaking earlier analyses
- more aligned with disciplined community-modeling practice

This SOP applies to both the COBRApy community branch and the MICOM community branch.

## Scope

This workflow currently covers:

- preprocessing supplementary abundance inputs into model-ready age-bin tables
- SG90-specific recovery of subject-level raw abundance inputs for MICOM
- single-species baseline screening
- shared-environment COBRApy community modeling
- MICOM baseline community modeling
- MICOM age-bin community modeling
- MICOM subject-level SG90 community modeling
- downstream summary-table generation for plotting and interpretation

This SOP does not claim that the current workflow proves in vivo butyrate production. It only governs how the in silico analyses are run and interpreted.

## Core Operating Principles

- One question per script family. Do not overload a script with unrelated biological claims.
- Inputs must be explicit. Every run should point to named files, not informal assumptions.
- Validation happens before interpretation.
- Community growth and butyrate evidence are separate analytical layers.
- Missing diet-metabolite mappings must be reported, not silently ignored.
- Age-bin abundance weights must sum to `1.0` within each age group before a community run is accepted.
- Baseline and age-weighted runs must remain directly comparable by using the same model set and diet source unless a protocol change is explicitly documented.

## Canonical Workflow Order

Run the project in this order:

1. Prepare age-bin inputs with [01_prepare_supplementary_agebin_inputs.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py:1).
2. Run single-species baseline screening with [01_single_species_growth_and_butyrate.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:1).
3. Run the COBRApy shared-environment baseline with [02_community_shared_environment.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:1).
4. Run the COBRApy age-bin weighted community with [03_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/03_agebin_weighted_community.py:1).
5. Run the MICOM baseline community with [04_micom_baseline_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/04_micom_baseline_community.py:1).
6. Run the MICOM age-bin weighted community with [05_micom_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/05_micom_agebin_weighted_community.py:1).
7. Rebuild SG90 subject-level MICOM inputs with [02_prepare_sg90_subject_level_micom_inputs.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/data_processing/02_prepare_sg90_subject_level_micom_inputs.py:1).
8. Run SG90 subject-level MICOM with [06_micom_subject_level_sg90.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/06_micom_subject_level_sg90.py:1).

Do not jump straight to age-bin MICOM interpretation without checking that the upstream processed abundance tables and baseline runs are internally consistent.

## Required Inputs

The current official inputs are:

- AGORA2 SBML models in [Models/vmh_agora2_sbml](/Users/taknev/Desktop/microbiome_butyrate_production_research/Models/vmh_agora2_sbml)
- diet definitions in [Medium_files/diet.csv](/Users/taknev/Desktop/microbiome_butyrate_production_research/Medium_files/diet.csv:1)
- supplementary metadata in [Suplementary_Data/Metadata_by_cohort.xlsx](/Users/taknev/Desktop/microbiome_butyrate_production_research/Suplementary_Data/Metadata_by_cohort.xlsx)
- subject-level abundance data in [Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx](/Users/taknev/Desktop/microbiome_butyrate_production_research/Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx)

Official processed abundance inputs for age-bin work are:

- [allcohort_agebin_median_abundance_10_species.csv](/Users/taknev/Desktop/microbiome_butyrate_production_research/Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv:1)
- [allcohort_agebin_median_abundance_10_species_wide.csv](/Users/taknev/Desktop/microbiome_butyrate_production_research/Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species_wide.csv:1)
- [agebin_input_qc_summary.csv](/Users/taknev/Desktop/microbiome_butyrate_production_research/Suplementary_Data/processed_data/agebin_input_qc_summary.csv:1)

## Entry Criteria Before Any New Run

Before treating a run as official:

- confirm the model directory being used
- confirm the diet file being used
- confirm whether the run is equal-abundance baseline or age-bin weighted
- confirm the output file names
- confirm the target species count
- confirm that the processed age-bin table still points to existing model files

If any of those change, the run should be treated as a new analysis version rather than a continuation of the old one.

## QC Gates

### Data Preparation Gate

The processed age-bin table is acceptable only if:

- each age group has the expected `10` modeled species
- each age group has unique `model_species_id` values
- normalized weights sum to `1.0`
- every referenced `model_file` exists

These are already enforced by the current code path in [05_micom_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/05_micom_agebin_weighted_community.py:38).

### Model-Build Gate

A baseline or age-bin community run is acceptable only if:

- the solver status is reported
- community growth is reported
- matched diet metabolite counts are reported
- missing diet metabolite counts are reported
- the build report is written to disk

### Interpretation Gate

Do not interpret a result as biologically meaningful until:

- the build report has been checked for missing metabolite mappings
- the number of growing taxa has been reviewed
- the run has been compared against the relevant baseline
- butyrate claims have been separated into pathway evidence and exchange evidence

## Standard Outputs To Keep

For each official run, keep:

- a community summary CSV
- a taxon or species growth CSV
- a wide-format CSV when comparing age bins
- a build report text file

This is already the pattern used in the MICOM scripts and should remain the standard.

## MICOM-Specific Standards

For MICOM analyses in this repository:

- use explicit taxonomy tables with `id`, `file`, and `abundance`
- use equal abundance only for the baseline community
- use `normalized_weight` from the processed age-bin table for age-bin communities
- keep the tradeoff fraction explicit and stable unless intentionally changed
- report missing diet-metabolite mappings for every diet
- store both community-level and taxon-level outputs

The current standard tradeoff fraction in the MICOM workflows is `0.5`, as defined in:

- [04_micom_baseline_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/04_micom_baseline_community.py:31)
- [05_micom_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/05_micom_agebin_weighted_community.py:31)

## Interpretation Guardrails

Use the following language discipline:

- Say "butyrate-related evidence" unless direct modeled secretion evidence is shown.
- Do not say a species "cannot grow" unless the statement is tied to a specific model, diet, and optimization setup.
- Do not treat sparse community optima as proof that non-growing taxa are invalid models.
- Do not collapse pathway presence, reaction flux, and exchange flux into one label.
- Do not compare COBRApy and MICOM outputs as if they were identical optimization frameworks.

## Change Control

Any of the following should be written down in the README or a dated note before reuse of outputs:

- changing the species set
- changing the model database version
- changing the diet file structure
- changing the tradeoff fraction
- changing the growth threshold
- changing the age-bin definition
- changing the interpretation criteria for butyrate evidence

If one of these changes, old outputs should not be mixed with new outputs in the same figure or conclusion without clearly labeling the version difference.

## Minimum Review Checklist

Before presenting results upward or using them in writing, check:

- Which script produced this table?
- Which diet was used?
- Which model collection was used?
- Was the run baseline or age-bin weighted?
- Are missing metabolites reported?
- Are abundance weights validated?
- Are butyrate statements phrased as evidence rather than certainty?
- Are COBRApy and MICOM results being compared fairly?

## Recommended Next Operational Upgrades

The next step toward an even stricter workflow would be to add:

- a pinned environment file for `cobra`, `micom`, and `pandas`
- a single reproducible run script that executes the canonical order
- a dated run log for official analysis outputs
- a version tag for output tables when protocol settings change
