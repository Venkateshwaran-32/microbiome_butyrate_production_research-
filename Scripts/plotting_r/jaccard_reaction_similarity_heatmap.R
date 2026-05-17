setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, ggtext)
library(ggtext)
rm(list = ls())
source("Scripts/plotting_r/00_taxon_utils.R")

# --- Load long-format pairwise Jaccard table from script 07. ---
jaccard_long <- read_csv(
  "Results/cobrapy_fba/tables/07_jaccard_reaction_pairs_long.csv",
  show_col_types = FALSE
)

# --- Hierarchical clustering on 1 - Jaccard (average linkage). ---
# Pivot to a wide numeric matrix keyed by species_a x species_b.
jaccard_wide <- jaccard_long %>%
  select(species_a, species_b, jaccard) %>%
  pivot_wider(names_from = species_b, values_from = jaccard)

species_ids <- jaccard_wide$species_a
jaccard_matrix <- as.matrix(jaccard_wide %>% select(-species_a))
rownames(jaccard_matrix) <- species_ids

# Reorder columns to match rows (defensive — script 07 writes the same order, but
# hclust requires a square matrix with consistent row/col labels).
jaccard_matrix <- jaccard_matrix[, species_ids]

dist_mat <- as.dist(1 - jaccard_matrix)
hc <- hclust(dist_mat, method = "average")
species_order <- hc$labels[hc$order]

# --- Build a display label table: keep the file-stem ID as the join key and
# generate the human-readable italicised abbreviation for axis printing. ---
strip_strain <- function(taxon_id) {
  taxon_id |>
    gsub("_", " ", x = _) |>
    sub("^([A-Za-z]+\\s+[A-Za-z]+).*$", "\\1", x = _)
}

species_display <- tibble(species_id = species_order) %>%
  mutate(
    species_label = italicize_taxon(strip_strain(species_id))
  )

# --- Prepare plot data with factor-encoded axes in the clustered order. ---
plot_data <- jaccard_long %>%
  mutate(
    species_a = factor(species_a, levels = species_order),
    species_b = factor(species_b, levels = species_order)
  ) %>%
  left_join(species_display, by = c("species_a" = "species_id")) %>%
  rename(label_a = species_label) %>%
  left_join(species_display, by = c("species_b" = "species_id")) %>%
  rename(label_b = species_label)

# --- Build the heatmap. ---
heatmap_plot <- ggplot(
  plot_data,
  aes(x = species_a, y = species_b, fill = jaccard)
) +
  geom_tile(color = "white", linewidth = 0.7) +
  geom_text(
    aes(label = sprintf("%.2f", jaccard), color = jaccard > 0.55),
    size = 3.2,
    show.legend = FALSE
  ) +
  scale_fill_gradient(
    low = "#F4EFE8",
    high = "#3F2417",
    limits = c(0, 1),
    breaks = c(0, 0.25, 0.5, 0.75, 1),
    name = "Jaccard\nsimilarity"
  ) +
  scale_color_manual(
    values = c(`TRUE` = "#F4EFE8", `FALSE` = "#2B2B2B")
  ) +
  scale_x_discrete(
    labels = setNames(species_display$species_label, species_display$species_id),
    expand = c(0, 0)
  ) +
  scale_y_discrete(
    labels = setNames(species_display$species_label, species_display$species_id),
    expand = c(0, 0)
  ) +
  coord_fixed() +
  labs(
    x = NULL,
    y = NULL,
    title = "Reaction-set Jaccard similarity across the 10 AGORA2 species",
    subtitle = "Rows and columns ordered by hierarchical clustering on (1 - Jaccard)."
  ) +
  theme_minimal(base_size = 11) +
  theme(
    axis.text.x      = ggtext::element_markdown(angle = 45, hjust = 1, color = "#2B2B2B"),
    axis.text.y      = ggtext::element_markdown(color = "#2B2B2B"),
    plot.title       = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle    = element_text(color = "#4A4A4A"),
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background  = element_rect(fill = "white", color = NA),
    panel.border     = element_rect(color = "#2B2B2B", fill = NA, linewidth = 0.8),
    legend.position  = "right",
    legend.title     = element_text(face = "bold", color = "#1F1F1F"),
    legend.text      = element_text(color = "#2B2B2B")
  )

print(heatmap_plot)

dir.create("Results/cobrapy_fba/figures", recursive = TRUE, showWarnings = FALSE)
ggsave(
  filename = "Results/cobrapy_fba/figures/07_jaccard_reaction_similarity_heatmap.png",
  plot     = heatmap_plot,
  width    = 8,
  height   = 7,
  dpi      = 600
)

cat("Species order from hierarchical clustering:\n")
for (sp in species_order) cat("  ", sp, "\n")

