# Microbiome Butyrate Production Research

## Project Overview

This project is focused on community metabolic modeling of a small microbiome species set using SBML genome-scale metabolic models and diet constraints. The main goal is to understand which species dominate modeled community growth, how that behavior changes across age-bin-specific abundance weightings, and whether butyrate-related metabolism is supported by pathway and exchange evidence.

The project is intentionally cautious about interpretation. In this workflow, "butyrate production" is not treated as a single yes/no signal. Instead, evidence is separated into:

- community growth dominance,
- internal butyrate-related pathway activity,
- exchange with the shared environment.

The project now also has an explicit operating standard in:

- [MD/project_sop.md](/Users/taknev/Desktop/microbiome_butyrate_production_research/MD/project_sop.md:1)
- [MD/micom_practices.md](/Users/taknev/Desktop/microbiome_butyrate_production_research/MD/micom_practices.md:1)

## Core Research Questions

- Which species dominate growth in the baseline community model under COBRApy?
- When many species do not grow in community FBA, is that due to model failure, or because weighted/shared community optimization produces sparse winner-take-all solutions?
- Are the dominant or growing species associated with butyrate-related metabolism?
- If yes, through which butyrate biosynthesis routes or related pathway steps do they contribute?
- Do age-bin-specific abundance weights change which species dominate community growth?
- In older age bins, do the dominant modeled species align with the age-enriched species reported in the octogenarian paper?
- Which species are associated with butyrate-related metabolism in younger age bins versus older age bins?
- For older age bins, is the evidence for butyrate production better seen from internal pathway flux, exchange with the shared environment, or both?

## Interpretation Notes

- Many organisms failing to grow in community FBA should not automatically be interpreted as broken SBML files.
- If single-species simulations show all models can grow individually, sparse community optima may instead reflect the structure of weighted LP-based community optimization.
- "Species involved in butyrate production" should be phrased more carefully as species showing butyrate-related pathway or exchange evidence.
- The biological framing may include multiple known butyrate routes, but the computational workflow may only test a narrower curated subset of reactions or exchange signals.

## Project Files

- `Scripts/`: top-level home for Python and R analysis code.
- `Scripts/data_processing/`: upstream preprocessing scripts that generate modeling-ready abundance inputs.
- `Scripts/modelling/`: core COBRApy and MICOM analysis entrypoints plus reusable helper modules.
- `Scripts/exploration/`: Python plotting and exploratory visualization scripts.
- `Scripts/plotting_r/`: R plotting scripts for COBRApy and MICOM outputs.
- `Results/`: top-level home for generated tables, figures, and build reports.
- `Results/cobrapy_fba/`: COBRApy outputs grouped into `tables/`, `figures/`, and `reports/`.
- `Results/micom_fba/`: MICOM outputs grouped into `tables/`, `figures/`, and `reports/`.
- `Results/subject_level_fba/`: reserved results space for future subject-level FBA analyses.
- `Models/vmh_agora1.03_sbml/`: legacy AGORA 1.03 SBML XML models for the selected microbial species.
- `Models/vmh_agora2_sbml/`: primary VMH AGORA2 SBML XML models for the selected microbial species.
- `Medium_files/diet.csv`: diet or medium constraints used for modeling.
- `Suplementary_Data/`: supplementary paper-derived metadata and subject-level taxonomic abundance workbooks.
- `Suplementary_Data/processed_data/`: processed subject-level and age-bin abundance tables generated for downstream modeling.
- `Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py`: prepares subject-level and all-cohort age-bin median abundance inputs for the 10 modeled AGORA2 species.
- `Scripts/modelling/00_baseline_modeling_utils.py`: shared helper functions for the baseline AGORA2 analyses.
- `Scripts/modelling/01_single_species_growth_and_butyrate.py`: single-species AGORA2 baseline growth and butyrate screen under both diets.
- `Results/cobrapy_fba/tables/01_single_species_growth_and_butyrate_by_diet.csv`: single-species growth summary by diet.
- `Results/cobrapy_fba/tables/01_single_species_butyrate_reactions_by_diet.csv`: per-species butyrate-related reaction flux summary by diet.
- `Scripts/modelling/02_community_shared_environment.py`: 10-species unweighted shared-environment community baseline under both diets.
- `Results/cobrapy_fba/tables/02_community_growth_summary_by_diet.csv`: community-level growth summary by diet.
- `Results/cobrapy_fba/tables/02_community_species_growth_by_diet.csv`: per-species community biomass flux summary by diet.
- `Results/cobrapy_fba/reports/02_community_model_build_report.txt`: build and medium-matching report for the shared-environment model.
- `Scripts/modelling/03_agebin_weighted_community.py`: age-bin-weighted shared-environment community modeling across all pooled age bins and both diets.
- `Results/cobrapy_fba/tables/03_agebin_community_growth_summary_by_diet.csv`: one row per age bin and diet summarizing weighted community behavior.
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv`: per-species weighted community biomass flux by age bin and diet.
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet_wide.csv`: wide-format per-species biomass flux across age bins for each diet.
- `Results/cobrapy_fba/reports/03_agebin_community_model_build_report.txt`: build, validation, and medium-matching report for the age-bin-weighted community runs.
- `Scripts/modelling/00_micom_utils.py`: shared MICOM-specific helper functions for baseline and age-bin community workflows.
- `Scripts/modelling/04_micom_baseline_community.py`: MICOM-based baseline community modeling for the same 10 AGORA2 species under both diets.
- `Results/micom_fba/tables/04_micom_community_growth_summary_by_diet.csv`: MICOM community-level growth summary by diet.
- `Results/micom_fba/tables/04_micom_taxon_growth_by_diet.csv`: MICOM per-taxon growth summary by diet.
- `Results/micom_fba/reports/04_micom_model_build_report.txt`: MICOM build and diet-mapping report for the baseline community run.
- `Scripts/modelling/05_micom_agebin_weighted_community.py`: MICOM age-bin community modeling using age-specific abundance weights under both diets.
- `Results/micom_fba/tables/05_micom_agebin_community_growth_summary_by_diet.csv`: MICOM age-bin community-level growth summary by diet.
- `Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv`: MICOM age-bin per-taxon growth summary by diet.
- `Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet_wide.csv`: wide-format MICOM per-taxon growth rates across age bins.
- `Results/micom_fba/reports/05_micom_agebin_model_build_report.txt`: MICOM age-bin build and diet-mapping report.
- `Scripts/data_processing/02_prepare_sg90_subject_level_micom_inputs.py`: rebuilds the SG90 subject-level 10-species MICOM input tables directly from the raw metadata and raw abundance workbook, including subjects above age 90.
- `Suplementary_Data/processed_data/subject_level_micom_sg90/`: SG90-only subject-level MICOM input tables, QC tables, and missing-subject audit files.
- `Scripts/modelling/06_micom_subject_level_sg90.py`: subject-level MICOM runner for SG90 using the recovered raw-workbook subject set.
- `Results/subject_level_fba/tables/06_sg90_subject_community_growth_summary_by_diet.csv`: SG90 subject-level MICOM community growth summary by diet.
- `Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet.csv`: SG90 per-subject, per-taxon MICOM growth summary by diet.
- `Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet_wide.csv`: wide-format SG90 subject-level MICOM taxon growth table.
- `Results/subject_level_fba/reports/06_sg90_subject_level_micom_build_report.txt`: SG90 subject-level MICOM build and solve report.
- `Scripts/modelling/07_summarize_sg90_subject_level_micom_growth.py`: summarizes SG90 subject-level MICOM growth and dominance patterns by age group.
- `MD/`: project markdown notes and references except for this README.
- `PDF/`: project PDF references.

## Operating Standard

The official workflow standard for this repository is:

1. prepare processed abundance inputs
2. confirm single-species baseline behavior
3. run the COBRApy baseline community
4. run the COBRApy age-bin weighted community
5. run the MICOM baseline community
6. run the MICOM age-bin weighted community
7. rebuild SG90 raw subject inputs and run SG90 subject-level MICOM

The detailed SOP and MICOM-specific practice note live in:

- [MD/project_sop.md](/Users/taknev/Desktop/microbiome_butyrate_production_research/MD/project_sop.md:1)
- [MD/micom_practices.md](/Users/taknev/Desktop/microbiome_butyrate_production_research/MD/micom_practices.md:1)

These documents define:

- required inputs
- QC gates
- build-report expectations
- interpretation guardrails
- the MICOM-specific habits that should remain stable across future analyses

## COBRApy In This Project

COBRApy is the Python package used here to load SBML metabolic models, define media constraints, and run constraint-based analyses such as flux balance analysis. It provides model I/O plus standard COBRA workflows including optimization, flux variability analysis, and related metabolic simulation tasks. In this project, it is the core tool for reading the species models and testing growth and butyrate-related metabolic behavior under shared community conditions.

## Community Model Baseline

The current baseline community model in this repo uses a connector-based shared-environment construction:

- each species keeps its own internal and extracellular metabolites,
- each species extracellular metabolite connects to a shared community metabolite pool through explicit connector reactions,
- diet uptake is applied at the community-exchange level,
- the objective is the sum of the species biomass reactions.

This baseline is intended to answer the first question:

- which species achieve nonzero growth in community FBA under the two diets.

Butyrate interpretation is treated as a separate follow-up analysis layer on top of that baseline, not as part of script `01`.

## Age-Bin Input Preparation

Before any age-bin-weighted community modeling, the supplementary workbook inputs can be converted into AGORA2-ready abundance tables using:

- `Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py`

This script reads:

- `Suplementary_Data/Metadata_by_cohort.xlsx`
- `Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx`

and writes processed outputs under:

- `Suplementary_Data/processed_data/`

The most directly useful pooled age-bin outputs are:

- `allcohort_agebin_median_abundance_10_species.csv`
- `allcohort_agebin_median_abundance_10_species_wide.csv`

These tables provide median abundance and normalized abundance weights for the 10 modeled species across age bins `21_40`, `41_60`, `61_70`, `71_80`, and `81_90`.

## Age-Bin Weighted Community Modeling

The pooled age-bin abundance table is used directly by:

- `Scripts/modelling/03_agebin_weighted_community.py`

This script:

- reads `Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv`
- builds the same shared-environment AGORA2 community used in the baseline analysis
- replaces the unweighted biomass objective with age-bin-specific `normalized_weight` coefficients
- runs all five age bins under both `western` and `high_fiber`
- writes long and wide species-level growth outputs plus a community summary table

The key outputs are:

- `Results/cobrapy_fba/tables/03_agebin_community_growth_summary_by_diet.csv`
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv`
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet_wide.csv`

## MICOM Baseline Community Modeling

The MICOM baseline branch is implemented in:

- `Scripts/modelling/04_micom_baseline_community.py`

This script:

- reads the same 10 AGORA2 SBML models used by the COBRApy baseline,
- reads the same `western` and `high_fiber` diets from `Medium_files/diet.csv`,
- builds a MICOM community from a taxonomy table containing `id`, `file`, and equal `abundance`,
- translates diet metabolite IDs into MICOM community exchange IDs,
- runs MICOM `cooperative_tradeoff()` once per diet,
- writes community-level and taxon-level MICOM growth outputs plus a plain-text build report.

The key outputs are:

- `Results/micom_fba/tables/04_micom_community_growth_summary_by_diet.csv`
- `Results/micom_fba/tables/04_micom_taxon_growth_by_diet.csv`
- `Results/micom_fba/reports/04_micom_model_build_report.txt`

## MICOM Age-Bin Community Modeling

The MICOM age-bin branch is implemented in:

- `Scripts/modelling/05_micom_agebin_weighted_community.py`

This script:

- reads `Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv`,
- builds one MICOM community per age group using `normalized_weight` as abundance,
- reads the same `western` and `high_fiber` diets from `Medium_files/diet.csv`,
- runs MICOM `cooperative_tradeoff()` for each age group and diet combination,
- writes age-bin community-level and taxon-level MICOM growth outputs plus a build report.

The key outputs are:

- `Results/micom_fba/tables/05_micom_agebin_community_growth_summary_by_diet.csv`
- `Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv`
- `Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet_wide.csv`
- `Results/micom_fba/reports/05_micom_agebin_model_build_report.txt`

## Next Step

The next operational upgrades that would make this even stronger are:

- add a pinned environment file for reproducible package versions
- add one canonical run script for the full workflow
- add a dated run log for official analyses
- version output tables when protocol settings change
