setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext, patchwork)
library(ggtext)
library(patchwork)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

age_bin_levels <- c("21_40", "41_60", "61_70", "71_80", "81_90", "91_100")
diet_levels <- c("western", "high_fiber")
age_midpoints <- c("21_40" = 30.5, "41_60" = 50.5, "61_70" = 65.5, "71_80" = 75.5, "81_90" = 85.5, "91_100" = 95.5)

species_family <- function(species_name) {
  case_when(
    str_detect(species_name, "^Alistipes") ~ "Alistipes",
    str_detect(species_name, "^Bacteroides") ~ "Bacteroides",
    str_detect(species_name, "^Faecalibacterium") ~ "Faecalibacterium",
    str_detect(species_name, "^Escherichia") ~ "Escherichia",
    TRUE ~ "Other"
  )
}

family_colors <- c(
  "Alistipes" = "#1B7837",
  "Bacteroides" = "#7A4A24",
  "Faecalibacterium" = "#5B2A86",
  "Escherichia" = "#1F4E5F",
  "Other" = "#4A4A4A"
)

micom_growth <- read_csv(
  "Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv",
  show_col_types = FALSE
) %>%
  mutate(
    age_group = factor(age_group, levels = age_bin_levels),
    diet_name = factor(diet_name, levels = diet_levels),
    age_mid = unname(age_midpoints[as.character(age_group)]),
    species_short = italicize_taxon(species_name),
    family = species_family(species_name)
  )

species_lookup <- micom_growth %>%
  distinct(taxon_id, species_name, species_short, family)

slope_data <- micom_growth %>%
  group_by(taxon_id, species_short, family, diet_name) %>%
  summarise(
    n_age_bins = n_distinct(age_group),
    slope = if_else(n_age_bins >= 2, coef(lm(growth_rate ~ age_mid))[["age_mid"]], NA_real_),
    mean_growth = mean(growth_rate, na.rm = TRUE),
    max_growth = max(growth_rate, na.rm = TRUE),
    .groups = "drop"
  )

species_order <- slope_data %>%
  group_by(species_short) %>%
  summarise(
    mean_slope = mean(slope, na.rm = TRUE),
    mean_growth = mean(mean_growth, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  arrange(mean_slope, mean_growth, species_short) %>%
  pull(species_short)

heatmap_data <- micom_growth %>%
  select(taxon_id, species_short, family, diet_name, age_group, growth_rate) %>%
  complete(
    taxon_id,
    diet_name = factor(diet_levels, levels = diet_levels),
    age_group = factor(age_bin_levels, levels = age_bin_levels)
  ) %>%
  left_join(species_lookup, by = "taxon_id", suffix = c("", "_lookup")) %>%
  mutate(
    species_short = coalesce(species_short, species_short_lookup),
    family = coalesce(family, family_lookup),
    growth_for_heatmap = replace_na(growth_rate, 0),
    species_short = factor(species_short, levels = species_order)
  ) %>%
  select(-ends_with("_lookup"))

slope_data <- slope_data %>%
  mutate(
    species_short = factor(species_short, levels = species_order),
    slope_direction = case_when(
      slope > 0 ~ "Increasing with age",
      slope < 0 ~ "Decreasing with age",
      TRUE ~ "Flat"
    )
  )

heatmap_plot <- ggplot(
  heatmap_data,
  aes(x = age_group, y = species_short, fill = growth_for_heatmap)
) +
  geom_tile(color = "white", linewidth = 0.7) +
  facet_wrap(~ diet_name, nrow = 1) +
  scale_fill_gradient(
    low = "#F4EFE8",
    high = "#3F2417",
    name = "Growth rate"
  ) +
  labs(
    x = NULL,
    y = NULL,
    title = "MICOM taxon growth trends across age bins",
    subtitle = "Includes 91_100 bin (n=26). Heatmap shows predicted growth rate; missing taxon-age combinations are displayed as zero growth."
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, color = "#2B2B2B"),
    axis.text.y = ggtext::element_markdown(color = "#2B2B2B"),
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    panel.border = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    strip.background = element_rect(fill = "white", color = "#2B2B2B", linewidth = 0.8),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right"
  )

slope_plot <- ggplot(
  slope_data,
  aes(x = slope, y = species_short, color = family)
) +
  geom_vline(xintercept = 0, color = "#2B2B2B", linewidth = 0.6) +
  geom_segment(
    aes(x = 0, xend = slope, yend = species_short),
    linewidth = 0.8,
    alpha = 0.85
  ) +
  geom_point(size = 2.8) +
  facet_wrap(~ diet_name, nrow = 1) +
  scale_color_manual(values = family_colors, name = "Species group") +
  labs(
    x = "Growth-rate slope per age year",
    y = NULL,
    subtitle = "Slope summarizes age-associated growth trend using observed MICOM outputs only"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(color = "#2B2B2B"),
    axis.text.y = ggtext::element_markdown(color = "#2B2B2B"),
    axis.title.x = element_text(color = "#2B2B2B"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    panel.border = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    strip.background = element_rect(fill = "white", color = "#2B2B2B", linewidth = 0.8),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    legend.position = "right"
  )

combined_v2_plot <- heatmap_plot / slope_plot + plot_layout(heights = c(3, 2.4))

print(combined_v2_plot)

ggsave(
  filename = "Results/micom_fba/figures/micom_multispecies_agebin_growth_v2.png",
  plot = combined_v2_plot,
  width = 15,
  height = 10,
  dpi = 300
)
