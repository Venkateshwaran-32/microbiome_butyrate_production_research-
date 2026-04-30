setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")

if (!requireNamespace("pacman", quietly = TRUE)) {
  install.packages("pacman", repos = "https://cloud.r-project.org")
}

pacman::p_load(tidyverse)

input_csv <- file.path(
  "Results",
  "subject_level_fba",
  "tables",
  "08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv"
)

tables_dir <- file.path("Results", "subject_level_fba", "tables")
figures_dir <- file.path("Results", "subject_level_fba", "figures")
reports_dir <- file.path("Results", "subject_level_fba", "reports")

dir.create(tables_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(reports_dir, recursive = TRUE, showWarnings = FALSE)

scores_output <- file.path(tables_dir, "11_direct_high_fiber_flux_pca_scores.csv")
variance_output <- file.path(tables_dir, "11_direct_high_fiber_flux_pca_explained_variance.csv")
loadings_output <- file.path(tables_dir, "11_direct_high_fiber_flux_pca_loadings.csv")
scree_plot_output <- file.path(figures_dir, "11_direct_high_fiber_flux_pca_scree.png")
cohort_plot_output <- file.path(figures_dir, "11_direct_high_fiber_flux_pca_scores_by_cohort.png")
age_plot_output <- file.path(figures_dir, "11_direct_high_fiber_flux_pca_scores_by_age_group.png")
report_output <- file.path(reports_dir, "11_direct_high_fiber_flux_pca_report.txt")

flux_long <- read_csv(input_csv, show_col_types = FALSE) %>%
  mutate(is_medium = tolower(as.character(is_medium))) %>%
  filter(is_medium != "true")

subject_metadata <- flux_long %>%
  distinct(subject_id, cohort, age_years, age_group) %>%
  arrange(subject_id)

subject_reaction_matrix <- flux_long %>%
  group_by(subject_id, reaction_id) %>%
  summarise(flux = sum(flux, na.rm = TRUE), .groups = "drop") %>%
  pivot_wider(
    names_from = reaction_id,
    values_from = flux,
    values_fill = 0
  ) %>%
  arrange(subject_id)

subject_ids <- subject_reaction_matrix$subject_id
flux_matrix <- subject_reaction_matrix %>%
  select(-subject_id) %>%
  as.matrix()

rownames(flux_matrix) <- subject_ids
storage.mode(flux_matrix) <- "double"

transformed_matrix <- asinh(flux_matrix)
feature_sd <- apply(transformed_matrix, 2, sd)
keep_features <- is.finite(feature_sd) & feature_sd > 0
filtered_matrix <- transformed_matrix[, keep_features, drop = FALSE]

if (ncol(filtered_matrix) < 2) {
  stop("PCA needs at least two non-zero-variance reaction features.")
}

pca_fit <- prcomp(filtered_matrix, center = TRUE, scale. = TRUE)

score_pc_count <- min(10, ncol(pca_fit$x))
scores_df <- as_tibble(
  pca_fit$x[, seq_len(score_pc_count), drop = FALSE],
  rownames = "subject_id"
) %>%
  left_join(subject_metadata, by = "subject_id") %>%
  relocate(subject_id, cohort, age_years, age_group)

variance_df <- tibble(
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
  mutate(abs_loading = abs(loading)) %>%
  arrange(pc, desc(abs_loading), reaction_id)

write_csv(scores_df, scores_output)
write_csv(variance_df, variance_output)
write_csv(loadings_df, loadings_output)

scree_plot_df <- variance_df %>%
  slice_head(n = 10) %>%
  mutate(pc = factor(pc, levels = paste0("PC", seq_len(n()))))

scree_plot <- ggplot(
  scree_plot_df,
  aes(x = pc, y = explained_variance_fraction)
) +
  geom_col(fill = "#1F7A6D") +
  labs(
    title = "High-fiber reaction flux PCA scree plot",
    x = NULL,
    y = "Explained variance fraction"
  ) +
  theme_minimal()

score_plot_df <- scores_df %>%
  filter(!is.na(PC1), !is.na(PC2))

cohort_plot <- ggplot(
  score_plot_df,
  aes(x = PC1, y = PC2, color = cohort)
) +
  geom_point(alpha = 0.8, size = 1.8) +
  labs(
    title = "High-fiber reaction flux PCA scores by cohort",
    x = "PC1",
    y = "PC2"
  ) +
  theme_minimal()

age_plot <- ggplot(
  score_plot_df,
  aes(x = PC1, y = PC2, color = age_group)
) +
  geom_point(alpha = 0.8, size = 1.8) +
  labs(
    title = "High-fiber reaction flux PCA scores by age group",
    x = "PC1",
    y = "PC2"
  ) +
  theme_minimal()

ggsave(scree_plot_output, plot = scree_plot, width = 8, height = 5, dpi = 300)
ggsave(cohort_plot_output, plot = cohort_plot, width = 8, height = 5.5, dpi = 300)
ggsave(age_plot_output, plot = age_plot, width = 8, height = 5.5, dpi = 300)

report_lines <- c(
  "Direct high-fiber flux PCA report",
  paste("Working directory:", getwd()),
  paste("Input CSV:", input_csv),
  "",
  "Preprocessing",
  "- Rows with is_medium == TRUE were excluded.",
  "- Flux was collapsed with a signed sum across taxa within subject_id + reaction_id.",
  "- Missing subject-reaction pairs were filled with 0.",
  "- A signed asinh transform was applied before centering and scaling.",
  "- Zero-variance reactions were removed before PCA.",
  "",
  sprintf("Subjects: %d", nrow(flux_matrix)),
  sprintf("Reactions before zero-variance filtering: %d", ncol(flux_matrix)),
  sprintf("Zero-variance reactions removed: %d", sum(!keep_features)),
  sprintf("Reactions used for PCA: %d", ncol(filtered_matrix)),
  "",
  "Output files",
  paste("Scores:", scores_output),
  paste("Explained variance:", variance_output),
  paste("Loadings:", loadings_output),
  paste("Scree plot:", scree_plot_output),
  paste("Scores by cohort:", cohort_plot_output),
  paste("Scores by age group:", age_plot_output)
)

write_lines(report_lines, report_output)

cat("Wrote", scores_output, "\n")
cat("Wrote", variance_output, "\n")
cat("Wrote", loadings_output, "\n")
cat("Wrote", scree_plot_output, "\n")
cat("Wrote", cohort_plot_output, "\n")
cat("Wrote", age_plot_output, "\n")
cat("Wrote", report_output, "\n")
