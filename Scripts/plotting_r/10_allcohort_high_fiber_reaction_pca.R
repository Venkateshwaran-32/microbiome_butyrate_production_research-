args <- commandArgs(trailingOnly = FALSE)
file_arg <- "--file="
script_path <- sub(file_arg, "", args[grep(file_arg, args)])
if (length(script_path) == 1 && nzchar(script_path)) {
  setwd(normalizePath(file.path(dirname(script_path), "../..")))
}

if (!requireNamespace("pacman", quietly = TRUE)) {
  stop("The pacman package is required to run this PCA script.")
}

pacman::p_load(tidyverse)
rm(list = ls())
source(file.path("Scripts", "plotting_r", "00_report_output_dictionary.R"))

tables_dir <- "Results/subject_level_fba/tables"
reports_dir <- "Results/subject_level_fba/reports"
figures_dir <- "Results/subject_level_fba/figures"

subject_set_specs <- tribble(
  ~subject_set, ~matrix_path, ~metadata_path,
  "all516",
  file.path(tables_dir, "09_allcohort_high_fiber_subject_by_reaction_matrix_all516.csv"),
  file.path(tables_dir, "09_allcohort_high_fiber_subject_metadata_all516.csv"),
  "optimal414",
  file.path(tables_dir, "09_allcohort_high_fiber_subject_by_reaction_matrix_optimal414.csv"),
  file.path(tables_dir, "09_allcohort_high_fiber_subject_metadata_optimal414.csv")
)

contribution_path <- file.path(
  tables_dir,
  "09_allcohort_high_fiber_reaction_taxon_contribution_by_subject_set.csv"
)

scores_output <- file.path(tables_dir, "10_allcohort_high_fiber_reaction_pca_scores.csv")
variance_output <- file.path(tables_dir, "10_allcohort_high_fiber_reaction_pca_explained_variance.csv")
loadings_output <- file.path(tables_dir, "10_allcohort_high_fiber_reaction_pca_loadings.csv")
top_loading_output <- file.path(tables_dir, "10_allcohort_high_fiber_reaction_top_loading_summary.csv")
top_reaction_contribution_output <- file.path(
  tables_dir,
  "10_allcohort_high_fiber_taxon_contribution_top_loading_reactions.csv"
)
lys_but_contribution_output <- file.path(
  tables_dir,
  "10_allcohort_high_fiber_taxon_contribution_lysine_butyrate_reactions.csv"
)
report_output <- file.path(reports_dir, "10_allcohort_high_fiber_reaction_pca_report.txt")

scree_plot_output <- file.path(figures_dir, "10_allcohort_high_fiber_reaction_pca_scree.png")
cohort_plot_output <- file.path(figures_dir, "10_allcohort_high_fiber_reaction_pca_scores_by_cohort.png")
age_plot_output <- file.path(figures_dir, "10_allcohort_high_fiber_reaction_pca_scores_by_age_group.png")
solver_plot_output <- file.path(figures_dir, "10_allcohort_high_fiber_reaction_pca_scores_by_solver_status.png")

top_loading_count <- 20
target_pcs <- c("PC1", "PC2", "PC3")
csv_output_specs <- list(
  list(
    path = scores_output,
    row_grain = "one row per subject_set x subject_id",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "subject_id", meaning = "Subject identifier carried through from the PCA input matrix."),
      list(name = "PC1", meaning = "Principal component 1 score for this subject."),
      list(name = "PC2", meaning = "Principal component 2 score for this subject."),
      list(name = "PC3", meaning = "Principal component 3 score for this subject."),
      list(name = "PC4", meaning = "Principal component 4 score for this subject."),
      list(name = "PC5", meaning = "Principal component 5 score for this subject."),
      list(name = "PC6", meaning = "Principal component 6 score for this subject."),
      list(name = "PC7", meaning = "Principal component 7 score for this subject."),
      list(name = "PC8", meaning = "Principal component 8 score for this subject."),
      list(name = "PC9", meaning = "Principal component 9 score for this subject."),
      list(name = "PC10", meaning = "Principal component 10 score for this subject."),
      list(name = "cohort", meaning = "Cohort label carried through from the subject metadata."),
      list(name = "age_years", meaning = "Subject age in years from the metadata table."),
      list(name = "age_group", meaning = "Age-bin label assigned from the metadata age."),
      list(name = "solver_status", meaning = "Solver status carried through from the 08 all-cohort MICOM summary table."),
      list(name = "community_growth_rate", meaning = "Community growth rate carried through from the 08 all-cohort MICOM summary table.")
    )
  ),
  list(
    path = variance_output,
    row_grain = "one row per subject_set x principal component",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "pc", meaning = "Principal component label."),
      list(
        name = "explained_variance_fraction",
        meaning = "Fraction of total PCA variance explained by this principal component.",
        formula = "explained_variance_fraction = sdev^2 / sum(sdev^2 across all PCs within subject_set)"
      ),
      list(
        name = "cumulative_explained_variance",
        meaning = "Cumulative explained variance through this principal component.",
        formula = "cumulative_explained_variance = cumulative sum of explained_variance_fraction ordered by PC number within subject_set"
      )
    )
  ),
  list(
    path = loadings_output,
    row_grain = "one row per subject_set x reaction_id x principal component",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "reaction_id", meaning = "Collapsed reaction identifier from the PCA feature matrix."),
      list(name = "pc", meaning = "Principal component label."),
      list(name = "loading", meaning = "Signed PCA loading for this reaction on the selected component."),
      list(name = "abs_loading", meaning = "Absolute PCA loading magnitude for this reaction on the selected component.", formula = "abs_loading = abs(loading)")
    )
  ),
  list(
    path = top_loading_output,
    row_grain = "one row per subject_set x principal component x direction x rank_within_direction",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "pc", meaning = "Principal component label."),
      list(name = "reaction_id", meaning = "Collapsed reaction identifier selected as a top positive or top negative loading."),
      list(name = "loading", meaning = "Signed PCA loading for this reaction on the selected component."),
      list(name = "abs_loading", meaning = "Absolute PCA loading magnitude for this reaction.", formula = "abs_loading = abs(loading)"),
      list(
        name = "explained_variance_fraction",
        meaning = "Fraction of total PCA variance explained by this principal component.",
        formula = "explained_variance_fraction = sdev^2 / sum(sdev^2 across all PCs within subject_set)"
      ),
      list(name = "direction", meaning = "Whether the reaction was selected from the positive or negative loading tail."),
      list(
        name = "rank_within_direction",
        meaning = "Rank within the positive or negative loading tail for the selected principal component.",
        formula = "rank_within_direction = rank after sorting by loading descending for positive rows or ascending for negative rows within subject_set + pc"
      )
    )
  ),
  list(
    path = top_reaction_contribution_output,
    row_grain = "one row per subject_set x reaction_id x taxon_id for reactions selected from top PCA loadings",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "reaction_id", meaning = "Collapsed reaction identifier selected from the top-loading PCA reactions."),
      list(name = "reaction_token_group", meaning = "Semicolon-separated token groups matched from the reaction ID for convenience filtering."),
      list(name = "taxon_id", meaning = "MICOM taxon/model identifier contributing flux to this reaction."),
      list(name = "species_name", meaning = "Species label mapped onto this model taxon."),
      list(name = "paper_taxon", meaning = "Original paper taxon label mapped onto this model species."),
      list(name = "n_subjects_in_set", meaning = "Total number of subjects in the selected subject set."),
      list(name = "n_subjects_with_flux", meaning = "Number of subjects in the set where this taxon carried nonzero flux for this reaction."),
      list(name = "fraction_subjects_with_flux", meaning = "Prevalence of this taxon-reaction flux within the selected subject set.", formula = "fraction_subjects_with_flux = n_subjects_with_flux / n_subjects_in_set"),
      list(name = "median_signed_flux", meaning = "Median signed taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
      list(name = "median_abs_flux", meaning = "Median absolute taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
      list(name = "total_abs_flux", meaning = "Total absolute flux contributed by this taxon across all subjects in the selected set for this reaction.", formula = "total_abs_flux = sum(abs(flux) across all exported subject rows within subject_set + reaction_id + taxon_id)"),
      list(name = "fraction_of_total_abs_flux", meaning = "Share of the total absolute reaction flux carried by this taxon within the selected subject set.", formula = "fraction_of_total_abs_flux = total_abs_flux / sum(total_abs_flux across all taxon_id within subject_set + reaction_id)"),
      list(name = "selected_from_pcs", meaning = "Semicolon-separated list of principal components that selected this reaction into the top-loading set."),
      list(name = "selected_directions", meaning = "Semicolon-separated list of loading directions that selected this reaction into the top-loading set."),
      list(name = "max_abs_loading", meaning = "Largest absolute loading observed for this reaction among the selected principal components.", formula = "max_abs_loading = max(abs_loading across selected PC rows for subject_set + reaction_id)")
    )
  ),
  list(
    path = lys_but_contribution_output,
    row_grain = "one row per subject_set x reaction_id x taxon_id for token-matched lysine or butyrate reactions",
    columns = list(
      list(name = "subject_set", meaning = "Subject-set label used for the PCA, either all516 or optimal414."),
      list(name = "reaction_id", meaning = "Collapsed reaction identifier matched by the lysine/butyrate token filter."),
      list(name = "reaction_token_group", meaning = "Semicolon-separated token groups matched from the reaction ID."),
      list(name = "taxon_id", meaning = "MICOM taxon/model identifier contributing flux to this reaction."),
      list(name = "species_name", meaning = "Species label mapped onto this model taxon."),
      list(name = "paper_taxon", meaning = "Original paper taxon label mapped onto this model species."),
      list(name = "n_subjects_in_set", meaning = "Total number of subjects in the selected subject set."),
      list(name = "n_subjects_with_flux", meaning = "Number of subjects in the set where this taxon carried nonzero flux for this reaction."),
      list(name = "fraction_subjects_with_flux", meaning = "Prevalence of this taxon-reaction flux within the selected subject set.", formula = "fraction_subjects_with_flux = n_subjects_with_flux / n_subjects_in_set"),
      list(name = "median_signed_flux", meaning = "Median signed taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
      list(name = "median_abs_flux", meaning = "Median absolute taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
      list(name = "total_abs_flux", meaning = "Total absolute flux contributed by this taxon across all subjects in the selected set for this reaction.", formula = "total_abs_flux = sum(abs(flux) across all exported subject rows within subject_set + reaction_id + taxon_id)"),
      list(name = "fraction_of_total_abs_flux", meaning = "Share of the total absolute reaction flux carried by this taxon within the selected subject set.", formula = "fraction_of_total_abs_flux = total_abs_flux / sum(total_abs_flux across all taxon_id within subject_set + reaction_id)")
    )
  )
)

dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(reports_dir, recursive = TRUE, showWarnings = FALSE)

run_subject_set_pca <- function(subject_set, matrix_path, metadata_path) {
  matrix_df <- read_csv(matrix_path, show_col_types = FALSE)
  metadata_df <- read_csv(metadata_path, show_col_types = FALSE)

  subject_ids <- matrix_df$subject_id
  flux_matrix <- matrix_df %>%
    select(-subject_id) %>%
    as.matrix()
  rownames(flux_matrix) <- subject_ids
  storage.mode(flux_matrix) <- "double"

  transformed_matrix <- asinh(flux_matrix)
  feature_sd <- apply(transformed_matrix, 2, sd)
  keep_features <- is.finite(feature_sd) & feature_sd > 0
  filtered_matrix <- transformed_matrix[, keep_features, drop = FALSE]

  pca_fit <- prcomp(filtered_matrix, center = TRUE, scale. = TRUE)

  score_pc_count <- min(10, ncol(pca_fit$x))
  scores_df <- as_tibble(
    pca_fit$x[, seq_len(score_pc_count), drop = FALSE],
    rownames = "subject_id"
  ) %>%
    left_join(metadata_df, by = "subject_id") %>%
    mutate(subject_set = subject_set) %>%
    relocate(subject_set, subject_id)

  variance_df <- tibble(
    subject_set = subject_set,
    pc = paste0("PC", seq_along(pca_fit$sdev)),
    explained_variance_fraction = (pca_fit$sdev^2) / sum(pca_fit$sdev^2)
  ) %>%
    mutate(cumulative_explained_variance = cumsum(explained_variance_fraction))

  loadings_df <- as.data.frame(pca_fit$rotation) %>%
    rownames_to_column("reaction_id") %>%
    pivot_longer(
      cols = -reaction_id,
      names_to = "pc",
      values_to = "loading"
    ) %>%
    mutate(
      subject_set = subject_set,
      abs_loading = abs(loading)
    ) %>%
    relocate(subject_set, reaction_id, pc, loading, abs_loading)

  target_pc_values <- intersect(target_pcs, unique(loadings_df$pc))
  top_loading_df <- loadings_df %>%
    filter(pc %in% target_pc_values) %>%
    left_join(
      variance_df %>% select(subject_set, pc, explained_variance_fraction),
      by = c("subject_set", "pc")
    ) %>%
    group_by(subject_set, pc) %>%
    group_modify(
      ~ {
        positive <- .x %>%
          arrange(desc(loading), reaction_id) %>%
          slice_head(n = top_loading_count) %>%
          mutate(direction = "positive", rank_within_direction = row_number())
        negative <- .x %>%
          arrange(loading, reaction_id) %>%
          slice_head(n = top_loading_count) %>%
          mutate(direction = "negative", rank_within_direction = row_number())
        bind_rows(positive, negative)
      }
    ) %>%
    ungroup() %>%
    arrange(subject_set, pc, direction, rank_within_direction)

  list(
    scores = scores_df,
    variance = variance_df,
    loadings = loadings_df,
    top_loadings = top_loading_df,
    feature_count_before = ncol(flux_matrix),
    zero_variance_removed = sum(!keep_features),
    feature_count_after = ncol(filtered_matrix),
    subject_count = nrow(flux_matrix)
  )
}

subject_set_results <- pmap(
  subject_set_specs,
  ~ run_subject_set_pca(..1, ..2, ..3)
)
names(subject_set_results) <- subject_set_specs$subject_set

scores_df <- bind_rows(map(subject_set_results, "scores"))
variance_df <- bind_rows(map(subject_set_results, "variance"))
loadings_df <- bind_rows(map(subject_set_results, "loadings"))
top_loading_df <- bind_rows(map(subject_set_results, "top_loadings"))

contribution_df <- read_csv(contribution_path, show_col_types = FALSE)

top_reaction_selection <- top_loading_df %>%
  group_by(subject_set, reaction_id) %>%
  summarise(
    selected_from_pcs = paste(sort(unique(pc)), collapse = ";"),
    selected_directions = paste(sort(unique(direction)), collapse = ";"),
    max_abs_loading = max(abs_loading),
    .groups = "drop"
  )

top_reaction_contribution_df <- contribution_df %>%
  inner_join(top_reaction_selection, by = c("subject_set", "reaction_id")) %>%
  arrange(subject_set, reaction_id, desc(fraction_of_total_abs_flux), taxon_id)

lys_but_contribution_df <- contribution_df %>%
  filter(!is.na(reaction_token_group), reaction_token_group != "") %>%
  arrange(subject_set, reaction_token_group, reaction_id, desc(fraction_of_total_abs_flux), taxon_id)

write_csv(scores_df, scores_output)
write_csv(variance_df, variance_output)
write_csv(loadings_df, loadings_output)
write_csv(top_loading_df, top_loading_output)
write_csv(top_reaction_contribution_df, top_reaction_contribution_output)
write_csv(lys_but_contribution_df, lys_but_contribution_output)

scree_plot_df <- variance_df %>%
  group_by(subject_set) %>%
  slice_head(n = 10) %>%
  ungroup() %>%
  mutate(pc = factor(pc, levels = paste0("PC", seq_len(10))))

scree_plot <- ggplot(
  scree_plot_df,
  aes(x = pc, y = explained_variance_fraction, fill = subject_set)
) +
  geom_col(position = "dodge") +
  scale_fill_manual(values = c("all516" = "#A64B00", "optimal414" = "#1B7837")) +
  labs(
    x = NULL,
    y = "Explained variance fraction",
    title = "Reaction-level PCA scree plot",
    subtitle = "Main biological PCA uses the optimal414 subject set; all516 is shown as QC"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(color = "#2B2B2B"),
    axis.text.y = element_text(color = "#2B2B2B"),
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    legend.title = element_blank(),
    legend.position = "top"
  )

scores_plot_df <- scores_df %>%
  filter(!is.na(PC1), !is.na(PC2)) %>%
  mutate(
    age_group = factor(age_group, levels = c("21_40", "41_60", "61_70", "71_80", "81_90", "91_100")),
    solver_status = factor(solver_status, levels = c("optimal", "infeasible"))
  )

cohort_plot <- ggplot(
  scores_plot_df,
  aes(x = PC1, y = PC2, color = cohort)
) +
  geom_point(alpha = 0.8, size = 1.8) +
  facet_wrap(~ subject_set) +
  scale_color_manual(
    values = c("CRE" = "#8C510A", "SG90" = "#1B7837", "SPMP" = "#5B2A86", "T2D" = "#1F4E5F")
  ) +
  labs(
    title = "Reaction-level PCA scores by cohort",
    subtitle = "PC1 vs PC2 from reaction-only subject matrices",
    x = "PC1",
    y = "PC2"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right"
  )

age_plot <- ggplot(
  scores_plot_df,
  aes(x = PC1, y = PC2, color = age_group)
) +
  geom_point(alpha = 0.8, size = 1.8) +
  facet_wrap(~ subject_set) +
  scale_color_brewer(palette = "YlGnBu") +
  labs(
    title = "Reaction-level PCA scores by age group",
    subtitle = "PC1 vs PC2 from reaction-only subject matrices",
    x = "PC1",
    y = "PC2"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right"
  )

solver_plot <- ggplot(
  scores_plot_df,
  aes(x = PC1, y = PC2, color = solver_status)
) +
  geom_point(alpha = 0.8, size = 1.8) +
  facet_wrap(~ subject_set) +
  scale_color_manual(values = c("optimal" = "#1B7837", "infeasible" = "#A61E4D")) +
  labs(
    title = "Reaction-level PCA scores by solver status",
    subtitle = "The all516 PCA is mainly for QC to show solver-status structure",
    x = "PC1",
    y = "PC2"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right"
  )

ggsave(scree_plot_output, plot = scree_plot, width = 10, height = 6, dpi = 300)
ggsave(cohort_plot_output, plot = cohort_plot, width = 10, height = 6.5, dpi = 300)
ggsave(age_plot_output, plot = age_plot, width = 10, height = 6.5, dpi = 300)
ggsave(solver_plot_output, plot = solver_plot, width = 10, height = 6.5, dpi = 300)

report_lines <- c(
  "All-cohort high-fiber reaction PCA report",
  paste("Subject-by-reaction matrix (all516):", subject_set_specs$matrix_path[subject_set_specs$subject_set == "all516"]),
  paste("Subject-by-reaction matrix (optimal414):", subject_set_specs$matrix_path[subject_set_specs$subject_set == "optimal414"]),
  paste("Contribution summary input:", contribution_path),
  "",
  "PCA preprocessing",
  "- Medium rows were excluded upstream.",
  "- Repeated subject_id + reaction_id fluxes were collapsed with a signed sum across taxa.",
  "- Missing subject-reaction pairs were filled with 0.0 before PCA.",
  "- A signed asinh transform was applied before centering and scaling.",
  "- Zero-variance reactions were removed separately for each subject set.",
  "",
  sprintf(
    "all516: subjects=%d, reactions_before=%d, zero_variance_removed=%d, reactions_after=%d",
    subject_set_results$all516$subject_count,
    subject_set_results$all516$feature_count_before,
    subject_set_results$all516$zero_variance_removed,
    subject_set_results$all516$feature_count_after
  ),
  sprintf(
    "optimal414: subjects=%d, reactions_before=%d, zero_variance_removed=%d, reactions_after=%d",
    subject_set_results$optimal414$subject_count,
    subject_set_results$optimal414$feature_count_before,
    subject_set_results$optimal414$zero_variance_removed,
    subject_set_results$optimal414$feature_count_after
  ),
  "",
  "Interpretation cautions",
  "- Primary biological interpretation should come from the optimal414 PCA.",
  "- The all516 PCA is a QC/exploratory comparison and may be influenced by infeasible subjects.",
  "- The main PCA is reaction-only, so species identity must be recovered from the taxon contribution tables.",
  "- The lysine/butyrate subset is token-based first-pass filtering on reaction IDs and should not be treated as a final curated provenance panel.",
  "",
  "Output files",
  paste("Scores table:", scores_output),
  paste("Explained variance table:", variance_output),
  paste("Loadings table:", loadings_output),
  paste("Top-loading reaction summary:", top_loading_output),
  paste("Top-reaction taxon contribution summary:", top_reaction_contribution_output),
  paste("Lysine/butyrate taxon contribution summary:", lys_but_contribution_output),
  paste("Scree plot:", scree_plot_output),
  paste("Scores by cohort:", cohort_plot_output),
  paste("Scores by age group:", age_plot_output),
  paste("Scores by solver status:", solver_plot_output)
)

write_lines(append_csv_output_dictionary_to_lines(report_lines, csv_output_specs), report_output)

cat("Wrote", scores_output, "\n")
cat("Wrote", variance_output, "\n")
cat("Wrote", loadings_output, "\n")
cat("Wrote", top_loading_output, "\n")
cat("Wrote", top_reaction_contribution_output, "\n")
cat("Wrote", lys_but_contribution_output, "\n")
cat("Wrote", scree_plot_output, "\n")
cat("Wrote", cohort_plot_output, "\n")
cat("Wrote", age_plot_output, "\n")
cat("Wrote", solver_plot_output, "\n")
cat("Wrote", report_output, "\n")
