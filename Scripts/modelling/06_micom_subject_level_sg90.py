from __future__ import annotations

import argparse
import csv
import importlib.util
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

BASELINE_UTILS_PATH = SCRIPT_DIR / "00_baseline_modeling_utils.py"
BASELINE_UTILS_SPEC = importlib.util.spec_from_file_location("baseline_modeling_utils", BASELINE_UTILS_PATH)
if BASELINE_UTILS_SPEC is None or BASELINE_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load utility module from {BASELINE_UTILS_PATH}")
BASELINE_UTILS_MODULE = importlib.util.module_from_spec(BASELINE_UTILS_SPEC)
BASELINE_UTILS_SPEC.loader.exec_module(BASELINE_UTILS_MODULE)

MICOM_UTILS_PATH = SCRIPT_DIR / "00_micom_utils.py"
MICOM_UTILS_SPEC = importlib.util.spec_from_file_location("micom_utils", MICOM_UTILS_PATH)
if MICOM_UTILS_SPEC is None or MICOM_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load MICOM utility module from {MICOM_UTILS_PATH}")
MICOM_UTILS_MODULE = importlib.util.module_from_spec(MICOM_UTILS_SPEC)
MICOM_UTILS_SPEC.loader.exec_module(MICOM_UTILS_MODULE)

SUBJECT_UTILS_PATH = SCRIPT_DIR / "00_subject_level_micom_utils.py"
SUBJECT_UTILS_SPEC = importlib.util.spec_from_file_location("subject_level_micom_utils", SUBJECT_UTILS_PATH)
if SUBJECT_UTILS_SPEC is None or SUBJECT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load subject-level utility module from {SUBJECT_UTILS_PATH}")
SUBJECT_UTILS_MODULE = importlib.util.module_from_spec(SUBJECT_UTILS_SPEC)
SUBJECT_UTILS_SPEC.loader.exec_module(SUBJECT_UTILS_MODULE)

REPORT_UTILS_PATH = SCRIPT_DIR / "00_report_output_dictionary.py"
REPORT_UTILS_SPEC = importlib.util.spec_from_file_location("report_output_dictionary", REPORT_UTILS_PATH)
if REPORT_UTILS_SPEC is None or REPORT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load report utility module from {REPORT_UTILS_PATH}")
REPORT_UTILS_MODULE = importlib.util.module_from_spec(REPORT_UTILS_SPEC)
REPORT_UTILS_SPEC.loader.exec_module(REPORT_UTILS_MODULE)

GROWTH_THRESHOLD = BASELINE_UTILS_MODULE.GROWTH_THRESHOLD
load_diet_table = BASELINE_UTILS_MODULE.load_diet_table
run_cooperative_tradeoff = MICOM_UTILS_MODULE.run_cooperative_tradeoff
write_csv = MICOM_UTILS_MODULE.write_csv
build_subject_taxonomy = SUBJECT_UTILS_MODULE.build_subject_taxonomy
build_subject_taxonomy_rows = SUBJECT_UTILS_MODULE.build_subject_taxonomy_rows
csv_bool = SUBJECT_UTILS_MODULE.csv_bool
group_rows_by_subject = SUBJECT_UTILS_MODULE.group_rows_by_subject
load_subject_level_rows = SUBJECT_UTILS_MODULE.load_subject_level_rows
target_model_species_ids_in_order = SUBJECT_UTILS_MODULE.target_model_species_ids_in_order
validate_subject_rows = SUBJECT_UTILS_MODULE.validate_subject_rows
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


SUBJECT_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_sg90/sg90_subject_taxonomy_for_micom.csv")
QC_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_sg90/sg90_subject_input_qc_summary.csv")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_community_growth_summary_by_diet.csv")
TAXON_OUTPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet.csv")
WIDE_OUTPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet_wide.csv")
BUILD_REPORT = Path("Results/subject_level_fba/reports/06_sg90_subject_level_micom_build_report.txt")
TRADEOFF_FRACTION = 0.5
SUMMARY_FIELDNAMES = [
    "subject_id",
    "cohort",
    "age_years",
    "age_group",
    "diet_name",
    "solver_status",
    "community_growth_rate",
    "objective_value",
    "tradeoff_fraction",
    "num_taxa_total",
    "num_taxa_with_nonzero_growth",
    "matched_diet_metabolites",
    "missing_diet_metabolites",
    "total_input_abundance_raw",
    "total_input_abundance_normalized",
    "error_message",
]
TAXON_FIELDNAMES = [
    "subject_id",
    "cohort",
    "age_years",
    "age_group",
    "diet_name",
    "taxon_id",
    "species_name",
    "paper_taxon",
    "abundance_raw",
    "abundance_normalized",
    "growth_rate",
    "is_growing",
    "reactions",
    "metabolites",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run subject-level MICOM for SG90 subjects.")
    parser.add_argument("--subject-id", help="Run a single subject ID only.")
    parser.add_argument("--age-group", choices=("71_80", "81_90", "91_100"), help="Restrict to one age group.")
    parser.add_argument("--limit", type=int, help="Limit the number of selected subjects.")
    return parser.parse_args()


def load_qc_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def select_subject_ids(qc_rows: list[dict[str, str]], args: argparse.Namespace) -> list[str]:
    selected_rows = [row for row in qc_rows if csv_bool(row["include_in_subject_micom"])]
    if args.age_group:
        selected_rows = [row for row in selected_rows if row["age_group"] == args.age_group]
    if args.subject_id:
        selected_rows = [row for row in selected_rows if row["subject_id"] == args.subject_id]
        if not selected_rows:
            raise ValueError(f"No included SG90 subject matched --subject-id {args.subject_id}")
    selected_rows = sorted(selected_rows, key=lambda row: row["subject_id"])
    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be a positive integer")
        selected_rows = selected_rows[: args.limit]
    return [row["subject_id"] for row in selected_rows]


def build_wide_rows(taxon_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    model_species_ids = target_model_species_ids_in_order()

    for row in taxon_rows:
        key = (str(row["subject_id"]), str(row["diet_name"]))
        existing = grouped.get(key)
        if existing is None:
            existing = {
                "subject_id": row["subject_id"],
                "cohort": row["cohort"],
                "age_years": row["age_years"],
                "age_group": row["age_group"],
                "diet_name": row["diet_name"],
            }
            grouped[key] = existing
        existing[str(row["taxon_id"])] = row["growth_rate"]

    wide_rows: list[dict[str, object]] = []
    for _, row in sorted(grouped.items()):
        for model_species_id in model_species_ids:
            row.setdefault(model_species_id, 0.0)
        wide_rows.append(row)
    return wide_rows


def build_csv_output_specs(model_species_ids: list[str]) -> list[dict[str, object]]:
    return [
        csv_output_spec(
            SUMMARY_OUTPUT,
            "one row per subject_id x diet_name",
            [
                col("subject_id", "Subject identifier from the SG90 subject-level MICOM input table."),
                col("cohort", "Cohort label carried through from the subject metadata."),
                col("age_years", "Subject age in years from the metadata table."),
                col("age_group", "Age-bin label assigned from the metadata age."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("solver_status", "MICOM solver status returned for this subject-level solve."),
                col("community_growth_rate", "MICOM-reported community growth rate for this subject and diet."),
                col(
                    "objective_value",
                    "Objective value returned by MICOM for this subject-level cooperative tradeoff solve.",
                    "objective_value = optimization objective reported by MICOM after cooperative_tradeoff",
                ),
                col("tradeoff_fraction", "Tradeoff fraction passed into MICOM cooperative tradeoff."),
                col("num_taxa_total", "Number of modeled taxa carried into the subject-level MICOM community input."),
                col(
                    "num_taxa_with_nonzero_growth",
                    "Count of modeled taxa whose MICOM growth rate exceeded the growth threshold.",
                    f"num_taxa_with_nonzero_growth = count(growth_rate > {GROWTH_THRESHOLD})",
                ),
                col(
                    "matched_diet_metabolites",
                    "Count of diet metabolite IDs translated into MICOM medium entries.",
                    "matched_diet_metabolites = number of diet metabolite_ids with a MICOM medium mapping",
                ),
                col(
                    "missing_diet_metabolites",
                    "Count of diet metabolite IDs that could not be translated into MICOM medium entries.",
                    "missing_diet_metabolites = total diet metabolite_ids - matched_diet_metabolites",
                ),
                col(
                    "total_input_abundance_raw",
                    "Sum of the raw abundances carried into the 10-taxon subject input for this subject.",
                    "total_input_abundance_raw = sum(abundance_raw across all taxon_id within subject_id)",
                ),
                col(
                    "total_input_abundance_normalized",
                    "Sum of the normalized abundances carried into the 10-taxon subject input for this subject.",
                    "total_input_abundance_normalized = sum(abundance_normalized across all taxon_id within subject_id)",
                ),
                col("error_message", "Error text recorded for failed community-build or solve attempts; blank otherwise."),
            ],
        ),
        csv_output_spec(
            TAXON_OUTPUT,
            "one row per subject_id x diet_name x taxon_id",
            [
                col("subject_id", "Subject identifier from the SG90 subject-level MICOM input table."),
                col("cohort", "Cohort label carried through from the subject metadata."),
                col("age_years", "Subject age in years from the metadata table."),
                col("age_group", "Age-bin label assigned from the metadata age."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("taxon_id", "MICOM taxon/model identifier."),
                col("species_name", "Species label mapped onto this model taxon."),
                col("paper_taxon", "Original paper taxon label mapped onto this model species."),
                col("abundance_raw", "Raw subject-level abundance used for this taxon."),
                col(
                    "abundance_normalized",
                    "Normalized subject-level abundance used for the MICOM taxonomy.",
                    "abundance_normalized = abundance_raw / sum(abundance_raw across modeled taxa within subject_id) when the within-subject total is positive",
                ),
                col("growth_rate", "MICOM-reported taxon growth rate for this subject and diet."),
                col(
                    "is_growing",
                    "Boolean flag showing whether the MICOM taxon growth rate exceeded the growth threshold.",
                    f"is_growing = growth_rate > {GROWTH_THRESHOLD}",
                ),
                col("reactions", "Number of reactions present in the MICOM member model returned for this taxon."),
                col("metabolites", "Number of metabolites present in the MICOM member model returned for this taxon."),
            ],
        ),
        csv_output_spec(
            WIDE_OUTPUT,
            "one row per subject_id x diet_name",
            [
                col("subject_id", "Subject identifier from the SG90 subject-level MICOM input table."),
                col("cohort", "Cohort label carried through from the subject metadata."),
                col("age_years", "Subject age in years from the metadata table."),
                col("age_group", "Age-bin label assigned from the metadata age."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                *[
                    col(
                        model_species_id,
                        f"MICOM taxon growth rate for model taxon {model_species_id} in this subject and diet.",
                    )
                    for model_species_id in model_species_ids
                ],
            ],
        ),
    ]


def main() -> None:
    args = parse_args()

    try:
        from micom import Community
    except ImportError as exc:
        raise ImportError(
            "MICOM is not installed in this environment. Install it first, for example with "
            "`pip install micom`, then rerun Scripts/modelling/06_micom_subject_level_sg90.py."
        ) from exc

    subject_input_rows = load_subject_level_rows(SUBJECT_INPUT)
    qc_rows = load_qc_rows(QC_INPUT)
    qc_by_subject = {row["subject_id"]: row for row in qc_rows}
    subject_rows_by_subject = group_rows_by_subject(subject_input_rows)
    diet_table = load_diet_table(DIET_CSV)
    selected_subject_ids = select_subject_ids(qc_rows, args)

    total_qc_subjects = len(qc_rows)
    included_subjects = sum(csv_bool(row["include_in_subject_micom"]) for row in qc_rows)
    excluded_subjects = total_qc_subjects - included_subjects
    missing_abundance_subjects = [
        row["subject_id"] for row in qc_rows if not csv_bool(row["has_abundance_workbook_row"])
    ]

    selected_qc_rows = [qc_by_subject[subject_id] for subject_id in selected_subject_ids]
    selected_age_counts = Counter(row["age_group"] for row in selected_qc_rows)
    nonzero_count_distribution = Counter(int(row["n_nonzero_modeled_taxa"]) for row in selected_qc_rows)

    report_lines = [
        "SG90 subject-level MICOM build report",
        f"Subject input: {SUBJECT_INPUT}",
        f"QC input: {QC_INPUT}",
        f"Diet file: {DIET_CSV}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        f"Selection filters: subject_id={args.subject_id or 'ALL'}, age_group={args.age_group or 'ALL'}, limit={args.limit or 'ALL'}",
        "",
        f"Total SG90 subjects in QC table: {total_qc_subjects}",
        f"Included subjects with abundance rows: {included_subjects}",
        f"Excluded subjects: {excluded_subjects}",
        f"Subjects missing from abundance workbook: {len(missing_abundance_subjects)}",
        f"Selected subjects for this run: {len(selected_subject_ids)}",
        "",
        "Selected subject counts by age group",
    ]
    report_lines.extend(f"{age_group}: {count}" for age_group, count in sorted(selected_age_counts.items()))
    report_lines.append("")
    report_lines.append("Selected subject nonzero modeled taxon distribution")
    report_lines.extend(f"{count} nonzero taxa: {n_subjects} subjects" for count, n_subjects in sorted(nonzero_count_distribution.items()))
    report_lines.append("")

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []
    failures: list[str] = []
    per_diet_successes = Counter()
    per_diet_failures = Counter()

    for subject_id in selected_subject_ids:
        subject_rows = subject_rows_by_subject.get(subject_id)
        if subject_rows is None:
            raise ValueError(f"Selected subject {subject_id} is missing from {SUBJECT_INPUT}")

        validate_subject_rows(subject_id, subject_rows)
        full_subject_rows = build_subject_taxonomy_rows(subject_rows)
        taxonomy, used_equal_abundance_fallback = build_subject_taxonomy(subject_rows)
        community_id = f"micom_subject_{subject_id}"

        try:
            community = Community(
                taxonomy=taxonomy,
                model_db=None,
                id=community_id,
                name=community_id,
                progress=False,
            )
        except Exception as exc:
            error_message = str(exc)
            failures.append(f"{subject_id}: community_build_failed -> {error_message}")
            report_lines.append(f"{subject_id}: community_build_failed -> {error_message}")
            for diet_name in diet_table:
                per_diet_failures[diet_name] += 1
                summary_rows.append(
                    {
                        "subject_id": full_subject_rows[0]["subject_id"],
                        "cohort": full_subject_rows[0]["cohort"],
                        "age_years": full_subject_rows[0]["age_years"],
                        "age_group": full_subject_rows[0]["age_group"],
                        "diet_name": diet_name,
                        "solver_status": "community_build_failed",
                        "community_growth_rate": "",
                        "objective_value": "",
                        "tradeoff_fraction": TRADEOFF_FRACTION,
                        "num_taxa_total": len(full_subject_rows),
                        "num_taxa_with_nonzero_growth": "",
                        "matched_diet_metabolites": "",
                        "missing_diet_metabolites": "",
                        "total_input_abundance_raw": sum(float(row["abundance_raw"]) for row in full_subject_rows),
                        "total_input_abundance_normalized": sum(float(row["abundance_normalized"]) for row in full_subject_rows),
                        "error_message": error_message,
                    }
                )
            continue

        for diet_name, diet_bounds in diet_table.items():
            try:
                solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
                    community,
                    diet_bounds,
                    TRADEOFF_FRACTION,
                )
            except Exception as exc:
                error_message = str(exc)
                failures.append(f"{subject_id} | {diet_name}: solve_failed -> {error_message}")
                report_lines.append(f"{subject_id} | {diet_name}: solve_failed -> {error_message}")
                per_diet_failures[diet_name] += 1
                summary_rows.append(
                    {
                        "subject_id": full_subject_rows[0]["subject_id"],
                        "cohort": full_subject_rows[0]["cohort"],
                        "age_years": full_subject_rows[0]["age_years"],
                        "age_group": full_subject_rows[0]["age_group"],
                        "diet_name": diet_name,
                        "solver_status": "solve_failed",
                        "community_growth_rate": "",
                        "objective_value": "",
                        "tradeoff_fraction": TRADEOFF_FRACTION,
                        "num_taxa_total": len(full_subject_rows),
                        "num_taxa_with_nonzero_growth": "",
                        "matched_diet_metabolites": "",
                        "missing_diet_metabolites": "",
                        "total_input_abundance_raw": sum(float(row["abundance_raw"]) for row in full_subject_rows),
                        "total_input_abundance_normalized": sum(float(row["abundance_normalized"]) for row in full_subject_rows),
                        "error_message": error_message,
                    }
                )
                continue

            members_by_taxon = {str(row.taxon_id): row for row in members.itertuples(index=False)}
            num_taxa_growing = 0
            for input_row in full_subject_rows:
                taxon_id = str(input_row["model_species_id"])
                member_row = members_by_taxon.get(taxon_id)
                growth_rate = float(getattr(member_row, "growth_rate", 0.0)) if member_row is not None else 0.0
                is_growing = growth_rate > GROWTH_THRESHOLD
                num_taxa_growing += int(is_growing)
                taxon_rows.append(
                    {
                        "subject_id": input_row["subject_id"],
                        "cohort": input_row["cohort"],
                        "age_years": input_row["age_years"],
                        "age_group": input_row["age_group"],
                        "diet_name": diet_name,
                        "taxon_id": taxon_id,
                        "species_name": input_row["species_name"],
                        "paper_taxon": input_row["paper_taxon"],
                        "abundance_raw": input_row["abundance_raw"],
                        "abundance_normalized": input_row["abundance_normalized"],
                        "growth_rate": growth_rate,
                        "is_growing": is_growing,
                        "reactions": getattr(member_row, "reactions", "") if member_row is not None else "",
                        "metabolites": getattr(member_row, "metabolites", "") if member_row is not None else "",
                    }
                )

            per_diet_successes[diet_name] += 1
            summary_rows.append(
                {
                    "subject_id": full_subject_rows[0]["subject_id"],
                    "cohort": full_subject_rows[0]["cohort"],
                    "age_years": full_subject_rows[0]["age_years"],
                    "age_group": full_subject_rows[0]["age_group"],
                    "diet_name": diet_name,
                    "solver_status": solution.status,
                    "community_growth_rate": solution.growth_rate,
                    "objective_value": solution.objective_value,
                    "tradeoff_fraction": TRADEOFF_FRACTION,
                    "num_taxa_total": len(full_subject_rows),
                    "num_taxa_with_nonzero_growth": num_taxa_growing,
                    "matched_diet_metabolites": len(medium),
                    "missing_diet_metabolites": len(missing_metabolites),
                    "total_input_abundance_raw": sum(float(row["abundance_raw"]) for row in full_subject_rows),
                    "total_input_abundance_normalized": sum(float(row["abundance_normalized"]) for row in full_subject_rows),
                    "error_message": "",
                }
            )
            if used_equal_abundance_fallback:
                report_lines.append(
                    f"{subject_id} | {diet_name}: used equal-abundance fallback because normalized abundances summed to 0.0"
                )

    report_lines.append("")
    report_lines.append("Solve summary by diet")
    for diet_name in sorted(diet_table):
        report_lines.append(
            f"{diet_name}: successes={per_diet_successes[diet_name]}, failures={per_diet_failures[diet_name]}"
        )
    if failures:
        report_lines.append("")
        report_lines.append("Failure list")
        report_lines.extend(failures)

    wide_rows = build_wide_rows(taxon_rows)

    write_csv(
        SUMMARY_OUTPUT,
        SUMMARY_FIELDNAMES,
        summary_rows,
    )
    write_csv(
        TAXON_OUTPUT,
        TAXON_FIELDNAMES,
        taxon_rows,
    )
    write_csv(
        WIDE_OUTPUT,
        ["subject_id", "cohort", "age_years", "age_group", "diet_name", *target_model_species_ids_in_order()],
        wide_rows,
    )
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(
        build_report_text(report_lines, build_csv_output_specs(target_model_species_ids_in_order()))
    )

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TAXON_OUTPUT}")
    print(f"Wrote {WIDE_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
