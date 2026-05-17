pacman::p_load(tidyverse, ggrepel)
this.path::here() %>% setwd()
rm(list = ls())

medium <- read_csv("diet.csv", show_col_types = FALSE)

head(medium)

medium_scatter <- ggplot(
  medium,
  aes(x = high_fiber, y = western, label = metabolite_name)
) +
  geom_point(size = 1.8, alpha = 0.8, color = "#2B2B2B") +
  geom_abline(intercept = 0, slope = 1, color = "#1F77B4", linetype = "dashed", linewidth = 0.6) +
  geom_text_repel(
    size = 3,
    max.overlaps = 25,
    segment.size = 0.25,
    segment.color = "gray60",
    min.segment.length = 0
  ) +
  scale_x_log10() +
  scale_y_log10() +
  labs(
    x = "High-fiber diet uptake bound (log10 scale, mmol/gDW/h)",
    y = "Western diet uptake bound (log10 scale, mmol/gDW/h)",
    title = "Diet metabolite uptake bounds: high-fiber vs western",
    subtitle = "Each point is one metabolite from Medium_files/diet.csv. Dashed blue line = y = x."
  ) +
  theme_classic(base_size = 13) +
  theme(
    plot.title    = element_text(face = "bold", color = "#1F1F1F"),
    plot.subtitle = element_text(color = "#4A4A4A"),
    axis.title    = element_text(color = "#2B2B2B"),
    axis.text     = element_text(color = "#2B2B2B")
  )

print(medium_scatter)

ggsave(
  filename = "medium_scatterplot.png",
  plot     = medium_scatter,
  width    = 10,
  height   = 8,
  dpi      = 600
)
