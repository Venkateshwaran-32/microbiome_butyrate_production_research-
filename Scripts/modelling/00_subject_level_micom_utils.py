from __future__ import annotations

import csv
import importlib.util
from collections import defaultdict
from pathlib import Path

PREP_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "data_processing" / "01_prepare_supplementary_agebin_inputs.py"
PREP_SPEC = importlib.util.spec_from_file_location("prepare_agebin_inputs", PREP_SCRIPT_PATH)
if PREP_SPEC is None or PREP_SPEC.loader is None:
    raise ImportError(f"Could not load preprocessing helpers from {PREP_SCRIPT_PATH}")
PREP_MODULE = importlib.util.module_from_spec(PREP_SPEC)
PREP_SPEC.loader.exec_module(PREP_MODULE)


ALLCOHORT_AGE_GROUPS = ("21_40", "41_60", "61_70", "71_80", "81_90", "91_100")
SUBJECT_LEVEL_TARGET_COHORT = "SG90"
SUBJECT_LEVEL_AGE_GROUPS = ("71_80", "81_90", "91_100")
METADATA_XLSX = Path("Suplementary_Data/Metadata_by_cohort.xlsx")
ABUNDANCE_XLSX = Path("Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx")
TARGET_SPECIES = PREP_MODULE.TARGET_SPECIES
EXPECTED_SPECIES_PER_SUBJECT = len(TARGET_SPECIES)


def read_sheet_rows(xlsx_path: Path, sheet_path: str) -> list[list[str]]:
    return PREP_MODULE.read_sheet_rows(xlsx_path, sheet_path)


def infer_cohort(subject_id: str, sequencer: str, age_value: str) -> str:
    return PREP_MODULE.infer_cohort(subject_id, sequencer, age_value)


def target_species_names_in_order() -> list[str]:
    return list(TARGET_SPECIES)


def target_model_species_ids_in_order() -> list[str]:
    return [TARGET_SPECIES[species_name]["model_species_id"] for species_name in target_species_names_in_order()]


def load_subject_level_rows(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def csv_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def filter_subject_level_rows(
    rows: list[dict[str, str]],
    *,
    cohort: str = SUBJECT_LEVEL_TARGET_COHORT,
    allowed_age_groups: tuple[str, ...] = SUBJECT_LEVEL_AGE_GROUPS,
) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["cohort"] == cohort and row["age_group"] in allowed_age_groups
    ]


def group_rows_by_subject(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["subject_id"]].append(row)
    return dict(sorted(grouped.items()))


def allcohort_age_group_from_years(age_value: str | float) -> str | None:
    try:
        age = float(age_value)
    except (TypeError, ValueError):
        return None
    if age < 21 or age > 100:
        return None
    if age <= 40:
        return "21_40"
    if age <= 60:
        return "41_60"
    if age <= 70:
        return "61_70"
    if age <= 80:
        return "71_80"
    if age <= 90:
        return "81_90"
    return "91_100"


def subject_level_age_group_from_years(age_value: str | float) -> str | None:
    age_group = allcohort_age_group_from_years(age_value)
    if age_group not in SUBJECT_LEVEL_AGE_GROUPS:
        return None
    return age_group


def _raw_abundance_from_row(row: dict[str, object]) -> float:
    if "abundance_raw" in row and row["abundance_raw"] not in {"", None}:
        return float(row["abundance_raw"])
    if "abundance" in row and row["abundance"] not in {"", None}:
        return float(row["abundance"])
    return 0.0


def _normalized_abundance_from_row(row: dict[str, object], total_abundance_raw: float) -> float:
    if "abundance_normalized" in row and row["abundance_normalized"] not in {"", None}:
        return float(row["abundance_normalized"])
    if total_abundance_raw <= 0:
        return 0.0
    return _raw_abundance_from_row(row) / total_abundance_raw


def load_allcohort_metadata(
    metadata_xlsx: Path = METADATA_XLSX,
    *,
    cohort: str | None = None,
    allowed_age_groups: tuple[str, ...] = ALLCOHORT_AGE_GROUPS,
) -> dict[str, dict[str, object]]:
    rows = read_sheet_rows(metadata_xlsx, "xl/worksheets/sheet1.xml")
    header = rows[0]
    subject_idx = header.index("Subject ID")
    age_idx = header.index("Age (in years)")
    gender_idx = header.index("Gender")
    sequencer_idx = header.index("Sequencer")

    metadata: dict[str, dict[str, object]] = {}
    for row in rows[1:]:
        if len(row) <= max(subject_idx, age_idx, gender_idx, sequencer_idx):
            continue
        subject_id = row[subject_idx].strip()
        age_value = row[age_idx].strip()
        if not subject_id or not age_value:
            continue

        sequencer = row[sequencer_idx].strip()
        inferred_cohort = infer_cohort(subject_id, sequencer, age_value)
        if cohort is not None and inferred_cohort != cohort:
            continue

        age_group = allcohort_age_group_from_years(age_value)
        if age_group is None:
            continue
        if age_group not in allowed_age_groups:
            continue

        metadata[subject_id] = {
            "subject_id": subject_id,
            "cohort": inferred_cohort,
            "age_years": float(age_value),
            "age_group": age_group,
            "gender": row[gender_idx].strip(),
            "sequencer": sequencer,
        }

    return dict(sorted(metadata.items()))


def load_sg90_metadata(metadata_xlsx: Path = METADATA_XLSX) -> dict[str, dict[str, object]]:
    metadata = load_allcohort_metadata(
        metadata_xlsx,
        cohort=SUBJECT_LEVEL_TARGET_COHORT,
        allowed_age_groups=SUBJECT_LEVEL_AGE_GROUPS,
    )
    for subject_id, subject_metadata in metadata.items():
        if subject_metadata["age_group"] not in SUBJECT_LEVEL_AGE_GROUPS:
            raise ValueError(
                f"SG90 subject {subject_id} has unsupported age_group {subject_metadata['age_group']}. "
                f"Expected one of {SUBJECT_LEVEL_AGE_GROUPS}."
            )
    return metadata


def load_subject_rows_from_abundance_workbook(
    metadata_by_subject: dict[str, dict[str, object]],
    abundance_xlsx: Path = ABUNDANCE_XLSX,
) -> tuple[dict[str, list[dict[str, object]]], set[str]]:
    rows = read_sheet_rows(abundance_xlsx, "xl/worksheets/sheet1.xml")
    header = rows[0]

    species_to_column: dict[str, int] = {}
    for idx, species_name in enumerate(header[1:], start=1):
        clean_name = species_name.strip()
        if clean_name in TARGET_SPECIES:
            species_to_column[clean_name] = idx

    missing_species_columns = sorted(set(TARGET_SPECIES) - set(species_to_column))
    if missing_species_columns:
        raise ValueError(
            "Missing target species columns in the raw abundance workbook: "
            + ", ".join(missing_species_columns)
        )

    subject_rows_by_subject: dict[str, list[dict[str, object]]] = {}
    found_species = set(species_to_column)

    for row in rows[1:]:
        if not row:
            continue
        subject_id = row[0].strip()
        if subject_id not in metadata_by_subject:
            continue
        if subject_id in subject_rows_by_subject:
            raise ValueError(f"Duplicate subject row found in abundance workbook: {subject_id}")

        meta = metadata_by_subject[subject_id]
        subject_rows: list[dict[str, object]] = []
        for species_name in target_species_names_in_order():
            column_idx = species_to_column[species_name]
            abundance_value = 0.0
            if column_idx < len(row) and row[column_idx] != "":
                abundance_value = float(row[column_idx])
            subject_rows.append(
                {
                    "subject_id": subject_id,
                    "cohort": meta["cohort"],
                    "age_years": meta["age_years"],
                    "age_group": meta["age_group"],
                    "species_name": species_name,
                    "paper_taxon": TARGET_SPECIES[species_name]["paper_taxon"],
                    "abundance": abundance_value,
                }
            )
        subject_rows_by_subject[subject_id] = subject_rows

    return dict(sorted(subject_rows_by_subject.items())), found_species


def load_abundance_workbook_subject_ids(abundance_xlsx: Path = ABUNDANCE_XLSX) -> list[str]:
    rows = read_sheet_rows(abundance_xlsx, "xl/worksheets/sheet1.xml")
    subject_ids: list[str] = []
    seen_subject_ids: set[str] = set()

    for row in rows[1:]:
        if not row:
            continue
        subject_id = row[0].strip()
        if not subject_id:
            continue
        if subject_id in seen_subject_ids:
            raise ValueError(f"Duplicate subject row found in abundance workbook: {subject_id}")
        seen_subject_ids.add(subject_id)
        subject_ids.append(subject_id)

    return subject_ids


def load_sg90_subject_rows_from_abundance_workbook(
    metadata_by_subject: dict[str, dict[str, object]],
    abundance_xlsx: Path = ABUNDANCE_XLSX,
) -> tuple[dict[str, list[dict[str, object]]], set[str]]:
    return load_subject_rows_from_abundance_workbook(metadata_by_subject, abundance_xlsx)


def enrich_subject_rows(subject_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    enriched_rows: list[dict[str, object]] = []
    total_abundance_raw = sum(_raw_abundance_from_row(row) for row in subject_rows)

    for row in subject_rows:
        species_name = str(row["species_name"])
        mapping = TARGET_SPECIES[species_name]
        abundance_raw = _raw_abundance_from_row(row)
        abundance_normalized = _normalized_abundance_from_row(row, total_abundance_raw)
        enriched_rows.append(
            {
                "sample_id": str(row.get("sample_id", row["subject_id"])),
                "subject_id": str(row["subject_id"]),
                "cohort": str(row["cohort"]),
                "age_years": float(row["age_years"]),
                "age_group": str(row["age_group"]),
                "species_name": species_name,
                "paper_taxon": str(row.get("paper_taxon", mapping["paper_taxon"])),
                "abundance_raw": abundance_raw,
                "abundance_normalized": abundance_normalized,
                "model_file": str(row.get("model_file", mapping["model_file"])),
                "model_species_id": str(row.get("model_species_id", mapping["model_species_id"])),
            }
        )

    return enriched_rows


def validate_subject_rows(
    subject_id: str,
    subject_rows: list[dict[str, object]],
    *,
    expected_species_per_subject: int = EXPECTED_SPECIES_PER_SUBJECT,
) -> list[str]:
    if len(subject_rows) != expected_species_per_subject:
        raise ValueError(
            f"Expected {expected_species_per_subject} rows for subject {subject_id}, found {len(subject_rows)}"
        )

    enriched_rows = enrich_subject_rows(subject_rows)
    species_names = {row["species_name"] for row in enriched_rows}
    if len(species_names) != expected_species_per_subject:
        raise ValueError(f"Subject {subject_id} contains duplicate species_name entries")

    model_ids = {row["model_species_id"] for row in enriched_rows}
    if len(model_ids) != expected_species_per_subject:
        raise ValueError(f"Subject {subject_id} contains duplicate model_species_id entries")

    missing_species = sorted(set(TARGET_SPECIES) - species_names)
    if missing_species:
        raise ValueError(f"Subject {subject_id} is missing expected species rows: {', '.join(missing_species)}")

    cohorts = {row["cohort"] for row in enriched_rows}
    if len(cohorts) != 1:
        raise ValueError(f"Subject {subject_id} contains multiple cohort labels: {sorted(cohorts)}")

    age_groups = {row["age_group"] for row in enriched_rows}
    if len(age_groups) != 1:
        raise ValueError(f"Subject {subject_id} contains multiple age_group labels: {sorted(age_groups)}")

    age_values = {row["age_years"] for row in enriched_rows}
    if len(age_values) != 1:
        raise ValueError(f"Subject {subject_id} contains multiple age_years values: {sorted(age_values)}")

    for row in enriched_rows:
        if not Path(row["model_file"]).exists():
            raise FileNotFoundError(f"Missing model file referenced for subject {subject_id}: {row['model_file']}")

    total_abundance_raw = sum(float(row["abundance_raw"]) for row in enriched_rows)
    n_nonzero_modeled_taxa = sum(float(row["abundance_raw"]) > 0 for row in enriched_rows)
    return [
        f"{subject_id}: cohort={enriched_rows[0]['cohort']}, age_group={enriched_rows[0]['age_group']}, "
        f"n_nonzero_modeled_taxa={n_nonzero_modeled_taxa}, total_abundance_raw={total_abundance_raw:.6f}"
    ]


def build_subject_qc_row(
    subject_rows: list[dict[str, object]],
    *,
    has_abundance_workbook_row: bool = True,
    include_in_subject_micom: bool = True,
    exclusion_reason: str = "",
) -> dict[str, object]:
    enriched_rows = enrich_subject_rows(subject_rows)
    total_abundance_raw = sum(float(row["abundance_raw"]) for row in enriched_rows)
    total_abundance_normalized = sum(float(row["abundance_normalized"]) for row in enriched_rows)
    n_nonzero_modeled_taxa = sum(float(row["abundance_raw"]) > 0 for row in enriched_rows)
    return {
        "subject_id": enriched_rows[0]["subject_id"],
        "cohort": enriched_rows[0]["cohort"],
        "age_years": enriched_rows[0]["age_years"],
        "age_group": enriched_rows[0]["age_group"],
        "has_abundance_workbook_row": has_abundance_workbook_row,
        "include_in_subject_micom": include_in_subject_micom,
        "exclusion_reason": exclusion_reason,
        "n_modeled_taxa_total": len(enriched_rows),
        "n_nonzero_modeled_taxa": n_nonzero_modeled_taxa,
        "total_modeled_abundance_raw": total_abundance_raw,
        "total_modeled_abundance_normalized": total_abundance_normalized,
        "all_modeled_taxa_zero": total_abundance_raw <= 0,
    }


def build_missing_subject_qc_row(
    subject_metadata: dict[str, object],
    *,
    exclusion_reason: str,
) -> dict[str, object]:
    return {
        "subject_id": subject_metadata["subject_id"],
        "cohort": subject_metadata["cohort"],
        "age_years": subject_metadata["age_years"],
        "age_group": subject_metadata["age_group"],
        "has_abundance_workbook_row": False,
        "include_in_subject_micom": False,
        "exclusion_reason": exclusion_reason,
        "n_modeled_taxa_total": 0,
        "n_nonzero_modeled_taxa": 0,
        "total_modeled_abundance_raw": 0.0,
        "total_modeled_abundance_normalized": 0.0,
        "all_modeled_taxa_zero": "",
    }


def build_subject_lookup_row(
    subject_metadata: dict[str, object],
    *,
    has_abundance_workbook_row: bool,
    include_in_subject_micom: bool,
    exclusion_reason: str = "",
) -> dict[str, object]:
    return {
        "subject_id": subject_metadata["subject_id"],
        "cohort": subject_metadata["cohort"],
        "age_years": subject_metadata["age_years"],
        "age_group": subject_metadata["age_group"],
        "gender": subject_metadata["gender"],
        "sequencer": subject_metadata["sequencer"],
        "has_abundance_workbook_row": has_abundance_workbook_row,
        "include_in_subject_micom": include_in_subject_micom,
        "exclusion_reason": exclusion_reason,
    }


def build_subject_presence_matrix_row(subject_rows: list[dict[str, object]]) -> dict[str, object]:
    enriched_rows = enrich_subject_rows(subject_rows)
    row = {
        "subject_id": enriched_rows[0]["subject_id"],
        "cohort": enriched_rows[0]["cohort"],
        "age_years": enriched_rows[0]["age_years"],
        "age_group": enriched_rows[0]["age_group"],
        "n_nonzero_modeled_taxa": sum(float(item["abundance_raw"]) > 0 for item in enriched_rows),
    }
    for model_species_id in target_model_species_ids_in_order():
        row[model_species_id] = 0
    for item in enriched_rows:
        row[item["model_species_id"]] = int(float(item["abundance_raw"]) > 0)
    return row


def build_missing_subject_audit_row(
    subject_metadata: dict[str, object],
    *,
    exclusion_reason: str = "missing_from_abundance_workbook",
) -> dict[str, object]:
    return {
        "subject_id": subject_metadata["subject_id"],
        "cohort": subject_metadata["cohort"],
        "age_years": subject_metadata["age_years"],
        "age_group": subject_metadata["age_group"],
        "gender": subject_metadata["gender"],
        "sequencer": subject_metadata["sequencer"],
        "exclusion_reason": exclusion_reason,
    }


def build_abundance_subject_missing_metadata_row(
    subject_id: str,
    *,
    exclusion_reason: str = "missing_from_metadata",
) -> dict[str, object]:
    return {
        "subject_id": subject_id,
        "exclusion_reason": exclusion_reason,
    }


def build_subject_taxonomy(subject_rows: list[dict[str, object]]):
    import pandas as pd

    enriched_rows = enrich_subject_rows(subject_rows)
    total_normalized_abundance = sum(float(row["abundance_normalized"]) for row in enriched_rows)
    used_equal_abundance_fallback = total_normalized_abundance <= 0

    if used_equal_abundance_fallback:
        abundance = 1.0 / len(enriched_rows)
        taxonomy_rows = [
            {
                "id": row["model_species_id"],
                "species": row["species_name"],
                "file": row["model_file"],
                "abundance": abundance,
            }
            for row in enriched_rows
        ]
    else:
        taxonomy_rows = [
            {
                "id": row["model_species_id"],
                "species": row["species_name"],
                "file": row["model_file"],
                "abundance": float(row["abundance_normalized"]),
            }
            for row in enriched_rows
        ]

    return pd.DataFrame(taxonomy_rows), used_equal_abundance_fallback


def build_subject_taxonomy_rows(subject_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return enrich_subject_rows(subject_rows)
