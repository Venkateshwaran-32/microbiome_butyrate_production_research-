setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

age_bin_community_species_growth <- read_csv("/Users/taknev/Desktop/microbiome_butyrate_production_research/Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv")

ggplot(
  age_bin_community_species_growth,
  aes(x = age_group, y = species_biomass_flux, fill = diet_name)
) +
  geom_col(position = "dodge")





# the below script is more concise 


setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor, ggtext)
library(ggtext)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

age_bin_community_species_growth <- read_csv(
  "Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv",
  show_col_types = FALSE
)

plot_data <- age_bin_community_species_growth %>%
  filter(is_growing == TRUE) %>%
  mutate(species_short = italicize_taxon(species_name))

community_species_growth_plot <- plot_data %>%
  ggplot(aes(x = species_short, y = species_biomass_flux, fill = diet_name)) +
  geom_col(position = "dodge", width = 0.55) +
  facet_wrap(~ age_group, nrow = 1) +
  labs(
    x = NULL,
    y = "Biomass flux",
    fill = "Diet",
    title = "Growing species in each age bin by diet",
    subtitle = "Includes 91_100 bin (n=26)."
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

ggsave(
  "Results/cobrapy_fba/figures/age_bin_community_growing_species.png",
  plot = community_species_growth_plot,
  width = 14,
  height = 5,
  dpi = 300
)

ggplot(plot_data, aes(x = species_short, y = species_biomass_flux, fill = diet_name)) +
  geom_col(width = 0.45) +
  facet_grid(diet_name ~ age_group) +
  labs(
    x = "species that grow",
    y = "Biomass flux",
    fill = "Diet",
    title = "Growing species in each age bin by diet",
    subtitle = "Includes 91_100 bin (n=26)."
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1),
    legend.position = "none"
  )




# all in one row 


ggplot(
  plot_data,
  aes(x = species_short, y = species_biomass_flux, fill = diet_name)
) +
  geom_col(position = "dodge", width = 0.55) +
  facet_wrap(~ age_group, nrow = 1) +
  labs(
    x = NULL,
    y = "Biomass flux",
    fill = "Diet",
    title = "Growing species in each age bin by diet",
    subtitle = "Includes 91_100 bin (n=26)."
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +

  theme_minimal() +
  theme(
    axis.text.x = ggtext::element_markdown(angle = 45, hjust = 1),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

