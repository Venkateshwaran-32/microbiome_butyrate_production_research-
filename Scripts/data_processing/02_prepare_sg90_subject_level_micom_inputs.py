from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUBJECT_UTILS_PATH = PROJECT_ROOT / "Scripts" / "modelling" / "00_subject_level_micom_utils.py"
SUBJECT_UTILS_SPEC = importlib.util.spec_from_file_location("subject_level_micom_utils", SUBJECT_UTILS_PATH)
if SUBJECT_UTILS_SPEC is None or SUBJECT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load subject-level utility module from {SUBJECT_UTILS_PATH}")
SUBJECT_UTILS_MODULE = importlib.util.module_from_spec(SUBJECT_UTILS_SPEC)
SUBJECT_UTILS_SPEC.loader.exec_module(SUBJECT_UTILS_MODULE)

METADATA_XLSX = SUBJECT_UTILS_MODULE.METADATA_XLSX
ABUNDANCE_XLSX = SUBJECT_UTILS_MODULE.ABUNDANCE_XLSX
TARGET_SPECIES = SUBJECT_UTILS_MODULE.TARGET_SPECIES
build_missing_subject_audit_row = SUBJECT_UTILS_MODULE.build_missing_subject_audit_row
build_missing_subject_qc_row = SUBJECT_UTILS_MODULE.build_missing_subject_qc_row
build_subject_lookup_row = SUBJECT_UTILS_MODULE.build_subject_lookup_row
build_subject_presence_matrix_row = SUBJECT_UTILS_MODULE.build_subject_presence_matrix_row
build_subject_qc_row = SUBJECT_UTILS_MODULE.build_subject_qc_row
build_subject_taxonomy_rows = SUBJECT_UTILS_MODULE.build_subject_taxonomy_rows
load_sg90_metadata = SUBJECT_UTILS_MODULE.load_sg90_metadata
load_sg90_subject_rows_from_abundance_workbook = SUBJECT_UTILS_MODULE.load_sg90_subject_rows_from_abundance_workbook
target_model_species_ids_in_order = SUBJECT_UTILS_MODULE.target_model_species_ids_in_order
validate_subject_rows = SUBJECT_UTILS_MODULE.validate_subject_rows


OUTPUT_DIR = Path("Suplementary_Data/processed_data/subject_level_micom_sg90")
TAXONOMY_OUTPUT = OUTPUT_DIR / "sg90_subject_taxonomy_for_micom.csv"
QC_OUTPUT = OUTPUT_DIR / "sg90_subject_input_qc_summary.csv"
FILTERING_OUTPUT = OUTPUT_DIR / "sg90_subject_filtering_summary.csv"
LOOKUP_OUTPUT = OUTPUT_DIR / "sg90_subject_to_agegroup_lookup.csv"
PRESENCE_OUTPUT = OUTPUT_DIR / "sg90_subject_taxon_presence_matrix.csv"
MISSING_OUTPUT = OUTPUT_DIR / "sg90_subjects_missing_from_abundance_workbook.csv"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    metadata_by_subject = load_sg90_metadata(METADATA_XLSX)
    subject_rows_by_subject, found_species = load_sg90_subject_rows_from_abundance_workbook(
        metadata_by_subject,
        ABUNDANCE_XLSX,
    )

    missing_species = sorted(set(TARGET_SPECIES) - found_species)
    if missing_species:
        raise ValueError(
            "Missing target species columns in the raw abundance workbook: " + ", ".join(missing_species)
        )

    taxonomy_rows: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []
    filtering_rows: list[dict[str, object]] = []
    lookup_rows: list[dict[str, object]] = []
    presence_rows: list[dict[str, object]] = []
    missing_rows: list[dict[str, object]] = []

    missing_reason = "missing_from_abundance_workbook"

    for subject_id, subject_metadata in metadata_by_subject.items():
        subject_rows = subject_rows_by_subject.get(subject_id)
        if subject_rows is None:
            qc_rows.append(build_missing_subject_qc_row(subject_metadata, exclusion_reason=missing_reason))
            filtering_rows.append(
                build_subject_lookup_row(
                    subject_metadata,
                    has_abundance_workbook_row=False,
                    include_in_subject_micom=False,
                    exclusion_reason=missing_reason,
                )
            )
            lookup_rows.append(
                build_subject_lookup_row(
                    subject_metadata,
                    has_abundance_workbook_row=False,
                    include_in_subject_micom=False,
                    exclusion_reason=missing_reason,
                )
            )
            missing_rows.append(build_missing_subject_audit_row(subject_metadata, exclusion_reason=missing_reason))
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
    missing_fieldnames = [
        "subject_id",
        "cohort",
        "age_years",
        "age_group",
        "gender",
        "sequencer",
        "exclusion_reason",
    ]

    write_csv(TAXONOMY_OUTPUT, taxonomy_fieldnames, taxonomy_rows)
    write_csv(QC_OUTPUT, qc_fieldnames, qc_rows)
    write_csv(FILTERING_OUTPUT, lookup_fieldnames, filtering_rows)
    write_csv(LOOKUP_OUTPUT, lookup_fieldnames, lookup_rows)
    write_csv(PRESENCE_OUTPUT, presence_fieldnames, presence_rows)
    write_csv(MISSING_OUTPUT, missing_fieldnames, missing_rows)

    included_subjects = sum(str(row["include_in_subject_micom"]) == "True" for row in qc_rows)
    excluded_subjects = len(qc_rows) - included_subjects
    print(f"Recovered {len(metadata_by_subject)} SG90 subjects from raw metadata")
    print(f"Subjects with raw abundance rows: {included_subjects}")
    print(f"Subjects missing from abundance workbook: {excluded_subjects}")
    print(f"Wrote {TAXONOMY_OUTPUT}")
    print(f"Wrote {QC_OUTPUT}")
    print(f"Wrote {FILTERING_OUTPUT}")
    print(f"Wrote {LOOKUP_OUTPUT}")
    print(f"Wrote {PRESENCE_OUTPUT}")
    print(f"Wrote {MISSING_OUTPUT}")


if __name__ == "__main__":
    main()
