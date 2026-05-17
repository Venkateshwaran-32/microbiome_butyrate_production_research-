setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, ggtext, scales)

subject_level <- read_csv(
  "Suplementary_Data/processed_data/subject_level_abundance_10_species.csv",
  show_col_types = FALSE
)

age_bin_levels <- c("21_40", "41_60", "61_70", "71_80", "81_90", "91_100")
cohort_levels  <- c("T2D", "CRE", "SPMP", "SG90")

cohort_colors <- c(
  "T2D"  = "#C65D00",
  "CRE"  = "#1B7837",
  "SPMP" = "#5B2A86",
  "SG90" = "#1F4E5F"
)

cohort_composition <- subject_level %>%
  distinct(subject_id, cohort, age_group) %>%
  count(age_group, cohort, name = "n") %>%
  group_by(age_group) %>%
  mutate(
    n_total = sum(n),
    frac    = n / n_total
  ) %>%
  ungroup() %>%
  mutate(
    age_group = factor(age_group, levels = age_bin_levels),
    cohort    = factor(cohort,    levels = cohort_levels)
  )

age_bin_totals <- cohort_composition %>%
  distinct(age_group, n_total)

strip_plot <- ggplot(
  cohort_composition,
  aes(x = age_group, y = frac, fill = cohort)
) +
  geom_col(width = 0.78) +
  geom_text(
    data = age_bin_totals,
    aes(x = age_group, y = 1.04, label = paste0("n=", n_total)),
    inherit.aes = FALSE,
    size = 3.2,
    color = "#1F1F1F",
    fontface = "bold"
  ) +
  scale_fill_manual(values = cohort_colors, name = "Cohort", drop = FALSE) +
  scale_y_continuous(
    expand = c(0, 0),
    limits = c(0, 1.10),
    breaks = c(0, 0.5, 1),
    labels = scales::percent_format(accuracy = 1)
  ) +
  labs(
    x = NULL,
    y = "Cohort\nfraction",
    title = "Cohort composition by age bin (preview strip)",
    subtitle = "Each bar is the share of subjects from each cohort within that age bin (n shown above)."
  ) +
  theme_minimal(base_size = 11) +
  theme(
    axis.text.x      = element_text(color = "#2B2B2B"),
    axis.text.y      = element_text(color = "#2B2B2B"),
    axis.title.y     = element_text(color = "#2B2B2B"),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.border     = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.7),
    plot.title       = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle    = element_text(color = "#4A4A4A"),
    legend.position  = "right",
    legend.title     = element_text(face = "bold", color = "#1F1F1F"),
    legend.text      = element_text(color = "#2B2B2B")
  )

print(strip_plot)
print(cohort_composition)

dir.create("Results/qc/figures", recursive = TRUE, showWarnings = FALSE)

ggsave(
  filename = "Results/qc/figures/cohort_composition_strip_preview.png",
  plot     = strip_plot,
  width    = 11,
  height   = 3.2,
  dpi      = 300
)
