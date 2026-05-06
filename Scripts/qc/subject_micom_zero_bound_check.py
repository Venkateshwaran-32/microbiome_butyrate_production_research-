from __future__ import annotations

import argparse
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODELLING_DIR = SCRIPT_DIR.parent / "modelling"


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUBJECT_UTILS = load_module("subject_level_micom_utils", MODELLING_DIR / "00_subject_level_micom_utils.py")
BASELINE_UTILS = load_module("baseline_modeling_utils", MODELLING_DIR / "00_baseline_modeling_utils.py")
MICOM_UTILS = load_module("micom_utils", MODELLING_DIR / "00_micom_utils.py")

SUBJECT_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_sg90/sg90_subject_taxonomy_for_micom.csv")
DIET_CSV = Path("Medium_files/diet.csv")
DEFAULT_SUBJECTS = ("MBS1232", "MBS1255", "MBS1478", "MBS1515")
DEFAULT_DIET = "high_fiber"
SCENARIO_NAME = "all_bounds_zero_all_taxa"
TRADEOFF_FRACTION = 0.5

SUMMARY_OUTPUT = Path("Results/qc/tables/micom_zero_bound_subject_summary.csv")
TARGET_OUTPUT = Path("Results/qc/tables/micom_zero_bound_target_taxon_growth.csv")
REPORT_OUTPUT = Path("Results/qc/reports/micom_zero_bound_subject_report.txt")

build_subject_taxonomy = SUBJECT_UTILS.build_subject_taxonomy
build_subject_taxonomy_rows = SUBJECT_UTILS.build_subject_taxonomy_rows
group_rows_by_subject = SUBJECT_UTILS.group_rows_by_subject
load_subject_level_rows = SUBJECT_UTILS.load_subject_level_rows
load_diet_table = BASELINE_UTILS.load_diet_table
run_cooperative_tradeoff = MICOM_UTILS.run_cooperative_tradeoff
write_csv = MICOM_UTILS.write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a MICOM QC where all reactions in all 10 community member models are set to bounds (0, 0)."
    )
    parser.add_argument(
        "--subject-id",
        action="append",
        dest="subject_ids",
        help="Subject ID to include. Repeat the flag to include multiple subjects. Defaults to the four QC subjects.",
    )
    parser.add_argument(
        "--diet-name",
        default=DEFAULT_DIET,
        help=f"Diet name to run. Default: {DEFAULT_DIET}",
    )
    return parser.parse_args()


def build_zero_bound_copy(source_model_path: str | Path, destination_dir: Path) -> Path:
    from cobra.io import read_sbml_model, write_sbml_model

    source_model_path = Path(source_model_path)
    model = read_sbml_model(source_model_path)

    # Block the full model so MICOM can test whether any growth survives
    # once this member loses all reaction capacity.
    for reaction in model.reactions:
        reaction.bounds = (0.0, 0.0)

    blocked_path = destination_dir / f"{source_model_path.stem}__all_bounds_zero.xml"
    write_sbml_model(model, blocked_path)
    return blocked_path


def build_all_taxa_zero_bound_taxonomy(subject_rows: list[dict[str, object]], destination_dir: Path):
    taxonomy, _ = build_subject_taxonomy(subject_rows)
    blocked_paths: list[Path] = []

    for index, row in taxonomy.iterrows():
        blocked_path = build_zero_bound_copy(row["file"], destination_dir)
        taxonomy.loc[index, "file"] = str(blocked_path)
        blocked_paths.append(blocked_path)

    return taxonomy, blocked_paths


def members_by_taxon(members) -> dict[str, object]:
    return {str(row.taxon_id): row for row in members.itertuples(index=False)}


def main() -> None:
    args = parse_args()

    try:
        from micom import Community
    except ImportError as exc:
        raise ImportError("MICOM is not installed. Activate the project venv and install `micom` before running this QC script.") from exc

    subject_input_rows = load_subject_level_rows(SUBJECT_INPUT)
    subject_rows_by_subject = group_rows_by_subject(subject_input_rows)
    selected_subject_ids = args.subject_ids or list(DEFAULT_SUBJECTS)

    diet_table = load_diet_table(DIET_CSV)
    if args.diet_name not in diet_table:
        raise ValueError(f"Unknown diet name: {args.diet_name}")
    diet_bounds = diet_table[args.diet_name]

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []
    failed_subjects: list[str] = []
    report_lines = [
        "MICOM zero-bound subject QC",
        "Previous single-taxon zero-bound outputs were replaced by all-10-species zero-bound outputs.",
        f"Subject input: {SUBJECT_INPUT}",
        f"Diet file: {DIET_CSV}",
        f"Diet run: {args.diet_name}",
        f"Scenario: {SCENARIO_NAME}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        f"Subjects: {', '.join(selected_subject_ids)}",
        "All 10 member models had every reaction bound set to (0, 0) before MICOM community construction.",
        "Per-taxon rows are omitted for any subject whose solve fails.",
        "",
    ]

    with tempfile.TemporaryDirectory(prefix="micom_zero_bounds_") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)

        for subject_id in selected_subject_ids:
            subject_rows = subject_rows_by_subject.get(subject_id)
            if subject_rows is None:
                raise ValueError(f"Subject {subject_id} is missing from {SUBJECT_INPUT}")

            print(f"Preparing {subject_id}", flush=True)
            full_subject_rows = build_subject_taxonomy_rows(subject_rows)
            blocked_taxonomy, blocked_paths = build_all_taxa_zero_bound_taxonomy(subject_rows, tmp_dir)

            try:
                community = Community(
                    taxonomy=blocked_taxonomy,
                    model_db=None,
                    id=f"micom_{subject_id}_{SCENARIO_NAME}",
                    name=f"micom_{subject_id}_{SCENARIO_NAME}",
                    progress=False,
                )

                print(f"Running {subject_id} | {SCENARIO_NAME} | {args.diet_name}", flush=True)
                solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
                    community,
                    diet_bounds,
                    TRADEOFF_FRACTION,
                )
            except Exception as exc:
                failed_subjects.append(subject_id)
                error_message = str(exc)
                summary_rows.append(
                    {
                        "subject_id": subject_id,
                        "diet_name": args.diet_name,
                        "scenario": SCENARIO_NAME,
                        "solver_status": "solve_failed",
                        "community_growth_rate": "",
                        "objective_value": "",
                        "matched_diet_metabolites": "",
                        "missing_diet_metabolites": "",
                        "error_message": error_message,
                    }
                )
                report_lines.append(f"{subject_id}: solve_failed -> {error_message}")
                continue

            summary_rows.append(
                {
                    "subject_id": subject_id,
                    "diet_name": args.diet_name,
                    "scenario": SCENARIO_NAME,
                    "solver_status": solution.status,
                    "community_growth_rate": solution.growth_rate,
                    "objective_value": solution.objective_value,
                    "matched_diet_metabolites": len(medium),
                    "missing_diet_metabolites": len(missing_metabolites),
                    "error_message": "",
                }
            )

            member_lookup = members_by_taxon(members)
            for input_row in full_subject_rows:
                taxon_id = str(input_row["model_species_id"])
                member_row = member_lookup.get(taxon_id)
                growth_rate = float(getattr(member_row, "growth_rate", 0.0)) if member_row is not None else 0.0
                taxon_rows.append(
                    {
                        "subject_id": subject_id,
                        "diet_name": args.diet_name,
                        "scenario": SCENARIO_NAME,
                        "taxon_id": taxon_id,
                        "species_name": input_row["species_name"],
                        "abundance_raw": input_row["abundance_raw"],
                        "abundance_normalized": input_row["abundance_normalized"],
                        "growth_rate": growth_rate,
                        "reactions": getattr(member_row, "reactions", "") if member_row is not None else "",
                        "metabolites": getattr(member_row, "metabolites", "") if member_row is not None else "",
                    }
                )

            report_lines.append(
                f"{subject_id}: solver_status={solution.status}, community_growth_rate={solution.growth_rate}, "
                f"blocked_models={len(blocked_paths)}, matched_diet_metabolites={len(medium)}, "
                f"missing_diet_metabolites={len(missing_metabolites)}"
            )

    write_csv(
        SUMMARY_OUTPUT,
        [
            "subject_id",
            "diet_name",
            "scenario",
            "solver_status",
            "community_growth_rate",
            "objective_value",
            "matched_diet_metabolites",
            "missing_diet_metabolites",
            "error_message",
        ],
        summary_rows,
    )
    write_csv(
        TARGET_OUTPUT,
        [
            "subject_id",
            "diet_name",
            "scenario",
            "taxon_id",
            "species_name",
            "abundance_raw",
            "abundance_normalized",
            "growth_rate",
            "reactions",
            "metabolites",
        ],
        taxon_rows,
    )

    if failed_subjects:
        report_lines.append("")
        report_lines.append(f"Failed subjects with omitted per-taxon rows: {', '.join(failed_subjects)}")

    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text("\n".join(report_lines) + "\n")

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TARGET_OUTPUT}")
    print(f"Wrote {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
