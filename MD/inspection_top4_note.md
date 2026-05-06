# Inspection Top 4

This note documents the focused inspection branch for the highest-flux subjects from script 8.

## Why these 4 subjects

The script 8 high-fiber MICOM pFBA run produced a small set of subjects with unusually large exported flux values. The top 4 by maximum absolute flux were:

- `MBS1232`
- `MBS1529`
- `MBS1262`
- `MBS1255`

These four dominate the extreme tail and are the first-pass targets for artifact inspection.

## What script 8 did

The source run was `Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py`.

That workflow used:

- diet: `high_fiber`
- `fluxes=True`
- `pfba=True`
- subject-level all-cohort 10-species MICOM communities

## Main comparison

The main diagnostic comparison on this branch is:

- original script 8 outputs (`pfba=True`)
- matched rerun on the same 4 subjects with `pfba=False`

If the extreme flux magnitudes collapse without pFBA, the leading explanation is a pFBA-driven degeneracy or loop artifact. If they persist, the next suspects are model structure, exchange mapping, or reaction-bound issues.
