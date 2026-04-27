setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research/R_for_plotting ")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

community_growth_data <- read_csv("../Results/cobrapy_fba/tables/02_community_species_growth_by_diet.csv")
view(community_growth_data)

head(community_growth_data)


community_growth_plot <- community_growth_data %>%
  mutate(
    species_short = species_name %>%
      str_replace_all("_", " ") %>%
      str_replace("^([A-Za-z]+\\s+[A-Za-z]+).*", "\\1")
  ) %>%
  group_by(species_short) %>%
  mutate(max_flux = max(species_biomass_flux, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(species_short = fct_reorder(species_short, max_flux, .desc = TRUE))


ggplot(
  community_growth_plot,
  aes(x = species_short, y = species_biomass_flux, fill = diet_name)
) + labs(X = NULL , )+
  geom_col(position = "dodge") +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

