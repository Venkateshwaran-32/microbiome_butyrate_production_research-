setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

age_bin_levels <- c("21_40", "41_60", "61_70", "71_80", "81_90")
diet_levels <- c("western", "high_fiber")
trend_threshold <- 0.05
direct_label_species <- c(
  "Faecalibac P",
  "E coli",
  "Alistipes O",
  "Alistipes S",
  "Bacteroides D",
  "Bacteroides X"
)

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
    species_name == "Klebsiella pneumoniae" ~ "Klebsiella P",
    TRUE ~ species_name
  )
}

micom_agebin_growth <- read_csv(
  "Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv",
  show_col_types = FALSE
)

species_lookup <- micom_agebin_growth %>%
  distinct(taxon_id, species_name, paper_taxon) %>%
  mutate(species_short = short_species_name(species_name))

plot_data <- micom_agebin_growth %>%
  mutate(
    age_group = factor(age_group, levels = age_bin_levels),
    diet_name = factor(diet_name, levels = diet_levels),
    species_short = short_species_name(species_name)
  ) %>%
  complete(
    taxon_id,
    age_group = factor(age_bin_levels, levels = age_bin_levels),
    diet_name = factor(diet_levels, levels = diet_levels),
    fill = list(
      growth_rate = 0,
      is_growing = FALSE,
      median_abundance = 0,
      normalized_weight = 0
    )
  ) %>%
  left_join(species_lookup, by = "taxon_id", suffix = c("", "_lookup")) %>%
  mutate(
    species_name = coalesce(species_name, species_name_lookup),
    paper_taxon = coalesce(paper_taxon, paper_taxon_lookup),
    species_short = coalesce(species_short, species_short_lookup)
  ) %>%
  select(-ends_with("_lookup"))

species_trends <- plot_data %>%
  group_by(species_short) %>%
  summarise(
    youngest_growth = mean(growth_rate[age_group == "21_40"], na.rm = TRUE),
    oldest_growth = mean(growth_rate[age_group == "81_90"], na.rm = TRUE),
    growth_shift = oldest_growth - youngest_growth,
    max_growth = max(growth_rate, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    trend_group = case_when(
      growth_shift > trend_threshold ~ "increasing",
      growth_shift < -trend_threshold ~ "decreasing",
      TRUE ~ "stable"
    )
  ) %>%
  arrange(growth_shift, species_short)

species_order <- species_trends %>%
  pull(species_short)

species_colors <- c(
  "Alistipes O" = "#1B7837",
  "Alistipes S" = "#4A8F45",
  "Bacteroides D" = "#7A4A24",
  "Bacteroides X" = "#9B6532",
  "Faecalibac P" = "#5B2A86",
  "E coli" = "#1F4E5F",
  "Klebsiella P" = "#2F6C8F",
  "Parabacteroides M" = "#6A3D2A",
  "Ruminococcus T" = "#4A4A4A"
)

plot_data <- plot_data %>%
  mutate(species_short = factor(species_short, levels = species_order))

endpoint_labels <- plot_data %>%
  filter(
    age_group == "81_90",
    species_short %in% direct_label_species
  )

micom_agebin_growth_plot <- ggplot(
  plot_data,
  aes(x = age_group, y = growth_rate, color = species_short, group = species_short)
) +
  geom_line(linewidth = 1.05, alpha = 0.9) +
  geom_point(aes(shape = is_growing), size = 2.4, stroke = 0.7) +
  geom_text(
    data = endpoint_labels,
    aes(label = species_short),
    hjust = -0.08,
    size = 3,
    show.legend = FALSE
  ) +
  facet_wrap(~ diet_name, nrow = 1) +
  scale_color_manual(values = species_colors, name = "Species") +
  scale_shape_manual(
    values = c("TRUE" = 16, "FALSE" = 1),
    labels = c("FALSE" = "Not growing", "TRUE" = "Growing"),
    name = NULL
  ) +
  scale_x_discrete(expand = expansion(add = c(0.35, 1.1))) +
  labs(
    x = NULL,
    y = "MICOM taxon growth rate",
    title = "MICOM age-bin taxon growth by diet",
    subtitle = "Alistipes species use green shades, Bacteroides use brown shades, and Faecalibac P uses purple"
  ) +
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
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right",
    legend.title = element_text(face = "bold", color = "#1F1F1F"),
    legend.text = element_text(color = "#2B2B2B")
  ) +
  coord_cartesian(clip = "off")

print(micom_agebin_growth_plot)

ggsave(
  "Results/micom_fba/figures/micom_multispecies_agebin_growth_plot.png",
  plot = micom_agebin_growth_plot,
  width = 15,
  height = 6.5,
  dpi = 300
)
