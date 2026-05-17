setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext)
library(ggtext)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

community_growth_data <- read_csv(
  "Results/cobrapy_fba/tables/02_community_species_growth_by_diet.csv",
  show_col_types = FALSE
)

community_growth_plot_data <- community_growth_data %>%
  mutate(species_short = italicize_taxon(strip_strain(species_name))) %>%
  group_by(species_short) %>%
  mutate(max_flux = max(species_biomass_flux, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(species_short = fct_reorder(species_short, max_flux, .desc = TRUE))

community_growth_plot <- ggplot(
  community_growth_plot_data,
  aes(x = species_short, y = species_biomass_flux, fill = diet_name)
) +
  geom_col(position = "dodge") +
  labs(x = NULL, y = "Species biomass flux", fill = "Diet") +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1)
  )

ggsave(
  "Results/cobrapy_fba/figures/basic_community_growth_plot.png",
  plot = community_growth_plot,
  width = 12,
  height = 5.5,
  dpi = 300
)

