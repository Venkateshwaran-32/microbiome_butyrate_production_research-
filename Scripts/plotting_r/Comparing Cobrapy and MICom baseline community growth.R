setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext, patchwork)
library(ggtext)
library(patchwork)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

zero_threshold <- 1e-9

micom_growth <- read_csv(
  "Results/micom_fba/tables/04_micom_taxon_growth_by_diet.csv",
  show_col_types = FALSE
) %>%
  transmute(
    diet_name,
    species_id = taxon_id,
    growth_value = growth_rate,
    is_growing,
    method = "MICOM"
  )

cobrapy_growth <- read_csv(
  "Results/cobrapy_fba/tables/02_community_species_growth_by_diet.csv",
  show_col_types = FALSE
) %>%
  transmute(
    diet_name,
    species_id = species_name,
    growth_value = if_else(abs(species_biomass_flux) < zero_threshold, 0, species_biomass_flux),
    is_growing,
    method = "COBRApy"
  )

combined_growth <- bind_rows(micom_growth, cobrapy_growth) %>%
  mutate(
    species_short = italicize_taxon(strip_strain(species_id)),
    diet_name = factor(diet_name, levels = c("western", "high_fiber")),
    method = factor(method, levels = c("COBRApy", "MICOM"))
  )

species_order <- combined_growth %>%
  filter(method == "MICOM") %>%
  group_by(species_short) %>%
  summarise(max_growth = max(growth_value, na.rm = TRUE), .groups = "drop") %>%
  arrange(desc(max_growth), species_short) %>%
  pull(species_short)

combined_growth <- combined_growth %>%
  mutate(
    species_short = factor(species_short, levels = species_order)
  )

bar_data <- combined_growth %>%
  mutate(panel_type = "Growth magnitude")

status_data <- combined_growth %>%
  mutate(
    status_fill = if_else(is_growing, method, "Not growing")
  )

growth_plot <- ggplot(
  bar_data,
  aes(x = species_short, y = growth_value, fill = method)
) +
  geom_col(
    position = position_dodge(width = 0.72),
    width = 0.62
  ) +
  facet_wrap(~ diet_name, nrow = 1) +
  labs(
    x = NULL,
    y = "Growth value",
    title = "COBRApy vs MICOM baseline community growth by diet",
    subtitle = "Top: growth magnitude. Bottom: whether each species is predicted to grow."
  ) +
  scale_fill_manual(
    values = c(
      "COBRApy" = "#C65D00",
      "MICOM" = "#1B7837"
    ),
    breaks = c("COBRApy", "MICOM"),
    name = NULL
  ) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1, color = "#2B2B2B"),
    axis.text.y = element_text(color = "#2B2B2B"),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    strip.background = element_rect(fill = "white", color = "#2B2B2B", linewidth = 0.8),
    panel.border = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    legend.position = "top",
    plot.title = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A")
  )

status_plot <- ggplot(
  status_data,
  aes(x = species_short, y = method, fill = status_fill)
) +
  geom_tile(height = 0.72, width = 0.72) +
  facet_wrap(~ diet_name, nrow = 1) +
  labs(
    x = NULL,
    y = NULL
  ) +
  scale_fill_manual(
    values = c(
      "COBRApy" = "#C65D00",
      "MICOM" = "#1B7837",
      "Not growing" = "#D9D9D9"
    ),
    breaks = c("COBRApy", "MICOM", "Not growing"),
    name = NULL
  ) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1, color = "#2B2B2B"),
    axis.text.y = element_text(color = "#2B2B2B"),
    strip.text = element_text(face = "bold", color = "#1F1F1F"),
    strip.background = element_rect(fill = "white", color = "#2B2B2B", linewidth = 0.8),
    panel.border = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    legend.position = "none"
  )

comparison_plot <- growth_plot / status_plot + plot_layout(heights = c(3.6, 1.4))

print(comparison_plot)

ggsave(
  filename = "Results/micom_fba/figures/cobrapy_vs_micom_baseline_growth_comparison.png",
  plot = comparison_plot,
  width = 15,
  height = 8,
  dpi = 300
)

