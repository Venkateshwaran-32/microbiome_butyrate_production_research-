setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

micom_taxon_growth <- read_csv(
  "Results/micom_fba/tables/04_micom_taxon_growth_by_diet.csv",
  show_col_types = FALSE
)

short_species_name <- function(taxon_id) {
  case_when(
    taxon_id == "Escherichia_coli_UTI89_UPEC" ~ "E coli",
    taxon_id == "Faecalibacterium_prausnitzii_M21_2" ~ "Faecalibac P",
    taxon_id == "Parabacteroides_merdae_ATCC_43184" ~ "Parabacteroides M",
    taxon_id == "Ruminococcus_torques_ATCC_27756" ~ "Ruminococcus T",
    taxon_id == "Alistipes_onderdonkii_DSM_19147" ~ "Alistipes O",
    taxon_id == "Alistipes_shahii_WAL_8301" ~ "Alistipes S",
    taxon_id == "Bacteroides_dorei_DSM_17855" ~ "Bacteroides D",
    taxon_id == "Bacteroides_xylanisolvens_XB1A" ~ "Bacteroides X",
    taxon_id == "Bilophila_wadsworthia_3_1_6" ~ "Bilophila W",
    taxon_id == "Klebsiella_pneumoniae_pneumoniae_MGH78578" ~ "Klebsiella P",
    TRUE ~ taxon_id %>%
      str_replace_all("_", " ") %>%
      str_replace("^([A-Za-z]+\\s+[A-Za-z]+).*", "\\1")
  )
}

species_summary <- micom_taxon_growth %>%
  mutate(species_short = short_species_name(taxon_id)) %>%
  group_by(taxon_id, species_short) %>%
  summarise(
    max_growth = max(growth_rate, na.rm = TRUE),
    growth_shift = growth_rate[diet_name == "high_fiber"][1] - growth_rate[diet_name == "western"][1],
    .groups = "drop"
  ) %>%
  arrange(desc(max_growth), desc(growth_shift), species_short)

species_order <- species_summary %>%
  pull(taxon_id)

species_short_order <- species_summary %>%
  pull(species_short)

plot_data <- micom_taxon_growth %>%
  mutate(
    diet_name = factor(diet_name, levels = c("western", "high_fiber")),
    species_short = short_species_name(taxon_id),
    taxon_id = factor(taxon_id, levels = species_order),
    species_short = factor(species_short, levels = species_short_order)
  )

micom_growth_plot <- ggplot(
  plot_data,
  aes(x = species_short, y = growth_rate, fill = diet_name)
) +
  geom_col(width = 0.62) +
  facet_wrap(~ diet_name, nrow = 1) +
  labs(
    x = NULL,
    y = "Growth rate",
    title = "MICOM baseline community taxon growth by diet",
    subtitle = "Species are ordered by highest observed growth rate across the two diets"
  ) +
  scale_fill_manual(values = c(
    "western" = "#C65D00",
    "high_fiber" = "#1B7837"
  ), guide = "none") +
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
    strip.text = element_text(face = "bold", color = "#1F1F1F")
  )

print(micom_growth_plot)

ggsave(
  "Results/micom_fba/figures/micom_baseline_community_growth_by_diet.png",
  plot = micom_growth_plot,
  width = 14,
  height = 5.5,
  dpi = 300
)

