suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(stringr)
})

TOP4_SUBJECTS <- c("MBS1232", "MBS1529", "MBS1262", "MBS1255")
EXTREME_THRESHOLD <- 1000
TOP_N_REACTIONS <- 15

original_flux_path <- "Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv"
original_taxon_path <- "Results/subject_level_fba/tables/08_allcohort_subject_taxon_growth_high_fiber_pfba.csv"
original_community_path <- "Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv"
rerun_flux_path <- "Results/subject_level_fba/tables/inspection_top4_no_pfba_flux.csv"
rerun_taxon_path <- "Results/subject_level_fba/tables/inspection_top4_no_pfba_taxon.csv"
rerun_community_path <- "Results/subject_level_fba/tables/inspection_top4_no_pfba_community.csv"

summary_output <- "Results/qc/tables/inspection_top4_subject_flux_summary.csv"
top_reactions_output <- "Results/qc/tables/inspection_top4_top_reactions.csv"
taxon_burden_output <- "Results/qc/tables/inspection_top4_taxon_flux_burden.csv"
comparison_output <- "Results/qc/tables/inspection_top4_pfba_vs_no_pfba_comparison.csv"
report_output <- "Results/qc/reports/inspection_top4_report.txt"

dir.create(dirname(summary_output), recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(report_output), recursive = TRUE, showWarnings = FALSE)

add_run_type <- function(df, run_type) {
  df %>% mutate(run_type = run_type)
}

subject_flux_summary <- function(flux_df) {
  flux_df %>%
    group_by(run_type, subject_id, cohort, age_years, age_group) %>%
    summarise(
      max_abs_flux = max(abs_flux, na.rm = TRUE),
      n_rxn_over_1k = sum(abs_flux > EXTREME_THRESHOLD, na.rm = TRUE),
      n_medium_over_1k = sum(abs_flux > EXTREME_THRESHOLD & is_medium, na.rm = TRUE),
      n_internal_over_1k = sum(abs_flux > EXTREME_THRESHOLD & !is_medium, na.rm = TRUE),
      .groups = "drop"
    )
}

top_reaction_rows <- function(flux_df) {
  flux_df %>%
    group_by(run_type, subject_id) %>%
    arrange(desc(abs_flux), .by_group = TRUE) %>%
    slice_head(n = TOP_N_REACTIONS) %>%
    ungroup() %>%
    mutate(
      reaction_class = case_when(
        is_medium ~ "medium_exchange",
        str_detect(reaction_id, "tex|tpp|EX_") ~ "transport_or_exchange",
        TRUE ~ "internal"
      )
    ) %>%
    select(run_type, subject_id, cohort, age_years, age_group, taxon_id, reaction_id, flux, abs_flux, is_medium, reaction_class)
}

taxon_flux_burden <- function(flux_df, taxon_df) {
  flux_df %>%
    filter(!is_medium, taxon_id != "") %>%
    group_by(run_type, subject_id, taxon_id) %>%
    summarise(
      total_abs_flux = sum(abs_flux, na.rm = TRUE),
      max_abs_flux = max(abs_flux, na.rm = TRUE),
      n_rxn_over_1k = sum(abs_flux > EXTREME_THRESHOLD, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    left_join(
      taxon_df %>%
        select(run_type, subject_id, taxon_id, species_name, abundance_raw, abundance_normalized, growth_rate),
      by = c("run_type", "subject_id", "taxon_id")
    ) %>%
    arrange(run_type, subject_id, desc(total_abs_flux))
}

original_flux <- read_csv(original_flux_path, show_col_types = FALSE) %>%
  filter(subject_id %in% TOP4_SUBJECTS) %>%
  add_run_type("pfba")
original_taxon <- read_csv(original_taxon_path, show_col_types = FALSE) %>%
  filter(subject_id %in% TOP4_SUBJECTS) %>%
  add_run_type("pfba")
original_community <- read_csv(original_community_path, show_col_types = FALSE) %>%
  filter(subject_id %in% TOP4_SUBJECTS) %>%
  add_run_type("pfba")

rerun_flux <- read_csv(rerun_flux_path, show_col_types = FALSE) %>% add_run_type("no_pfba")
rerun_taxon <- read_csv(rerun_taxon_path, show_col_types = FALSE) %>% add_run_type("no_pfba")
rerun_community <- read_csv(rerun_community_path, show_col_types = FALSE) %>% add_run_type("no_pfba")

all_flux <- bind_rows(original_flux, rerun_flux)
all_taxon <- bind_rows(original_taxon, rerun_taxon)
all_community <- bind_rows(original_community, rerun_community)

summary_table <- subject_flux_summary(all_flux) %>%
  left_join(
    all_community %>%
      select(run_type, subject_id, solver_status, community_growth_rate, objective_value),
    by = c("run_type", "subject_id")
  ) %>%
  arrange(desc(run_type), desc(max_abs_flux))

top_reactions_table <- top_reaction_rows(all_flux)
taxon_burden_table <- taxon_flux_burden(all_flux, all_taxon)

comparison_table <- summary_table %>%
  select(run_type, subject_id, community_growth_rate, objective_value, max_abs_flux, n_rxn_over_1k, n_medium_over_1k, n_internal_over_1k) %>%
  tidyr::pivot_wider(
    names_from = run_type,
    values_from = c(community_growth_rate, objective_value, max_abs_flux, n_rxn_over_1k, n_medium_over_1k, n_internal_over_1k)
  ) %>%
  mutate(
    max_abs_flux_drop = max_abs_flux_pfba - max_abs_flux_no_pfba,
    max_abs_flux_drop_ratio = max_abs_flux_pfba / pmax(max_abs_flux_no_pfba, 1e-12),
    n_rxn_over_1k_drop = n_rxn_over_1k_pfba - n_rxn_over_1k_no_pfba
  ) %>%
  arrange(desc(max_abs_flux_pfba))

write_csv(summary_table, summary_output)
write_csv(top_reactions_table, top_reactions_output)
write_csv(taxon_burden_table, taxon_burden_output)
write_csv(comparison_table, comparison_output)

report_lines <- c(
  "Inspection top 4 flux review",
  sprintf("Subjects: %s", paste(TOP4_SUBJECTS, collapse = ", ")),
  sprintf("Extreme threshold: %s", EXTREME_THRESHOLD),
  "",
  "Subject-level comparison"
)

for (i in seq_len(nrow(comparison_table))) {
  row <- comparison_table[i, ]
  report_lines <- c(
    report_lines,
    sprintf(
      "%s: pfba max_abs_flux=%.6f, no_pfba max_abs_flux=%.6f, ratio=%.3f, pfba rxn_over_1k=%s, no_pfba rxn_over_1k=%s, pfba growth=%.6f, no_pfba growth=%.6f",
      row$subject_id,
      row$max_abs_flux_pfba,
      row$max_abs_flux_no_pfba,
      row$max_abs_flux_drop_ratio,
      row$n_rxn_over_1k_pfba,
      row$n_rxn_over_1k_no_pfba,
      row$community_growth_rate_pfba,
      row$community_growth_rate_no_pfba
    )
  )
}

writeLines(report_lines, report_output)
