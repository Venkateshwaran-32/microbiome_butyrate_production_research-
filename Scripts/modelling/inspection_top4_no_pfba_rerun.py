from __future__ import annotations

import argparse
import csv
import importlib.util
import math
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE_UTILS = load_module("baseline_modeling_utils", SCRIPT_DIR / "00_baseline_modeling_utils.py")
MICOM_UTILS = load_module("micom_utils", SCRIPT_DIR / "00_micom_utils.py")
SUBJECT_UTILS = load_module("subject_level_micom_utils", SCRIPT_DIR / "00_subject_level_micom_utils.py")

SUBJECT_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_taxonomy_for_micom.csv")
DIET_CSV = Path("Medium_files/diet.csv")
HIGH_FIBER_DIET = "high_fiber"
TRADEOFF_FRACTION = 0.5
FLUX_THRESHOLD = 1e-12
DEFAULT_SUBJECTS = ("MBS1232", "MBS1529", "MBS1262", "MBS1255")

SUMMARY_OUTPUT = Path("Results/subject_level_fba/tables/inspection_top4_no_pfba_community.csv")
TAXON_OUTPUT = Path("Results/subject_level_fba/tables/inspection_top4_no_pfba_taxon.csv")
FLUX_OUTPUT = Path("Results/subject_level_fba/tables/inspection_top4_no_pfba_flux.csv")
REPORT_OUTPUT = Path("Results/qc/reports/inspection_top4_no_pfba_report.txt")

build_subject_taxonomy = SUBJECT_UTILS.build_subject_taxonomy
build_subject_taxonomy_rows = SUBJECT_UTILS.build_subject_taxonomy_rows
group_rows_by_subject = SUBJECT_UTILS.group_rows_by_subject
load_subject_level_rows = SUBJECT_UTILS.load_subject_level_rows
validate_subject_rows = SUBJECT_UTILS.validate_subject_rows
GROWTH_THRESHOLD = BASELINE_UTILS.GROWTH_THRESHOLD
load_diet_table = BASELINE_UTILS.load_diet_table
run_cooperative_tradeoff = MICOM_UTILS.run_cooperative_tradeoff
write_csv = MICOM_UTILS.write_csv

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
    "pfba",
    "fluxes",
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
FLUX_FIELDNAMES = [
    "subject_id",
    "cohort",
    "age_years",
    "age_group",
    "diet_name",
    "compartment",
    "taxon_id",
    "reaction_id",
    "feature_id",
    "flux",
    "abs_flux",
    "is_medium",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun the top 4 high-flux subjects without pFBA.")
    parser.add_argument(
        "--subject-id",
        action="append",
        dest="subject_ids",
        help="Subject ID to include. Repeat to include multiple subjects. Defaults to the top 4 flux outliers.",
    )
    return parser.parse_args()


def initialize_csv(path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()


def append_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with open(path, "a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerows(rows)


def iter_nonzero_flux_rows(
    fluxes,
    *,
    subject_id: str,
    cohort: str,
    age_years: float,
    age_group: str,
    diet_name: str,
):
    if fluxes is None:
        return

    try:
        stacked_fluxes = fluxes.stack(future_stack=True)
    except TypeError:
        stacked_fluxes = fluxes.stack(dropna=True)

    for (compartment, reaction_id), flux_value in stacked_fluxes.items():
        flux_value = float(flux_value)
        if not math.isfinite(flux_value):
            continue
        abs_flux = abs(flux_value)
        if abs_flux <= FLUX_THRESHOLD:
            continue
        is_medium = compartment == "medium"
        taxon_id = "" if is_medium else str(compartment)
        yield {
            "subject_id": subject_id,
            "cohort": cohort,
            "age_years": age_years,
            "age_group": age_group,
            "diet_name": diet_name,
            "compartment": str(compartment),
            "taxon_id": taxon_id,
            "reaction_id": str(reaction_id),
            "feature_id": f"medium__{reaction_id}" if is_medium else f"{taxon_id}__{reaction_id}",
            "flux": flux_value,
            "abs_flux": abs_flux,
            "is_medium": is_medium,
        }


def main() -> None:
    args = parse_args()

    try:
        from micom import Community
    except ImportError as exc:
        raise ImportError(
            "MICOM is not installed in this environment. Activate the project venv and install it before rerunning."
        ) from exc

    subject_input_rows = load_subject_level_rows(SUBJECT_INPUT)
    subject_rows_by_subject = group_rows_by_subject(subject_input_rows)
    selected_subject_ids = args.subject_ids or list(DEFAULT_SUBJECTS)

    diet_table = load_diet_table(DIET_CSV)
    if HIGH_FIBER_DIET not in diet_table:
        raise ValueError(f"Diet file {DIET_CSV} does not contain a {HIGH_FIBER_DIET!r} column")
    high_fiber_bounds = diet_table[HIGH_FIBER_DIET]

    initialize_csv(FLUX_OUTPUT, FLUX_FIELDNAMES)

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []
    report_lines = [
        "Inspection top 4 no-pFBA rerun",
        f"Subject input: {SUBJECT_INPUT}",
        f"Diet file: {DIET_CSV}",
        f"Diet: {HIGH_FIBER_DIET}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        "Flux export enabled: True",
        "pFBA enabled: False",
        f"Subjects: {', '.join(selected_subject_ids)}",
        "",
    ]

    for subject_index, subject_id in enumerate(selected_subject_ids, start=1):
        subject_rows = subject_rows_by_subject.get(subject_id)
        if subject_rows is None:
            raise ValueError(f"Selected subject {subject_id} is missing from {SUBJECT_INPUT}")

        validate_subject_rows(subject_id, subject_rows)
        full_subject_rows = build_subject_taxonomy_rows(subject_rows)
        taxonomy, used_equal_abundance_fallback = build_subject_taxonomy(subject_rows)
        subject_metadata = full_subject_rows[0]
        total_input_abundance_raw = sum(float(row["abundance_raw"]) for row in full_subject_rows)
        total_input_abundance_normalized = sum(float(row["abundance_normalized"]) for row in full_subject_rows)

        print(f"[{subject_index}/{len(selected_subject_ids)}] {subject_id}", flush=True)

        try:
            community = Community(
                taxonomy=taxonomy,
                model_db=None,
                id=f"inspection_top4_{subject_id}",
                name=f"inspection_top4_{subject_id}",
                progress=False,
            )
            solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
                community,
                high_fiber_bounds,
                TRADEOFF_FRACTION,
                fluxes=True,
                pfba=False,
            )
        except Exception as exc:
            error_message = str(exc)
            report_lines.append(f"{subject_id}: solve_failed -> {error_message}")
            summary_rows.append(
                {
                    "subject_id": subject_metadata["subject_id"],
                    "cohort": subject_metadata["cohort"],
                    "age_years": subject_metadata["age_years"],
                    "age_group": subject_metadata["age_group"],
                    "diet_name": HIGH_FIBER_DIET,
                    "solver_status": "solve_failed",
                    "community_growth_rate": "",
                    "objective_value": "",
                    "tradeoff_fraction": TRADEOFF_FRACTION,
                    "num_taxa_total": len(full_subject_rows),
                    "num_taxa_with_nonzero_growth": "",
                    "matched_diet_metabolites": "",
                    "missing_diet_metabolites": "",
                    "total_input_abundance_raw": total_input_abundance_raw,
                    "total_input_abundance_normalized": total_input_abundance_normalized,
                    "pfba": False,
                    "fluxes": True,
                    "error_message": error_message,
                }
            )
            continue

        solver_status = str(solution.status)
        if solver_status != "optimal":
            error_message = f"non_optimal_solution_status:{solver_status}"
            report_lines.append(f"{subject_id}: {error_message}")
            summary_rows.append(
                {
                    "subject_id": subject_metadata["subject_id"],
                    "cohort": subject_metadata["cohort"],
                    "age_years": subject_metadata["age_years"],
                    "age_group": subject_metadata["age_group"],
                    "diet_name": HIGH_FIBER_DIET,
                    "solver_status": solver_status,
                    "community_growth_rate": "",
                    "objective_value": "",
                    "tradeoff_fraction": TRADEOFF_FRACTION,
                    "num_taxa_total": len(full_subject_rows),
                    "num_taxa_with_nonzero_growth": "",
                    "matched_diet_metabolites": len(medium),
                    "missing_diet_metabolites": len(missing_metabolites),
                    "total_input_abundance_raw": total_input_abundance_raw,
                    "total_input_abundance_normalized": total_input_abundance_normalized,
                    "pfba": False,
                    "fluxes": True,
                    "error_message": error_message,
                }
            )
            continue

        input_rows_by_taxon = {str(row["model_species_id"]): row for row in full_subject_rows}
        num_taxa_growing = 0
        for member_row in members.itertuples(index=False):
            taxon_id = str(member_row.taxon_id)
            input_row = input_rows_by_taxon.get(taxon_id)
            if input_row is None:
                continue
            growth_rate = float(getattr(member_row, "growth_rate", 0.0))
            is_growing = growth_rate > GROWTH_THRESHOLD
            num_taxa_growing += int(is_growing)
            taxon_rows.append(
                {
                    "subject_id": input_row["subject_id"],
                    "cohort": input_row["cohort"],
                    "age_years": input_row["age_years"],
                    "age_group": input_row["age_group"],
                    "diet_name": HIGH_FIBER_DIET,
                    "taxon_id": taxon_id,
                    "species_name": input_row["species_name"],
                    "paper_taxon": input_row["paper_taxon"],
                    "abundance_raw": input_row["abundance_raw"],
                    "abundance_normalized": input_row["abundance_normalized"],
                    "growth_rate": growth_rate,
                    "is_growing": is_growing,
                    "reactions": getattr(member_row, "reactions", ""),
                    "metabolites": getattr(member_row, "metabolites", ""),
                }
            )

        subject_flux_rows = list(
            iter_nonzero_flux_rows(
                solution.fluxes,
                subject_id=str(subject_metadata["subject_id"]),
                cohort=str(subject_metadata["cohort"]),
                age_years=float(subject_metadata["age_years"]),
                age_group=str(subject_metadata["age_group"]),
                diet_name=HIGH_FIBER_DIET,
            )
        )
        append_csv_rows(FLUX_OUTPUT, FLUX_FIELDNAMES, subject_flux_rows)

        summary_rows.append(
            {
                "subject_id": subject_metadata["subject_id"],
                "cohort": subject_metadata["cohort"],
                "age_years": subject_metadata["age_years"],
                "age_group": subject_metadata["age_group"],
                "diet_name": HIGH_FIBER_DIET,
                "solver_status": solver_status,
                "community_growth_rate": float(solution.growth_rate),
                "objective_value": solution.objective_value,
                "tradeoff_fraction": TRADEOFF_FRACTION,
                "num_taxa_total": len(full_subject_rows),
                "num_taxa_with_nonzero_growth": num_taxa_growing,
                "matched_diet_metabolites": len(medium),
                "missing_diet_metabolites": len(missing_metabolites),
                "total_input_abundance_raw": total_input_abundance_raw,
                "total_input_abundance_normalized": total_input_abundance_normalized,
                "pfba": False,
                "fluxes": True,
                "error_message": "",
            }
        )

        report_lines.append(
            f"{subject_id}: solver_status={solver_status}, community_growth_rate={float(solution.growth_rate)}, "
            f"num_taxa_with_nonzero_growth={num_taxa_growing}, flux_rows={len(subject_flux_rows)}"
        )
        if used_equal_abundance_fallback:
            report_lines.append(
                f"{subject_id}: used equal-abundance fallback because normalized abundances summed to 0.0"
            )

    write_csv(SUMMARY_OUTPUT, SUMMARY_FIELDNAMES, summary_rows)
    write_csv(TAXON_OUTPUT, TAXON_FIELDNAMES, taxon_rows)
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text("\n".join(report_lines) + "\n")

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TAXON_OUTPUT}")
    print(f"Wrote {FLUX_OUTPUT}")
    print(f"Wrote {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
