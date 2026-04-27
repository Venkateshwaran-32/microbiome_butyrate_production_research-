setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, readxl, janitor)
rm(list = ls())

zero_threshold <- 1e-9

short_species_name <- function(species_id) {
  case_when(
    species_id %in% c("Escherichia_coli_UTI89_UPEC", "Escherichia coli") ~ "E coli",
    species_id %in% c("Faecalibacterium_prausnitzii_M21_2", "Faecalibacterium prausnitzii") ~ "Faecalibac P",
    species_id %in% c("Parabacteroides_merdae_ATCC_43184", "Parabacteroides merdae") ~ "Parabacteroides M",
    species_id %in% c("Ruminococcus_torques_ATCC_27756", "Ruminococcus torques") ~ "Ruminococcus T",
    species_id %in% c("Alistipes_onderdonkii_DSM_19147", "Alistipes onderdonkii") ~ "Alistipes O",
    species_id %in% c("Alistipes_shahii_WAL_8301", "Alistipes shahii") ~ "Alistipes S",
    species_id %in% c("Bacteroides_dorei_DSM_17855", "Bacteroides dorei") ~ "Bacteroides D",
    species_id %in% c("Bacteroides_xylanisolvens_XB1A", "Bacteroides xylanisolvens") ~ "Bacteroides X",
    species_id %in% c("Bilophila_wadsworthia_3_1_6", "Bilophila wadsworthia") ~ "Bilophila W",
    species_id %in% c("Klebsiella_pneumoniae_pneumoniae_MGH78578", "Klebsiella pneumoniae") ~ "Klebsiella P",
    TRUE ~ species_id
  )
}

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
    species_short = short_species_name(species_id),
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
    axis.text.x = element_text(angle = 45, hjust = 1, color = "#2B2B2B"),
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
    axis.text.x = element_text(angle = 45, hjust = 1, color = "#2B2B2B"),
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

growth_grob <- ggplotGrob(growth_plot)
status_grob <- ggplotGrob(status_plot)

draw_comparison_plot <- function() {
  grid::grid.newpage()
  grid::pushViewport(
    grid::viewport(
      layout = grid::grid.layout(
        nrow = 2,
        ncol = 1,
        heights = grid::unit(c(3.6, 1.4), "null")
      )
    )
  )
  grid::pushViewport(grid::viewport(layout.pos.row = 1, layout.pos.col = 1))
  grid::grid.draw(growth_grob)
  grid::popViewport()
  grid::pushViewport(grid::viewport(layout.pos.row = 2, layout.pos.col = 1))
  grid::grid.draw(status_grob)
  grid::popViewport(2)
}

draw_comparison_plot()

png(
  filename = "Results/micom_fba/figures/cobrapy_vs_micom_baseline_growth_comparison.png",
  width = 15,
  height = 8,
  units = "in",
  res = 300
)
draw_comparison_plot()
dev.off()

