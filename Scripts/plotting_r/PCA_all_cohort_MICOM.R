setwd("/Users/taknev/Desktop/microbiome_butyrate_production_research")
pacman::p_load(tidyverse, janitor, broom, ggfortify, ggrepel)
rm(list = ls())

MICOM <- read_csv("Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv")
summary(MICOM)

glimpse(MICOM) # much better to understand 

MICOM %>%
  select(subject_id, taxon_id, reaction_id, flux, abs_flux, is_medium) %>%
  head(10)


MICOM_no_medium <- MICOM %>%
  filter(is_medium == FALSE)  # only internal reactions not the medium ones 

nrow(MICOM) #1930299
nrow(MICOM_no_medium) # 1,847,120

MICOM_only_medium <- MICOM %>%
  filter(is_medium == TRUE)  #  only reactions in the medium compartment 

nrow(MICOM_only_medium) # 83179

rm(MICOM_only_medium, MICOM)


# starting PCA here  ------------------------------------------------------

reaction_flux <- MICOM_no_medium %>%
  
  group_by(subject_id, reaction_id) %>%
  
  summarise(flux = sum(flux, na.rm = TRUE),  .groups = "drop") %>% 
  
  pivot_wider(names_from = reaction_id, values_from = flux, values_fill = 0) %>% 
  
  column_to_rownames("subject_id")

dim(reaction_flux)


glimpse(subject_reaction_matrix)
#    Rows: 516
#    Columns: 4,565 
#    516 * 4565 = 2355540

# so now there is like 4564 features , which are the reactions , and the subjects with similar levels of the reactions can get clustered with each other
# changing subject id to rownames----
pca_matrix <- subject_reaction_matrix %>%
  column_to_rownames("subject_id") %>%
  as.matrix()

pca_matrix[1:5, 1:5]

dim(pca_matrix) #  516 4564


pc <- prcomp(pca_matrix, scale. = TRUE)
pc$sdev
pc$sdev^2

pc_var <- pc$sdev^2

pc_var_percent <- pc_var / sum(pc_var)

head(pc_var)
head(pc_var_percent)

summary(pc)

# scree plot of the variances  --------------------------------------------
screeplot(pc, type = "barplot")


# ggplot of pc1 and pc2  --------------------------------------------------

pc_scores <- as.data.frame(pc$x) %>%
  rownames_to_column("subject_id")

metadata <- MICOM %>%
  distinct(subject_id, cohort, age_group)

pc_scores <- pc_scores %>%
  left_join(metadata, by = "subject_id")

ggplot(pc_scores, aes(x = PC1, y = PC2, color = cohort)) +
  geom_point() +
  theme_minimal()
# zoom in 

ggplot(pc_scores, aes(x = PC1, y = PC2, color = cohort)) +
  geom_point(alpha = 0.7) +
  coord_cartesian(
    xlim = quantile(pc_scores$PC1, c(0.02, 0.98)),
    ylim = quantile(pc_scores$PC2, c(0.02, 0.98))
  ) +
  theme_minimal()



