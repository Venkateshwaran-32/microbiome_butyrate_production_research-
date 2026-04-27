pacman::p_load(tidyverse, ggrepel)
this.path::here() %>% setwd()
rm(list=ls())

medium <- read_csv("diet.csv")

head(medium)
ggplot( medium , aes(x = high_fiber , y = western , label = metabolite_name ))






ggplot(medium, aes(x = high_fiber, y = western, label = metabolite_name)) +
  geom_point() +
  scale_x_log10() +
  scale_y_log10() +
  geom_text_repel(size = 5) +
  geom_abline(intercept = 0, slope = 1, col = "blue") +
  theme_classic(base_size = 18)


view(medium)
