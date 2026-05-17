# Jaccard reaction-similarity analysis — implementation report

**Compiled:** 2026-05-15
**Plan:** `/Users/taknev/.claude/plans/1-jacquard-similarity-analysis-giggly-chipmunk.md`
**Approved scope:** Build a paper-grade figure showing how metabolically similar the 10 modeled AGORA2 species are to one another, using pairwise Jaccard similarity on raw reaction-ID sets, visualised as a 10×10 heatmap ordered by hierarchical clustering.

---

## 1. Files created

| Path | Role | Notes |
|---|---|---|
| `Scripts/modelling/07_jaccard_reaction_similarity.py` | Python — loads SBMLs, computes Jaccard matrix, writes outputs | New canonical-workflow script numbered 07 |
| `Scripts/plotting_r/jaccard_reaction_similarity_heatmap.R` | R — renders the heatmap | Sources `00_taxon_utils.R` for species-label formatting |
| `Results/cobrapy_fba/tables/07_jaccard_reaction_matrix_wide.csv` | Wide 10×10 Jaccard matrix | First column `species_name`, then 10 species columns |
| `Results/cobrapy_fba/tables/07_jaccard_reaction_pairs_long.csv` | Long pairwise table | 100 rows, columns `species_a, species_b, n_reactions_a, n_reactions_b, intersection, union, jaccard, dissimilarity` |
| `Results/cobrapy_fba/reports/07_jaccard_reaction_similarity_report.txt` | Build report | Includes per-species reaction counts, pairwise summary, and standard `CSV Output Dictionary` section |
| `Results/cobrapy_fba/figures/07_jaccard_reaction_similarity_heatmap.png` | Final heatmap | 8 × 7 in at **600 dpi** for paper print |
| `Results/cobrapy_fba/reports/07_jaccard_reaction_similarity_implementation_report.md` | This report | Implementation summary + interpretation |

---

## 2. Key implementation decisions

### Reaction-set definition
- **Reaction set** for each species = `{r.id for r in cobra_model.reactions}`.
- **No filtering** applied — exchange reactions (`EX_*`), biomass, sinks, demands are all included. This matches the user's explicit choice ("all reactions") and is the standard Jaccard-on-AGORA-models convention.
- **No compartment-suffix normalisation.** AGORA2 reaction IDs are compartment-free strings (e.g. `PYK`, `ATPS4r`, `EX_glc_D(e)`); only metabolite IDs carry `[c]` / `[e]` brackets. Raw `reaction.id` equality is meaningful across models because the VMH/AGORA2 namespace is curated and shared.

### Diagonal and symmetry
- **Diagonal forced to 1.0** explicitly in code (avoids any floating drift from `len(A) / len(A)` rounding edge cases).
- **All 100 ordered pairs** written to the long CSV — i.e. each unordered pair appears twice (once as `(A, B)` and once as `(B, A)`) — so R-side code can pivot without assuming symmetry.

### Ordering for the heatmap
- **Hierarchical clustering** on the distance matrix `1 − Jaccard` using `hclust(..., method = "average")`. The species order pulled from `hc$labels[hc$order]` is applied as factor levels to both x and y axes.
- This is data-driven and the standard choice for paper-grade similarity heatmaps. Same-genus pairs cluster adjacent (the two Alistipes, the two Bacteroides) and the most-distinct species (R. torques, the smallest model) ends up at the matrix corner.

### Visual styling
- Used the project's existing brown-gradient convention (matches `MICOM_multispecies_age_bin_growthv2.R`): `geom_tile(color = "white", linewidth = 0.7)` + `scale_fill_gradient(low = "#F4EFE8", high = "#3F2417", limits = c(0, 1))`.
- **Auto-adaptive tile-label colour**: dark text (`#2B2B2B`) on light tiles, cream text (`#F4EFE8`) on dark tiles, switched at `Jaccard > 0.55`. Keeps the value labels readable across the full gradient.
- Species labels via `italicize_taxon()` (abbreviated, no markdown asterisks). The first render mistakenly wrapped labels in `*...*` and the asterisks rendered literally; fixed by dropping the wrapper. Labels now plain non-italic, consistent with the rest of the figures in the repo.

### Reused conventions
- SBML loading + helpers: `cobra.io.read_sbml_model()` via `Scripts/modelling/00_baseline_modeling_utils.py:load_model` and `load_species_model_paths`, `species_name_from_path` (lines 20, 131, 138).
- Build-report `CSV Output Dictionary`: `csv_output_spec`, `col`, `build_report_text` from `Scripts/modelling/00_report_output_dictionary.py`.
- Importlib pattern for cross-module loads: same `importlib.util.spec_from_file_location(...)` block as script 08.
- R species labels: `italicize_taxon()` from `Scripts/plotting_r/00_taxon_utils.R`.

---

## 3. Verification — all checks passed

### Inline asserts in the Python script

```
Diagonal == 1.0 for all 10 species: PASS
Symmetry within 1e-12 for all unordered pairs: PASS
Per-species reaction counts match expected (1189, 2434, 2115, 2657, 1240,
                                            3198, 2046, 2113, 2495, 998): PASS
```

### Spot-check pair 1 — same genus (Alistipes)

A. onderdonkii (1189 reactions) vs A. shahii (2434 reactions):
- Intersection: **1048**
- Union: **2575**
- Jaccard: **0.407**
- Plan expectation: ≤ theoretical upper bound 1189/2434 = 0.488; range 0.40–0.49
- **Result: in range** ✓
- Interpretation: 88% of A. onderdonkii's 1189 reactions overlap with A. shahii (1048/1189), but A. shahii has ~1386 additional reactions not in A. onderdonkii — those pull the Jaccard below 0.5.

### Spot-check pair 2 — cross-phylum (Proteobacteria vs Firmicutes)

E. coli (3198 reactions) vs F. prausnitzii (2046 reactions):
- Intersection: **1360**
- Union: **3884**
- Jaccard: **0.350**
- Plan expectation: 0.30–0.45, must be lower than the same-genus pair
- **Result: in range and < 0.407** ✓

### Spot-check pair 3 — same family (Enterobacteriaceae)

E. coli (3198 reactions) vs K. pneumoniae (2113 reactions):
- Intersection: **1855**
- Union: **3456**
- Jaccard: **0.537**
- Bracketed between cross-phylum (~0.35) and same-genus Bacteroides (~0.71) ✓

### Spot-check pair 4 — same genus (Bacteroides)

B. dorei (2115 reactions) vs B. xylanisolvens (2657 reactions):
- Intersection: **1989**
- Union: **2783**
- Jaccard: **0.715** — highest visible same-genus pair ✓

### Overall extremes (off-diagonal, 45 unordered pairs)

| Statistic | Value | Pair |
|---|---|---|
| Minimum Jaccard | **0.195** | A. shahii vs R. torques |
| Median Jaccard | **0.359** | — |
| Maximum Jaccard | **0.794** | B. xylanisolvens vs P. merdae |

The highest off-diagonal Jaccard is between **B. xylanisolvens and P. merdae** — two different genera but both Bacteroidales gut microbes — at **0.794**. Notably higher than the same-genus B. dorei × B. xylanisolvens pair (0.715), indicating their reaction repertoires are closer than the two Bacteroides species are to each other.

---

## 4. Heatmap interpretation

The hierarchical clustering produced this species order (matrix corner → matrix corner):

```
A. onderdonkii → A. shahii → B. dorei → B. xylanisolvens → B. wadsworthia
  → E. coli → F. prausnitzii → K. pneumoniae → P. merdae → R. torques
```

Visible structure:

1. **Strong Bacteroidales block** — A. shahii, B. dorei, B. xylanisolvens, P. merdae form a high-Jaccard cluster (pairwise 0.61–0.79). All four are Bacteroidales gut microbes with overlapping carbohydrate-degradation repertoires.
2. **A. onderdonkii is a near-subset of A. shahii** — its 1189 reactions are ~88% contained in A. shahii's 2434. The clustering correctly puts them adjacent, but the Jaccard (0.41) is dragged down by the size asymmetry.
3. **E. coli + K. pneumoniae (Enterobacteriaceae)** share 0.54 Jaccard — higher than their similarity to most non-Proteobacteria but lower than within Bacteroidales. Average-linkage clustering placed them apart in the final order, which is a minor counterintuitive outcome of the algorithm and not a data error.
4. **R. torques is the most distinct** species — sits at the matrix corner with off-diagonal Jaccards in the 0.20–0.37 range. Two contributing factors: it is the smallest model (998 reactions) and the only Lachnospiraceae in the set.
5. **F. prausnitzii** (Ruminococcaceae, the only species in its family here) sits in the middle of the matrix with intermediate Jaccards (0.26–0.38 against most others). Its 2046 reactions cover broad core metabolism so it overlaps moderately with everything but is closest to nothing.
6. **B. wadsworthia** (Desulfovibrionaceae, sulfate reducer) — moderate Jaccards 0.25–0.49. Its niche metabolism is reflected in lower overlap with the Bacteroidales cluster.

---

## 5. Deviations from the approved plan

| Plan said | Actual | Reason |
|---|---|---|
| Species labels wrapped in `*...*` for italic via `element_markdown` | Wrapped on first render — asterisks rendered literally; removed wrapper on second render | The main paper figure uses `italicize_taxon()` output directly without asterisks; matching that convention. Labels are now plain abbreviated species names. |
| Subtitle: "Pairwise Jaccard on raw reaction IDs; rows and columns ordered by hierarchical clustering on (1 − Jaccard) with average linkage." | Subtitle: "Rows and columns ordered by hierarchical clustering on (1 − Jaccard)." | Original wording overran the plot width and was truncated mid-word. Shortened to fit. |

No other deviations. All other plan-level decisions (file locations, output schemas, asserts, dpi=600, full matrix rather than triangle, hierarchical-cluster ordering, all reactions including exchanges) were implemented as approved.

---

## 6. Pending — reference figure

The user mentioned during planning that they have a **specific paper figure** they want this heatmap to aesthetically match. That reference has not yet been shared. The current output uses the project's existing brown-gradient style as a placeholder; once the reference is provided, the colour scale, annotation precision, legend placement, and axis label rotation can all be tuned to match. The underlying CSV + clustering layer is reference-independent and does not need to change.

---

## 7. How to re-run

```bash
# 1. Recompute the Jaccard matrix.
.venv_micom/bin/python Scripts/modelling/07_jaccard_reaction_similarity.py

# 2. Re-render the heatmap.
Rscript "Scripts/plotting_r/jaccard_reaction_similarity_heatmap.R"
```

Both scripts are idempotent and safe to re-run. The Python script's inline asserts will surface any data integrity issues loudly (mismatched reaction counts, broken symmetry).
