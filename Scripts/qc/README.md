# QC Scripts

This folder is the working home for quality-control scripts and small chart-preparation utilities that do not belong inside the core modelling pipeline.

Use this folder for:

- input validation checks
- output sanity checks
- PCA or outlier review helpers
- chart-ready summary-table builders

Keep these conventions:

- read canonical inputs from `Suplementary_Data/processed_data/` or `Results/`
- write machine-readable QC tables to `Results/qc/tables/`
- write narrative QC notes to `Results/qc/reports/`
- write draft or final QC charts to `Results/qc/figures/`
- keep one narrow purpose per script

If a QC script becomes part of the official repeatable workflow, promote it into the numbered pipeline and document that change in the README and SOP.
