setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, janitor, broom, ggfortify, ggrepel)
rm(list = ls())
options(max.print = 10000)

# Data input and exploration ----------------------------------------------
MICOM <- read_csv("Results/subject_level_fba/tables/09_allcohort_subject_reaction_flux_nonzero_long_high_fiber_no_pfba.csv")
summary(MICOM)

glimpse(MICOM) # much better to understand 

MICOM %>%
  select(subject_id, taxon_id, reaction_id, flux, abs_flux, is_medium) %>%
  head(10)

MICOM %>% 
  tabyl(is_medium). # 83179 are in the medium, 1.8m are in the internal reaction



# Data reshaping ----------------------------------------------------------

reaction_flux <- MICOM %>%
  
  filter(is_medium == FALSE)  %>%                                                #  only internal reactions (i.e. not in the medium)

  group_by(subject_id, reaction_id) %>%
  
  summarise(flux = sum(flux, na.rm = TRUE),  .groups = "drop") %>% 
  
  pivot_wider(names_from = reaction_id, values_from = flux, values_fill = 0) %>% 
  
  column_to_rownames("subject_id") %>% 

  as.matrix()


dim(reaction_flux) # 516 subjects and 4564 reactions

openxlsx::write.xlsx(reaction_flux %>% data.frame() %>% rownames_to_column("subject_id"), 
                     file = "Results/reaction_flux.xlsx")



# QC on the reaction flux matrix ------------------------------------------
MASS::truehist( c(reaction_flux) )

MASS::truehist( rs <- rowSums(reaction_flux) )

## by subject ----
sort(rs, decreasing = TRUE) %>% head(10)
#      MBS1232      MBS1529      MBS1262       MHS276      MBS1539      MBS1438      MBS1576      MBS1503      MBS1515      MBS1586 
# 22739341.447  5495536.637  1999011.316   188201.167   139092.519    43446.573     7395.848     4878.600     4747.044     4404.576 

reaction_flux[ "MBS1232", ] %>% sort(decreasing = TRUE) %>% tail(20)


MASS::truehist( colSums(reaction_flux) )  # by variable




# Principal component analysis --------------------------------------------

pc <- prcomp(reaction_flux, scale. = TRUE)

plot(pc, n = 30)

pc_var <- pc$sdev^2
pc_var_percent <- pc_var / sum(pc_var)

plot(1:516, cumsum(pc_var_percent))

which( cumsum(pc_var_percent) > 0.7 ) %>% min()  # first 20 PC explain at least 70% of the variation in the data

screeplot(pc, type = "barplot", npcs = 516)



# ggplot of pc1 and pc2  --------------------------------------------------
metadata <- MICOM %>%
  distinct(subject_id, cohort, age_years, age_group)

pc_scores <- as.data.frame(pc$x) %>%
  rownames_to_column("subject_id") %>% 
  left_join(metadata)

ggplot(pc_scores, aes(x = PC1, y = PC2, color = cohort)) +
  geom_point() +
  theme_minimal()

outliers <- pc_scores %>% 
  filter(PC1 > 400 | PC2 < -100) %>% 
  pull(subject_id)

reaction_flux[outliers, ]


ggplot(pc_scores, aes(x = PC1, y = PC2, color = cohort)) +
  geom_point(alpha = 0.7) +
  coord_cartesian(
    xlim = quantile(pc_scores$PC1, c(0.02, 0.98)),
    ylim = quantile(pc_scores$PC2, c(0.02, 0.98))
  ) +
  theme_minimal()



