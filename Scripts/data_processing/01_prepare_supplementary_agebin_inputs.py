from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from statistics import median
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUPP_DIR = PROJECT_ROOT / "Suplementary_Data"
OUT_DIR = SUPP_DIR / "processed_data"

METADATA_XLSX = SUPP_DIR / "Metadata_by_cohort.xlsx"
ABUNDANCE_XLSX = SUPP_DIR / "subject_level_taxonomic_relative_abundance_values.xlsx"

SUBJECT_LEVEL_OUT = OUT_DIR / "subject_level_abundance_10_species.csv"
COHORT_AGEBIN_OUT = OUT_DIR / "cohort_agebin_median_abundance_10_species.csv"
ALLCOHORT_AGEBIN_OUT = OUT_DIR / "allcohort_agebin_median_abundance_10_species.csv"
ALLCOHORT_WIDE_OUT = OUT_DIR / "allcohort_agebin_median_abundance_10_species_wide.csv"
QC_SUMMARY_OUT = OUT_DIR / "agebin_input_qc_summary.csv"

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

TARGET_SPECIES = {
    "Alistipes onderdonkii": {
        "paper_taxon": "Alistipes onderdonkii",
        "model_file": "Models/vmh_agora2_sbml/Alistipes_onderdonkii_DSM_19147.xml",
        "model_species_id": "Alistipes_onderdonkii_DSM_19147",
    },
    "Alistipes shahii": {
        "paper_taxon": "Alistipes shahii",
        "model_file": "Models/vmh_agora2_sbml/Alistipes_shahii_WAL_8301.xml",
        "model_species_id": "Alistipes_shahii_WAL_8301",
    },
    "Bacteroides dorei": {
        "paper_taxon": "Bacteroides dorei",
        "model_file": "Models/vmh_agora2_sbml/Bacteroides_dorei_DSM_17855.xml",
        "model_species_id": "Bacteroides_dorei_DSM_17855",
    },
    "Bacteroides xylanisolvens": {
        "paper_taxon": "Bacteroides xylanisolvens",
        "model_file": "Models/vmh_agora2_sbml/Bacteroides_xylanisolvens_XB1A.xml",
        "model_species_id": "Bacteroides_xylanisolvens_XB1A",
    },
    "Bilophila wadsworthia": {
        "paper_taxon": "Bilophila unclassified",
        "model_file": "Models/vmh_agora2_sbml/Bilophila_wadsworthia_3_1_6.xml",
        "model_species_id": "Bilophila_wadsworthia_3_1_6",
    },
    "Escherichia coli": {
        "paper_taxon": "Escherichia coli",
        "model_file": "Models/vmh_agora2_sbml/Escherichia_coli_UTI89_UPEC.xml",
        "model_species_id": "Escherichia_coli_UTI89_UPEC",
    },
    "Faecalibacterium prausnitzii": {
        "paper_taxon": "Faecalibacterium prausnitzii",
        "model_file": "Models/vmh_agora2_sbml/Faecalibacterium_prausnitzii_M21_2.xml",
        "model_species_id": "Faecalibacterium_prausnitzii_M21_2",
    },
    "Klebsiella pneumoniae": {
        "paper_taxon": "Klebsiella pneumoniae",
        "model_file": "Models/vmh_agora2_sbml/Klebsiella_pneumoniae_pneumoniae_MGH78578.xml",
        "model_species_id": "Klebsiella_pneumoniae_pneumoniae_MGH78578",
    },
    "Parabacteroides merdae": {
        "paper_taxon": "Parabacteroides merdae",
        "model_file": "Models/vmh_agora2_sbml/Parabacteroides_merdae_ATCC_43184.xml",
        "model_species_id": "Parabacteroides_merdae_ATCC_43184",
    },
    "Ruminococcus torques": {
        "paper_taxon": "Ruminococcus torques",
        "model_file": "Models/vmh_agora2_sbml/Ruminococcus_torques_ATCC_27756.xml",
        "model_species_id": "Ruminococcus_torques_ATCC_27756",
    },
}


def excel_column_to_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    value = 0
    for ch in letters:
        value = value * 26 + (ord(ch.upper()) - ord("A") + 1)
    return value - 1


def read_shared_strings(handle: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(handle.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("main:si", NS):
        parts = [node.text or "" for node in si.iterfind(".//main:t", NS)]
        strings.append("".join(parts))
    return strings


def read_sheet_rows(xlsx_path: Path, sheet_path: str) -> list[list[str]]:
    with zipfile.ZipFile(xlsx_path) as handle:
        shared_strings = read_shared_strings(handle)
        root = ET.fromstring(handle.read(sheet_path))

    rows: list[list[str]] = []
    for row in root.find("main:sheetData", NS).findall("main:row", NS):
        parsed: list[str] = []
        current_col = 0
        for cell in row.findall("main:c", NS):
            col_index = excel_column_to_index(cell.attrib["r"])
            while current_col < col_index:
                parsed.append("")
                current_col += 1

            raw_value = cell.findtext("main:v", default="", namespaces=NS)
            if cell.attrib.get("t") == "s" and raw_value != "":
                value = shared_strings[int(raw_value)]
            else:
                value = raw_value

            parsed.append(value)
            current_col += 1
        rows.append(parsed)
    return rows


def age_group_from_years(age_value: str) -> str | None:
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


def infer_cohort(subject_id: str, sequencer: str, age_value: str) -> str:
    prefix = re.match(r"[A-Za-z]+", subject_id)
    prefix_text = prefix.group(0) if prefix else ""

    if prefix_text in {"CON", "NLF", "NLM", "NOF", "NOM"}:
        return "T2D"
    if prefix_text in {"MBE", "MBM", "WFC"}:
        return "SPMP"
    if prefix_text == "MHH":
        return "CRE"
    if prefix_text == "MHS":
        return "SPMP" if sequencer == "Illumina HiSeq4K" else "CRE"
    if prefix_text == "MBH":
        return "SPMP" if sequencer == "Illumina HiSeq4K" else "CRE"
    if prefix_text == "MBS":
        if sequencer == "Illumina HiSeq X":
            return "SG90"
        try:
            age = float(age_value)
        except (TypeError, ValueError):
            age = -1
        return "SG90" if age >= 77 else "CRE"
    return "unknown"


def normalize_weights(values: list[float]) -> list[float]:
    total = sum(values)
    if total <= 0:
        if not values:
            return []
        return [1.0 / len(values)] * len(values)
    return [value / total for value in values]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_wide_rows(allcohort_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    age_order = ["21_40", "41_60", "61_70", "71_80", "81_90", "91_100"]
    by_species: dict[str, dict[str, object]] = {}
    for row in allcohort_rows:
        species_name = str(row["species_name"])
        species_row = by_species.setdefault(
            species_name,
            {
                "species_name": species_name,
                "paper_taxon": row["paper_taxon"],
                "model_file": row["model_file"],
                "model_species_id": row["model_species_id"],
            },
        )
        species_row[str(row["age_group"])] = row["median_abundance"]

    wide_rows: list[dict[str, object]] = []
    for species_name in sorted(by_species):
        row = by_species[species_name]
        for age_group in age_order:
            row.setdefault(age_group, 0.0)
        wide_rows.append(row)
    return wide_rows


def load_metadata() -> dict[str, dict[str, object]]:
    rows = read_sheet_rows(METADATA_XLSX, "xl/worksheets/sheet1.xml")
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
        age_years = row[age_idx].strip()
        if not subject_id:
            continue
        age_group = age_group_from_years(age_years)
        if age_group is None:
            continue
        sequencer = row[sequencer_idx].strip()
        metadata[subject_id] = {
            "subject_id": subject_id,
            "age_years": float(age_years),
            "gender": row[gender_idx].strip(),
            "sequencer": sequencer,
            "cohort": infer_cohort(subject_id, sequencer, age_years),
            "age_group": age_group,
        }
    return metadata


def load_target_species_abundances(metadata: dict[str, dict[str, object]]) -> tuple[list[dict[str, object]], set[str]]:
    rows = read_sheet_rows(ABUNDANCE_XLSX, "xl/worksheets/sheet1.xml")
    header = rows[0]
    species_columns = {idx: species_name.strip() for idx, species_name in enumerate(header[1:], start=1) if species_name.strip()}
    target_species_columns = {
        idx: species_name for idx, species_name in species_columns.items() if species_name in TARGET_SPECIES
    }

    subject_level_rows: list[dict[str, object]] = []
    found_species: set[str] = set(target_species_columns.values())

    for row in rows[1:]:
        if not row:
            continue
        subject_id = row[0].strip()
        if subject_id not in metadata:
            continue
        meta = metadata[subject_id]
        for idx, species_name in target_species_columns.items():
            mapping = TARGET_SPECIES[species_name]
            value = 0.0
            if idx < len(row) and row[idx] != "":
                value = float(row[idx])
            subject_level_rows.append(
                {
                    "subject_id": subject_id,
                    "cohort": meta["cohort"],
                    "age_years": meta["age_years"],
                    "age_group": meta["age_group"],
                    "species_name": species_name,
                    "paper_taxon": mapping["paper_taxon"],
                    "abundance": value,
                }
            )
    return subject_level_rows, found_species


def build_aggregated_rows(
    subject_level_rows: list[dict[str, object]],
    cohort_value: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_group: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    subjects_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in subject_level_rows:
        cohort = row["cohort"] if cohort_value is None else cohort_value
        age_group = row["age_group"]
        key = (str(cohort), str(age_group))
        by_group[key][str(row["species_name"])].append(float(row["abundance"]))
        subjects_by_group[key].add(str(row["subject_id"]))

    aggregated_rows: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []

    age_order = ["21_40", "41_60", "61_70", "71_80", "81_90", "91_100"]
    group_keys = sorted(by_group, key=lambda item: ((item[0] != "all_cohort"), age_order.index(item[1]), item[0]))

    for cohort, age_group in group_keys:
        medians: list[float] = []
        species_rows: list[dict[str, object]] = []
        for species_name in sorted(TARGET_SPECIES):
            mapping = TARGET_SPECIES[species_name]
            values = by_group[(cohort, age_group)].get(species_name, [])
            med = float(median(values)) if values else 0.0
            medians.append(med)
            species_rows.append(
                {
                    "cohort": cohort,
                    "age_group": age_group,
                    "species_name": species_name,
                    "paper_taxon": mapping["paper_taxon"],
                    "model_file": mapping["model_file"],
                    "model_species_id": mapping["model_species_id"],
                    "median_abundance": med,
                    "n_subjects": len(subjects_by_group[(cohort, age_group)]),
                }
            )

        normalized = normalize_weights(medians)
        used_equal_fallback = sum(medians) <= 0
        for row, weight in zip(species_rows, normalized):
            row["normalized_weight"] = weight
            aggregated_rows.append(row)

        qc_rows.append(
            {
                "cohort": cohort,
                "age_group": age_group,
                "n_subjects_matched": len(subjects_by_group[(cohort, age_group)]),
                "n_species_nonzero": sum(1 for value in medians if value > 0),
                "total_median_abundance_pre_norm": sum(medians),
                "used_equal_weight_fallback": used_equal_fallback,
            }
        )

    return aggregated_rows, qc_rows


def sort_qc_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    def age_sort_key(age_group: str) -> tuple[int, int]:
        match = re.match(r"^\s*(\d+)_(\d+)\s*$", age_group)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (999, 999)

    return sorted(
        rows,
        key=lambda row: (
            age_sort_key(str(row["age_group"])),
            1 if str(row["cohort"]) == "all_cohort" else 0,
            str(row["cohort"]),
        ),
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata = load_metadata()
    subject_level_rows, found_species = load_target_species_abundances(metadata)

    missing_species = sorted(set(TARGET_SPECIES) - found_species)
    if missing_species:
        raise RuntimeError(f"Missing target species in abundance workbook: {', '.join(missing_species)}")

    cohort_rows, cohort_qc_rows = build_aggregated_rows(subject_level_rows)
    allcohort_input_rows = [dict(row, cohort="all_cohort") for row in subject_level_rows]
    allcohort_rows, allcohort_qc_rows = build_aggregated_rows(allcohort_input_rows, cohort_value="all_cohort")

    allcohort_bin_sizes = [int(row["n_subjects_matched"]) for row in allcohort_qc_rows]
    low_n_threshold = median(allcohort_bin_sizes) if allcohort_bin_sizes else 0
    for qc_row in cohort_qc_rows + allcohort_qc_rows:
        qc_row["low_n_bin"] = int(qc_row["n_subjects_matched"]) < low_n_threshold

    write_csv(
        SUBJECT_LEVEL_OUT,
        ["subject_id", "cohort", "age_years", "age_group", "species_name", "paper_taxon", "abundance"],
        subject_level_rows,
    )
    write_csv(
        COHORT_AGEBIN_OUT,
        [
            "cohort",
            "age_group",
            "species_name",
            "paper_taxon",
            "model_file",
            "model_species_id",
            "median_abundance",
            "normalized_weight",
            "n_subjects",
        ],
        cohort_rows,
    )
    write_csv(
        ALLCOHORT_AGEBIN_OUT,
        [
            "cohort",
            "age_group",
            "species_name",
            "paper_taxon",
            "model_file",
            "model_species_id",
            "median_abundance",
            "normalized_weight",
            "n_subjects",
        ],
        allcohort_rows,
    )
    write_csv(
        ALLCOHORT_WIDE_OUT,
        [
            "species_name",
            "paper_taxon",
            "model_file",
            "model_species_id",
            "21_40",
            "41_60",
            "61_70",
            "71_80",
            "81_90",
            "91_100",
        ],
        build_wide_rows(allcohort_rows),
    )
    write_csv(
        QC_SUMMARY_OUT,
        [
            "cohort",
            "age_group",
            "n_subjects_matched",
            "n_species_nonzero",
            "total_median_abundance_pre_norm",
            "used_equal_weight_fallback",
            "low_n_bin",
        ],
        sort_qc_rows(cohort_qc_rows + allcohort_qc_rows),
    )

    print(f"Wrote {SUBJECT_LEVEL_OUT}")
    print(f"Wrote {COHORT_AGEBIN_OUT}")
    print(f"Wrote {ALLCOHORT_AGEBIN_OUT}")
    print(f"Wrote {ALLCOHORT_WIDE_OUT}")
    print(f"Wrote {QC_SUMMARY_OUT}")


if __name__ == "__main__":
    main()
