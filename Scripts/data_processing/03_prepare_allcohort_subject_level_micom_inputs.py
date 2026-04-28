from __future__ import annotations

import csv
import importlib.util
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUBJECT_UTILS_PATH = PROJECT_ROOT / "Scripts" / "modelling" / "00_subject_level_micom_utils.py"
SUBJECT_UTILS_SPEC = importlib.util.spec_from_file_location("subject_level_micom_utils", SUBJECT_UTILS_PATH)
if SUBJECT_UTILS_SPEC is None or SUBJECT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load subject-level utility module from {SUBJECT_UTILS_PATH}")
SUBJECT_UTILS_MODULE = importlib.util.module_from_spec(SUBJECT_UTILS_SPEC)
SUBJECT_UTILS_SPEC.loader.exec_module(SUBJECT_UTILS_MODULE)

ABUNDANCE_XLSX = SUBJECT_UTILS_MODULE.ABUNDANCE_XLSX
ALLCOHORT_AGE_GROUPS = SUBJECT_UTILS_MODULE.ALLCOHORT_AGE_GROUPS
METADATA_XLSX = SUBJECT_UTILS_MODULE.METADATA_XLSX
TARGET_SPECIES = SUBJECT_UTILS_MODULE.TARGET_SPECIES
build_abundance_subject_missing_metadata_row = SUBJECT_UTILS_MODULE.build_abundance_subject_missing_metadata_row
build_missing_subject_audit_row = SUBJECT_UTILS_MODULE.build_missing_subject_audit_row
build_missing_subject_qc_row = SUBJECT_UTILS_MODULE.build_missing_subject_qc_row
build_subject_lookup_row = SUBJECT_UTILS_MODULE.build_subject_lookup_row
build_subject_presence_matrix_row = SUBJECT_UTILS_MODULE.build_subject_presence_matrix_row
build_subject_qc_row = SUBJECT_UTILS_MODULE.build_subject_qc_row
build_subject_taxonomy_rows = SUBJECT_UTILS_MODULE.build_subject_taxonomy_rows
load_abundance_workbook_subject_ids = SUBJECT_UTILS_MODULE.load_abundance_workbook_subject_ids
load_allcohort_metadata = SUBJECT_UTILS_MODULE.load_allcohort_metadata
load_subject_rows_from_abundance_workbook = SUBJECT_UTILS_MODULE.load_subject_rows_from_abundance_workbook
target_model_species_ids_in_order = SUBJECT_UTILS_MODULE.target_model_species_ids_in_order
validate_subject_rows = SUBJECT_UTILS_MODULE.validate_subject_rows


OUTPUT_DIR = Path("Suplementary_Data/processed_data/subject_level_micom_allcohort")
TAXONOMY_OUTPUT = OUTPUT_DIR / "allcohort_subject_taxonomy_for_micom.csv"
QC_OUTPUT = OUTPUT_DIR / "allcohort_subject_input_qc_summary.csv"
LOOKUP_OUTPUT = OUTPUT_DIR / "allcohort_subject_to_agegroup_lookup.csv"
PRESENCE_OUTPUT = OUTPUT_DIR / "allcohort_subject_taxon_presence_matrix.csv"
MISSING_ABUNDANCE_OUTPUT = OUTPUT_DIR / "allcohort_metadata_subjects_missing_from_abundance_workbook.csv"
MISSING_METADATA_OUTPUT = OUTPUT_DIR / "allcohort_abundance_subjects_missing_from_metadata.csv"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    metadata_by_subject = load_allcohort_metadata(METADATA_XLSX, allowed_age_groups=ALLCOHORT_AGE_GROUPS)
    subject_rows_by_subject, found_species = load_subject_rows_from_abundance_workbook(
        metadata_by_subject,
        ABUNDANCE_XLSX,
    )
    abundance_subject_ids = set(load_abundance_workbook_subject_ids(ABUNDANCE_XLSX))

    missing_species = sorted(set(TARGET_SPECIES) - found_species)
    if missing_species:
        raise ValueError(
            "Missing target species columns in the raw abundance workbook: " + ", ".join(missing_species)
        )

    metadata_subject_ids = set(metadata_by_subject)
    abundance_subjects_missing_metadata = sorted(abundance_subject_ids - metadata_subject_ids)
    metadata_subjects_missing_abundance = sorted(metadata_subject_ids - set(subject_rows_by_subject))

    taxonomy_rows: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []
    lookup_rows: list[dict[str, object]] = []
    presence_rows: list[dict[str, object]] = []
    missing_abundance_rows: list[dict[str, object]] = []
    missing_metadata_rows: list[dict[str, object]] = []

    missing_abundance_reason = "missing_from_abundance_workbook"
    missing_metadata_reason = "missing_from_metadata"

    for subject_id, subject_metadata in metadata_by_subject.items():
        subject_rows = subject_rows_by_subject.get(subject_id)
        if subject_rows is None:
            qc_rows.append(build_missing_subject_qc_row(subject_metadata, exclusion_reason=missing_abundance_reason))
            lookup_rows.append(
                build_subject_lookup_row(
                    subject_metadata,
                    has_abundance_workbook_row=False,
                    include_in_subject_micom=False,
                    exclusion_reason=missing_abundance_reason,
                )
            )
            missing_abundance_rows.append(
                build_missing_subject_audit_row(subject_metadata, exclusion_reason=missing_abundance_reason)
            )
            continue

        validate_subject_rows(subject_id, subject_rows)
        subject_taxonomy_rows = build_subject_taxonomy_rows(subject_rows)
        if len(subject_taxonomy_rows) != len(TARGET_SPECIES):
            raise ValueError(
                f"Expected {len(TARGET_SPECIES)} processed taxonomy rows for {subject_id}, "
                f"found {len(subject_taxonomy_rows)}"
            )

        taxonomy_rows.extend(subject_taxonomy_rows)
        qc_rows.append(
            build_subject_qc_row(
                subject_rows,
                has_abundance_workbook_row=True,
                include_in_subject_micom=True,
                exclusion_reason="",
            )
        )
        lookup_rows.append(
            build_subject_lookup_row(
                subject_metadata,
                has_abundance_workbook_row=True,
                include_in_subject_micom=True,
                exclusion_reason="",
            )
        )
        presence_rows.append(build_subject_presence_matrix_row(subject_rows))

    for subject_id in abundance_subjects_missing_metadata:
        missing_metadata_rows.append(
            build_abundance_subject_missing_metadata_row(
                subject_id,
                exclusion_reason=missing_metadata_reason,
            )
        )

    taxonomy_fieldnames = [
        "sample_id",
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "species_name",
        "paper_taxon",
        "abundance_raw",
        "abundance_normalized",
        "model_file",
        "model_species_id",
    ]
    qc_fieldnames = [
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "has_abundance_workbook_row",
        "include_in_subject_micom",
        "exclusion_reason",
        "n_modeled_taxa_total",
        "n_nonzero_modeled_taxa",
        "total_modeled_abundance_raw",
        "total_modeled_abundance_normalized",
        "all_modeled_taxa_zero",
    ]
    lookup_fieldnames = [
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "gender",
        "sequencer",
        "has_abundance_workbook_row",
        "include_in_subject_micom",
        "exclusion_reason",
    ]
    presence_fieldnames = [
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "n_nonzero_modeled_taxa",
        *target_model_species_ids_in_order(),
    ]
    missing_abundance_fieldnames = [
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "gender",
        "sequencer",
        "exclusion_reason",
    ]
    missing_metadata_fieldnames = [
        "subject_id",
        "exclusion_reason",
    ]

    write_csv(TAXONOMY_OUTPUT, taxonomy_fieldnames, taxonomy_rows)
    write_csv(QC_OUTPUT, qc_fieldnames, qc_rows)
    write_csv(LOOKUP_OUTPUT, lookup_fieldnames, lookup_rows)
    write_csv(PRESENCE_OUTPUT, presence_fieldnames, presence_rows)
    write_csv(MISSING_ABUNDANCE_OUTPUT, missing_abundance_fieldnames, missing_abundance_rows)
    write_csv(MISSING_METADATA_OUTPUT, missing_metadata_fieldnames, missing_metadata_rows)

    included_qc_rows = [row for row in qc_rows if str(row["include_in_subject_micom"]) == "True"]
    included_cohort_counts = Counter(str(row["cohort"]) for row in included_qc_rows)
    included_age_counts = Counter(str(row["age_group"]) for row in included_qc_rows)
    zero_total_abundance_subjects = [
        row["subject_id"]
        for row in included_qc_rows
        if float(row["total_modeled_abundance_raw"]) <= 0
    ]

    print(f"Recovered {len(metadata_by_subject)} all-cohort metadata subjects across {ALLCOHORT_AGE_GROUPS}")
    print(f"Subjects with abundance workbook rows: {len(included_qc_rows)}")
    print(f"Metadata subjects missing abundance rows: {len(missing_abundance_rows)}")
    print(f"Abundance subjects missing metadata rows: {len(missing_metadata_rows)}")
    print(
        "Included cohort counts: "
        + ", ".join(f"{cohort}={included_cohort_counts[cohort]}" for cohort in sorted(included_cohort_counts))
    )
    print(
        "Included age-group counts: "
        + ", ".join(f"{age_group}={included_age_counts[age_group]}" for age_group in ALLCOHORT_AGE_GROUPS)
    )
    print(f"Subjects with zero total modeled abundance: {len(zero_total_abundance_subjects)}")
    print(f"Wrote {TAXONOMY_OUTPUT}")
    print(f"Wrote {QC_OUTPUT}")
    print(f"Wrote {LOOKUP_OUTPUT}")
    print(f"Wrote {PRESENCE_OUTPUT}")
    print(f"Wrote {MISSING_ABUNDANCE_OUTPUT}")
    print(f"Wrote {MISSING_METADATA_OUTPUT}")


if __name__ == "__main__":
    main()
