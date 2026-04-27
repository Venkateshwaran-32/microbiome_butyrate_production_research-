setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

age_bin_taxa_abundance <- read_csv(
  "Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species_wide.csv",
  show_col_types = FALSE
)

age_shift_threshold <- 0.1

short_species_name <- function(species_name) {
  case_when(
    species_name == "Escherichia coli" ~ "E coli",
    species_name == "Faecalibacterium prausnitzii" ~ "Faecalibac P",
    species_name == "Parabacteroides merdae" ~ "Parabacteroides M",
    species_name == "Ruminococcus torques" ~ "Ruminococcus T",
    species_name == "Alistipes onderdonkii" ~ "Alistipes O",
    species_name == "Alistipes shahii" ~ "Alistipes S",
    species_name == "Bacteroides dorei" ~ "Bacteroides D",
    species_name == "Bacteroides xylanisolvens" ~ "Bacteroides X",
    species_name == "Bilophila wadsworthia" ~ "Bilophila W",
    species_name == "Klebsiella pneumoniae pneumoniae" ~ "Klebsiella P",
    TRUE ~ species_name
  )
}

species_summary <- age_bin_taxa_abundance %>%
  transmute(
    species_name,
    age_shift = `81_90` - `21_40`,
    trend_group = case_when(
      (`81_90` - `21_40`) < -age_shift_threshold ~ "decreasing",
      (`81_90` - `21_40`) > age_shift_threshold ~ "increasing",
      TRUE ~ "stable"
    ),
    species_short = short_species_name(species_name)
  ) %>%
  arrange(age_shift, species_name)

species_order <- species_summary %>%
  pull(species_name)

species_short_order <- species_summary %>%
  pull(species_short)

species_colors <- c(
  "Faecalibac P" = "#1F4E5F",
  "Ruminococcus T" = "#2A6A73",
  "Alistipes O" = "#8C3B1F",
  "Bacteroides X" = "#9B4B22",
  "Klebsiella P" = "#AA5922",
  "Bacteroides D" = "#B76622",
  "Parabacteroides M" = "#C57524",
  "Alistipes S" = "#4A4A4A",
  "Bilophila W" = "#6A6A6A",
  "E coli" = "#7A2E1C"
)

plot_data <- age_bin_taxa_abundance %>%
  pivot_longer(
    cols = c(`21_40`, `41_60`, `61_70`, `71_80`, `81_90`),
    names_to = "age_bin",
    values_to = "median_abundance"
  ) %>%
  mutate(
    age_bin = factor(age_bin, levels = c("21_40", "41_60", "61_70", "71_80", "81_90")),
    species_short = short_species_name(species_name),
    species_name = factor(species_name, levels = species_order),
    species_short = factor(species_short, levels = species_short_order)
  ) %>%
  left_join(
    species_summary %>% select(species_name, trend_group),
    by = "species_name"
  )

age_bin_taxa_plot <- ggplot(
  plot_data,
  aes(x = species_short, y = median_abundance, fill = species_short)
) +
  geom_col(width = 0.6, color = NA) +
  facet_wrap(~ age_bin, nrow = 1) +
  labs(
    x = NULL,
    y = "Median taxa abundance",
    title = "Median taxa abundance by age bin",
    subtitle = "Cool tones decrease with age, warm tones increase with age, gray tones stay relatively stable"
  ) +
  scale_fill_manual(values = species_colors, guide = "none") +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, color = "#2B2B2B"),
    axis.text.y = element_text(color = "#2B2B2B"),
    axis.title.y = element_text(color = "#2B2B2B"),
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    panel.border = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    strip.background = element_rect(fill = "white", color = "#2B2B2B", linewidth = 0.8),
    strip.text = element_text(face = "bold", color = "#1F1F1F")
  )

print(age_bin_taxa_plot)

ggsave(
  "Results/cobrapy_fba/figures/age_bin_median_taxa_abundance_visualisation.png",
  plot = age_bin_taxa_plot,
  width = 18,
  height = 5,
  dpi = 300
)

