setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext)
library(ggtext)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

single_species_growth_value <- read_csv(
  "Results/cobrapy_fba/tables/01_single_species_growth_and_butyrate_by_diet.csv",
  show_col_types = FALSE
)

single_species_growth_value <- single_species_growth_value %>%
  mutate(species_short = italicize_taxon(strip_strain(species_name))) %>%
  group_by(species_short) %>%
  mutate(max_growth = max(growth_value, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(species_short = fct_reorder(species_short, max_growth, .desc = TRUE))

single_species_growth_plot <- ggplot(
  single_species_growth_value,
  aes(x = species_short, y = growth_value, fill = diet_name)
) +
  geom_col(position = "dodge") +
  labs(
    x = "Species",
    y = "Growth value",
    fill = "Diet",
    title = "Single-species growth by diet"
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1)
  )

ggsave(
  "Results/cobrapy_fba/figures/single_species_growth.png",
  plot = single_species_growth_plot,
  width = 12,
  height = 5.5,
  dpi = 300
)

