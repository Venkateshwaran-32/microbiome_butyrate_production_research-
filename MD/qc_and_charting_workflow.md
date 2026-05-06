# QC And Charting Workflow

## Purpose

This note defines a simple working convention for repository tasks that are mainly about:

- QC
- exploratory review
- presentation charts

These tasks often sit near the official modelling workflow, but they should not overwrite or blur the canonical pipeline outputs.

## Folder Convention

- put QC-oriented scripts in `Scripts/qc/`
- put QC tables in `Results/qc/tables/`
- put QC charts in `Results/qc/figures/`
- put QC writeups, audit notes, and run summaries in `Results/qc/reports/`

## Intended Use

Use this lane for work such as:

- checking whether subject-level runs contain outlier flux values
- reviewing solver-status subsets before interpretation
- creating PCA diagnostics
- generating chart-ready summary tables for talks or notes
- comparing draft visualizations before deciding which one becomes canonical

## Guardrails

- treat `Results/cobrapy_fba/`, `Results/micom_fba/`, and `Results/subject_level_fba/` as canonical method-specific result stores
- treat `Results/qc/` as the shared staging area for cross-cutting QC and charting work
- do not move official pipeline outputs into `Results/qc/`; instead, derive QC summaries from them
- name files so the source branch is obvious, for example `subject_level_flux_qc_*.csv` or `micom_agebin_chart_*.png`
- if a QC chart becomes part of the official repo story, either copy the finalized artifact into the relevant canonical results folder or document why it remains in `Results/qc/`

## Relationship To The SOP

The SOP still defines the official modelling order and acceptance gates.

This QC/charting lane is a companion workspace for:

- validating outputs
- summarizing outputs
- preparing figures without changing the underlying pipeline
