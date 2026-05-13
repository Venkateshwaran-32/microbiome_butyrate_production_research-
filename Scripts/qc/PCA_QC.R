setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
rm(list = ls())

pacman::p_load(tidyverse)

MICOM <- read_csv("Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv")

subject_qc <- MICOM %>%
  mutate(abs_flux = abs(flux)) %>%
  group_by(subject_id) %>%
  summarise(
    cohort = first(cohort),
    age_years = first(age_years),
    age_group = first(age_group),
    max_abs_flux = max(abs_flux, na.rm = TRUE),
    n_rxn_over_1k = sum(abs_flux > 1000, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    flux_group = case_when(
      max_abs_flux <= 1000 ~ "<=1k",
      max_abs_flux <= 10000 ~ "1k-10k",
      max_abs_flux <= 100000 ~ "10k-100k",
      TRUE ~ "100k+"
    )
  )

flagged_subjects <- subject_qc %>%
  filter(max_abs_flux > 1000) %>%
  arrange(desc(max_abs_flux))

less_than_1k_flux_subjects <- MICOM %>%
  filter(!subject_id %in% flagged_subjects$subject_id)

less_than_1k_subject_qc <- less_than_1k_flux_subjects %>%
  mutate(abs_flux = abs(flux)) %>%
  group_by(subject_id) %>%
  summarise(
    cohort = first(cohort),
    age_years = first(age_years),
    age_group = first(age_group),
    max_abs_flux = max(abs_flux, na.rm = TRUE),
    n_rxn_over_1k = sum(abs_flux > 1000, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    flux_group = case_when(
      max_abs_flux <= 1000 ~ "<=1k",
      max_abs_flux <= 10000 ~ "1k-10k",
      max_abs_flux <= 100000 ~ "10k-100k",
      TRUE ~ "100k+"
    )
  )

# Subject : MBS1232 all fluxes  -------------------------------------------
mbs1232_fluxes <- MICOM %>%
  mutate(abs_flux = abs(flux)) %>%
  filter(subject_id == "MBS1232") %>%
  arrange(desc(abs_flux))

nrow(mbs1232_fluxes) # 2131 
#Subject : MBS1232 fluxes >100 ----------------------- 
mbs1232_high_fluxes <- mbs1232_fluxes %>%
  filter(abs_flux > 1000)

ggplot(subject_qc, aes(x = flux_group)) +
  geom_bar() +
  labs(
    x = "Subject maximum absolute flux bin",
    y = "Number of subjects",
    title = "QC of extreme MICOM flux values"
  )

# clustering the 11 subjects  ---------------------------------------------

flagged_high_flux_rxns <- MICOM %>%
  mutate(abs_flux = abs(flux)) %>%
  filter(subject_id %in% flagged_subjects$subject_id, abs_flux > 1000)

shared_high_flux_rxns <- flagged_high_flux_rxns %>%
  group_by(reaction_id) %>%
  summarise(
    n_subjects = n_distinct(subject_id),
    subjects = paste(sort(unique(subject_id)), collapse = ", "),
    .groups = "drop"
  ) %>%
  arrange(desc(n_subjects), reaction_id)

shared_high_flux_rxns %>% filter(n_subjects > 1)

reaction_subject_matrix <- flagged_high_flux_rxns %>%
  distinct(reaction_id, subject_id) %>%
  mutate(high_flux_present = 1) %>%
  pivot_wider(
    names_from = subject_id,
    values_from = high_flux_present,
    values_fill = 0
  ) %>%
  column_to_rownames("reaction_id") %>%
  as.matrix()

reaction_dist <- dist(reaction_subject_matrix, method = "binary")
reaction_hclust <- hclust(reaction_dist, method = "ward.D2")
reaction_clusters <- cutree(reaction_hclust, k = 3)

reaction_cluster_df <- tibble(
  reaction_id = names(reaction_clusters),
  cluster = factor(reaction_clusters)
)

cluster_colors <- c("1" = "#D55E00", "2" = "#0072B2", "3" = "#009E73")

pheatmap::pheatmap(
  reaction_subject_matrix,
  cluster_rows = reaction_hclust,
  cluster_cols = TRUE,
  annotation_row = reaction_cluster_df %>% column_to_rownames("reaction_id"),
  annotation_colors = list(cluster = cluster_colors),
  show_rownames = FALSE
)
