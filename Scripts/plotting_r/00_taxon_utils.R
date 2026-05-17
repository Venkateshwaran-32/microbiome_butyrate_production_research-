strip_strain <- function(taxon_id) {
  taxon_id |>
    gsub("_", " ", x = _) |>
    sub("^([A-Za-z]+\\s+[A-Za-z]+).*$", "\\1", x = _)
}

abbreviate_taxon_one <- function(organism_name, delimiter = "[ _\\-]+") {
  words <- unlist(strsplit(organism_name, delimiter))
  if (length(words) >= 2) {
    return(paste0(substr(words[1], 1, 1), ". ", words[2]))
  }
  organism_name
}

abbreviate_taxon <- function(organism_name, delimiter = "[ _\\-]+") {
  vapply(organism_name, abbreviate_taxon_one, FUN.VALUE = character(1),
         delimiter = delimiter, USE.NAMES = FALSE)
}

italicize_taxon <- function(organism_name) {
  abbreviate_taxon(organism_name)
}
