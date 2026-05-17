setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext, ggrepel)
library(ggtext)
library(ggrepel)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

age_bin_levels <- c("21_40", "41_60", "61_70", "71_80", "81_90", "91_100")
diet_levels <- c("western", "high_fiber")
trend_threshold <- 0.05
direct_label_species <- c(
  "F. prausnitzii",
  "E. coli",
  "A. onderdonkii",
  "A. shahii",
  "B. dorei",
  "B. xylanisolvens"
)

micom_agebin_growth <- read_csv(
  "Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv",
  show_col_types = FALSE
)

bilophila_stub <- tidyr::crossing(
  age_group = age_bin_levels,
  diet_name = diet_levels
) %>%
  mutate(
    taxon_id = "Bilophila_wadsworthia_3_1_6",
    species_name = "Bilophila wadsworthia",
    paper_taxon = "Bilophila unclassified",
    median_abundance = 0,
    normalized_weight = 0,
    n_subjects = NA_integer_,
    growth_rate = 0,
    is_growing = FALSE,
    reactions = NA_integer_,
    metabolites = NA_integer_
  )

micom_agebin_growth <- bind_rows(micom_agebin_growth, bilophila_stub)

species_lookup <- micom_agebin_growth %>%
  distinct(taxon_id, species_name, paper_taxon) %>%
  mutate(species_short = italicize_taxon(species_name))

plot_data <- micom_agebin_growth %>%
  mutate(
    age_group = factor(age_group, levels = age_bin_levels),
    diet_name = factor(diet_name, levels = diet_levels),
    species_short = italicize_taxon(species_name)
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
    oldest_growth = mean(growth_rate[age_group == "91_100"], na.rm = TRUE),
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
  "F. prausnitzii"   = "#9467BD",
  "E. coli"          = "#1F77B4",
  "R. torques"       = "#2CA02C",
  "B. dorei"         = "#8C564B",
  "B. xylanisolvens" = "#FF7F0E",
  "B. wadsworthia"   = "#7F7F7F",
  "A. onderdonkii"   = "#BCBD22",
  "A. shahii"        = "#17BECF",
  "K. pneumoniae"    = "#E377C2",
  "P. merdae"        = "#D62728"
)

plot_data <- plot_data %>%
  mutate(species_short = factor(species_short, levels = species_order))

endpoint_labels <- plot_data %>%
  filter(age_group == "91_100")

micom_agebin_growth_plot <- ggplot(
  plot_data,
  aes(x = age_group, y = growth_rate, color = species_short, group = species_short)
) +
  geom_line(linewidth = 0.55, alpha = 0.9) +
  geom_point(aes(shape = is_growing), size = 1.6, stroke = 0.55) +
  ggrepel::geom_text_repel(
    data = endpoint_labels,
    aes(label = species_short),
    direction = "y",
    nudge_x = 0.45,
    hjust = 0,
    size = 3,
    segment.size = 0.3,
    segment.color = "gray60",
    segment.alpha = 0.7,
    box.padding = 0.18,
    point.padding = 0.15,
    min.segment.length = 0,
    max.overlaps = Inf,
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
    subtitle = "Species weighted by median relative abundance per age bin, pooled across the four cohorts (T2D, CRE, SPMP, SG90; n=516)."
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
    legend.text = ggtext::element_markdown(color = "#2B2B2B")
  ) +
  coord_cartesian(clip = "off")

print(micom_agebin_growth_plot)

ggsave(
  "Results/micom_fba/figures/micom_multispecies_agebin_growth_plot.png",
  plot = micom_agebin_growth_plot,
  width = 15,
  height = 6.5,
  dpi = 600
)
