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
