setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

single_species_growth_value <- read_csv(
  "Results/cobrapy_fba/tables/01_single_species_growth_and_butyrate_by_diet.csv",
  show_col_types = FALSE
)

single_species_growth_value <- single_species_growth_value %>%
  mutate(
    species_short = species_name %>%
      str_replace_all("_", " ") %>%
      str_replace("^([A-Za-z]+\\s+[A-Za-z]+).*", "\\1")
  ) %>%
  group_by(species_short) %>%
  mutate(max_growth = max(growth_value, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(species_short = fct_reorder(species_short, max_growth, .desc = TRUE))

ggplot(
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
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

