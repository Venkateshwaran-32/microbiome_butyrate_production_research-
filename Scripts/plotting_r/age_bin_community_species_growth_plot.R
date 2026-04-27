setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

age_bin_community_species_growth <- read_csv("/Users/taknev/Desktop/microbiome_butyrate_production_research/Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv")

ggplot(
  age_bin_community_species_growth,
  aes(x = age_group, y = species_biomass_flux, fill = diet_name)
) +
  geom_col(position = "dodge")





# the below script is more concise 


setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

age_bin_community_species_growth <- read_csv(
  "Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv",
  show_col_types = FALSE
)

plot_data <- age_bin_community_species_growth %>%
  filter(is_growing == TRUE) %>%
  mutate(
    species_short = case_when(
      species_name == "Escherichia coli" ~ "E coli",
      species_name == "Faecalibacterium prausnitzii" ~ "Faecalibac P",
      species_name == "Parabacteroides merdae" ~ "Parabacteroides M",
      species_name == "Ruminococcus torques" ~ "Ruminococcus T",
      TRUE ~ species_name
    )
  )

ggplot(plot_data, aes(x = species_short, y = species_biomass_flux, fill = diet_name)) +
  geom_col(width = 0.45) +
  facet_grid(diet_name ~ age_group) +
  labs(
    x = "species that grow",
    y = "Biomass flux",
    fill = "Diet",
    title = "Growing species in each age bin by diet"
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
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
    title = "Growing species in each age bin by diet"
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  )) +
  
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

