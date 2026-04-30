read_csv_header <- function(path) {
  first_line <- readLines(path, n = 1L, warn = FALSE)
  strsplit(first_line, ",", fixed = TRUE)[[1]]
}

wrap_prefixed_line <- function(prefix, text, width = 100) {
  wrapped <- strwrap(
    text,
    width = width,
    exdent = nchar(prefix),
    simplify = FALSE
  )[[1]]
  if (length(wrapped) == 0) {
    return(prefix)
  }
  c(
    paste0(prefix, wrapped[1]),
    if (length(wrapped) > 1) {
      paste0(strrep(" ", nchar(prefix)), wrapped[-1])
    } else {
      character(0)
    }
  )
}

validate_report_output_dictionary <- function(specs) {
  for (spec in specs) {
    header <- read_csv_header(spec$path)
    fixed_header <- vapply(spec$columns, `[[`, character(1), "name")

    if (is.null(spec$dynamic_columns)) {
      if (!identical(header, fixed_header)) {
        stop(
          sprintf(
            "Header mismatch for %s. Expected %s, found %s",
            spec$path,
            paste(fixed_header, collapse = ", "),
            paste(header, collapse = ", ")
          )
        )
      }
    } else {
      prefix <- header[seq_along(fixed_header)]
      if (!identical(prefix, fixed_header)) {
        stop(
          sprintf(
            "Header prefix mismatch for %s. Expected %s, found %s",
            spec$path,
            paste(fixed_header, collapse = ", "),
            paste(header, collapse = ", ")
          )
        )
      }
      if (length(header) <= length(fixed_header)) {
        stop(sprintf("Expected dynamic columns after fixed prefix in %s", spec$path))
      }
    }
  }
}

render_csv_output_dictionary <- function(specs) {
  validate_report_output_dictionary(specs)
  lines <- c("CSV Output Dictionary", "")

  for (index in seq_along(specs)) {
    spec <- specs[[index]]
    header <- read_csv_header(spec$path)

    lines <- c(
      lines,
      basename(spec$path),
      paste("Path:", spec$path),
      paste("Row grain:", spec$row_grain),
      "Columns:"
    )

    for (column in spec$columns) {
      text <- paste0(column$name, ": ", column$meaning)
      if (!is.null(column$formula) && nzchar(column$formula)) {
        text <- paste0(text, " Formula: ", column$formula)
      }
      lines <- c(lines, wrap_prefixed_line("- ", text))
    }

    if (!is.null(spec$dynamic_columns)) {
      dynamic_header <- header[(length(spec$columns) + 1):length(header)]
      dynamic_text <- paste0(
        spec$dynamic_columns$label,
        " (",
        length(dynamic_header),
        " total): ",
        spec$dynamic_columns$meaning,
        " Exact column names: ",
        paste(dynamic_header, collapse = ", ")
      )
      if (!is.null(spec$dynamic_columns$formula) && nzchar(spec$dynamic_columns$formula)) {
        dynamic_text <- paste0(dynamic_text, " Formula: ", spec$dynamic_columns$formula)
      }
      lines <- c(lines, wrap_prefixed_line("- ", dynamic_text))
    }

    if (index != length(specs)) {
      lines <- c(lines, "")
    }
  }

  lines
}

strip_existing_csv_output_dictionary <- function(report_lines) {
  marker_index <- match("CSV Output Dictionary", report_lines)
  if (is.na(marker_index)) {
    return(trimws(report_lines, which = "right"))
  }
  trimws(report_lines[seq_len(marker_index - 1L)], which = "right")
}

append_csv_output_dictionary_to_lines <- function(report_lines, specs) {
  base_lines <- strip_existing_csv_output_dictionary(report_lines)
  dictionary_lines <- render_csv_output_dictionary(specs)
  c(base_lines, "", dictionary_lines)
}
