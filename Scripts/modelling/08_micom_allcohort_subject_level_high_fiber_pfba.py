from __future__ import annotations

import argparse
import csv
import importlib.util
import math
from collections import Counter
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

ALLCOHORT_AGE_GROUPS = SUBJECT_UTILS_MODULE.ALLCOHORT_AGE_GROUPS
build_subject_taxonomy = SUBJECT_UTILS_MODULE.build_subject_taxonomy
build_subject_taxonomy_rows = SUBJECT_UTILS_MODULE.build_subject_taxonomy_rows
csv_bool = SUBJECT_UTILS_MODULE.csv_bool
group_rows_by_subject = SUBJECT_UTILS_MODULE.group_rows_by_subject
load_subject_level_rows = SUBJECT_UTILS_MODULE.load_subject_level_rows
validate_subject_rows = SUBJECT_UTILS_MODULE.validate_subject_rows

GROWTH_THRESHOLD = BASELINE_UTILS_MODULE.GROWTH_THRESHOLD
load_diet_table = BASELINE_UTILS_MODULE.load_diet_table
run_cooperative_tradeoff = MICOM_UTILS_MODULE.run_cooperative_tradeoff
write_csv = MICOM_UTILS_MODULE.write_csv
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


SUBJECT_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_taxonomy_for_micom.csv")
QC_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_subject_input_qc_summary.csv")
ABUNDANCE_MISSING_METADATA_INPUT = Path(
    "Suplementary_Data/processed_data/subject_level_micom_allcohort/allcohort_abundance_subjects_missing_from_metadata.csv"
)
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv")
TAXON_OUTPUT = Path("Results/subject_level_fba/tables/08_allcohort_subject_taxon_growth_high_fiber_pfba.csv")
FLUX_OUTPUT = Path("Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv")
BUILD_REPORT = Path("Results/subject_level_fba/reports/08_allcohort_subject_level_high_fiber_pfba_build_report.txt")

COHORT_CHOICES = ("CRE", "SG90", "SPMP", "T2D")
HIGH_FIBER_DIET = "high_fiber"
TRADEOFF_FRACTION = 0.5
FLUX_THRESHOLD = 1e-12
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
CSV_OUTPUT_SPECS = [
    csv_output_spec(
        SUMMARY_OUTPUT,
        "one row per subject_id for the high_fiber diet",
        [
            col("subject_id", "Subject identifier from the all-cohort subject-level MICOM input table."),
            col("cohort", "Cohort label carried through from the subject metadata."),
            col("age_years", "Subject age in years from the metadata table."),
            col("age_group", "Age-bin label assigned from the metadata age."),
            col("diet_name", "Diet scenario name; this script writes high_fiber only."),
            col("solver_status", "MICOM solver status returned for this subject-level solve."),
            col(
                "community_growth_rate",
                "MICOM-reported community growth rate for this subject under high_fiber; blank for non-optimal solves.",
            ),
            col(
                "objective_value",
                "Objective value returned by MICOM for this subject-level cooperative tradeoff plus pFBA solve.",
                "objective_value = optimization objective reported by MICOM after cooperative_tradeoff with pfba=True",
            ),
            col("tradeoff_fraction", "Tradeoff fraction passed into MICOM cooperative tradeoff."),
            col("num_taxa_total", "Number of modeled taxa carried into the subject-level MICOM community input."),
            col(
                "num_taxa_with_nonzero_growth",
                "Count of returned taxa whose MICOM growth rate exceeded the growth threshold.",
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
            col("pfba", "Boolean flag showing that pFBA flux extraction was requested for this solve."),
            col("fluxes", "Boolean flag showing that MICOM flux export was requested for this solve."),
            col("error_message", "Error text recorded for failed community-build or solve attempts; blank otherwise."),
        ],
    ),
    csv_output_spec(
        TAXON_OUTPUT,
        "one row per subject_id x taxon_id for the high_fiber diet",
        [
            col("subject_id", "Subject identifier from the all-cohort subject-level MICOM input table."),
            col("cohort", "Cohort label carried through from the subject metadata."),
            col("age_years", "Subject age in years from the metadata table."),
            col("age_group", "Age-bin label assigned from the metadata age."),
            col("diet_name", "Diet scenario name; this script writes high_fiber only."),
            col("taxon_id", "MICOM taxon/model identifier."),
            col("species_name", "Species label mapped onto this model taxon."),
            col("paper_taxon", "Original paper taxon label mapped onto this model species."),
            col("abundance_raw", "Raw subject-level abundance used for this taxon."),
            col(
                "abundance_normalized",
                "Normalized subject-level abundance used for the MICOM taxonomy.",
                "abundance_normalized = abundance_raw / sum(abundance_raw across modeled taxa within subject_id) when the within-subject total is positive",
            ),
            col(
                "growth_rate",
                "MICOM-reported taxon growth rate for this subject under high_fiber. Taxon rows are written only for optimal solves.",
            ),
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
        FLUX_OUTPUT,
        "one row per subject_id x compartment x reaction_id with nonzero exported flux for optimal solves",
        [
            col("subject_id", "Subject identifier from the all-cohort subject-level MICOM input table."),
            col("cohort", "Cohort label carried through from the subject metadata."),
            col("age_years", "Subject age in years from the metadata table."),
            col("age_group", "Age-bin label assigned from the metadata age."),
            col("diet_name", "Diet scenario name; this script writes high_fiber only."),
            col("compartment", "Flux compartment label from the MICOM flux table; either a taxon_id or the literal medium compartment."),
            col("taxon_id", "Taxon identifier for organism-level flux rows; blank for medium rows."),
            col("reaction_id", "Reaction identifier from the MICOM flux export."),
            col(
                "feature_id",
                "Compact feature label combining compartment scope with the reaction ID.",
                "feature_id = 'medium__' + reaction_id for medium rows, otherwise taxon_id + '__' + reaction_id",
            ),
            col("flux", "Signed flux value exported by MICOM for this subject, compartment, and reaction."),
            col("abs_flux", "Absolute flux magnitude for this exported row.", "abs_flux = abs(flux)"),
            col(
                "is_medium",
                "Boolean flag showing whether the exported flux row came from the shared medium compartment.",
                "is_medium = (compartment == 'medium')",
            ),
        ],
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all-cohort subject-level MICOM with high-fiber pFBA flux export."
    )
    parser.add_argument("--subject-id", help="Run a single subject ID only.")
    parser.add_argument("--cohort", choices=COHORT_CHOICES, help="Restrict to one cohort.")
    parser.add_argument("--age-group", choices=ALLCOHORT_AGE_GROUPS, help="Restrict to one age group.")
    parser.add_argument("--limit", type=int, help="Limit the number of selected subjects.")
    return parser.parse_args()


def load_qc_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def load_optional_csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def select_subject_ids(qc_rows: list[dict[str, str]], args: argparse.Namespace) -> list[str]:
    selected_rows = [row for row in qc_rows if csv_bool(row["include_in_subject_micom"])]
    if args.cohort:
        selected_rows = [row for row in selected_rows if row["cohort"] == args.cohort]
    if args.age_group:
        selected_rows = [row for row in selected_rows if row["age_group"] == args.age_group]
    if args.subject_id:
        selected_rows = [row for row in selected_rows if row["subject_id"] == args.subject_id]
        if not selected_rows:
            raise ValueError(f"No included subject matched --subject-id {args.subject_id}")
    selected_rows = sorted(selected_rows, key=lambda row: row["subject_id"])
    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be a positive integer")
        selected_rows = selected_rows[: args.limit]
    return [row["subject_id"] for row in selected_rows]


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
            "MICOM is not installed in this environment. Install it first, for example with "
            "`pip install micom`, then rerun Scripts/modelling/08_micom_allcohort_subject_level_high_fiber_pfba.py."
        ) from exc

    subject_input_rows = load_subject_level_rows(SUBJECT_INPUT)
    qc_rows = load_qc_rows(QC_INPUT)
    qc_by_subject = {row["subject_id"]: row for row in qc_rows}
    subject_rows_by_subject = group_rows_by_subject(subject_input_rows)
    diet_table = load_diet_table(DIET_CSV)
    if HIGH_FIBER_DIET not in diet_table:
        raise ValueError(f"Diet file {DIET_CSV} does not contain a {HIGH_FIBER_DIET!r} column")
    high_fiber_bounds = diet_table[HIGH_FIBER_DIET]
    selected_subject_ids = select_subject_ids(qc_rows, args)

    total_qc_subjects = len(qc_rows)
    total_included_subjects = sum(csv_bool(row["include_in_subject_micom"]) for row in qc_rows)
    total_metadata_only_subjects = total_qc_subjects - total_included_subjects
    total_abundance_only_subjects = load_optional_csv_row_count(ABUNDANCE_MISSING_METADATA_INPUT)
    total_zero_abundance_subjects = sum(
        csv_bool(row["include_in_subject_micom"]) and csv_bool(row["all_modeled_taxa_zero"])
        for row in qc_rows
    )
    selected_qc_rows = [qc_by_subject[subject_id] for subject_id in selected_subject_ids]
    selected_cohort_counts = Counter(row["cohort"] for row in selected_qc_rows)
    selected_age_counts = Counter(row["age_group"] for row in selected_qc_rows)
    selected_nonzero_taxa_counts = Counter(int(row["n_nonzero_modeled_taxa"]) for row in selected_qc_rows)

    report_lines = [
        "All-cohort subject-level MICOM high-fiber pFBA build report",
        f"Subject input: {SUBJECT_INPUT}",
        f"QC input: {QC_INPUT}",
        f"Diet file: {DIET_CSV}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        f"Selection filters: subject_id={args.subject_id or 'ALL'}, cohort={args.cohort or 'ALL'}, age_group={args.age_group or 'ALL'}, limit={args.limit or 'ALL'}",
        f"Flux export enabled: True",
        f"pFBA enabled: True",
        "",
        f"Total subjects in QC table: {total_qc_subjects}",
        f"Included abundance-matched subjects: {total_included_subjects}",
        f"Metadata-only excluded subjects: {total_metadata_only_subjects}",
        f"Abundance-only missing-metadata subjects: {total_abundance_only_subjects}",
        f"Included subjects with zero total modeled abundance: {total_zero_abundance_subjects}",
        f"Selected subjects for this run: {len(selected_subject_ids)}",
        "",
        "Selected subject counts by cohort",
    ]
    report_lines.extend(f"{cohort}: {count}" for cohort, count in sorted(selected_cohort_counts.items()))
    report_lines.append("")
    report_lines.append("Selected subject counts by age group")
    report_lines.extend(f"{age_group}: {selected_age_counts[age_group]}" for age_group in ALLCOHORT_AGE_GROUPS)
    report_lines.append("")
    report_lines.append("Selected subject nonzero modeled taxon distribution")
    report_lines.extend(
        f"{count} nonzero taxa: {n_subjects} subjects"
        for count, n_subjects in sorted(selected_nonzero_taxa_counts.items())
    )
    report_lines.append("")

    initialize_csv(FLUX_OUTPUT, FLUX_FIELDNAMES)

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []
    failures: list[str] = []
    community_rows_written = 0
    taxon_rows_written = 0
    flux_rows_written = 0
    zero_growth_subjects = 0
    nonoptimal_status_counts: Counter[str] = Counter()

    for subject_index, subject_id in enumerate(selected_subject_ids, start=1):
        subject_rows = subject_rows_by_subject.get(subject_id)
        if subject_rows is None:
            raise ValueError(f"Selected subject {subject_id} is missing from {SUBJECT_INPUT}")

        validate_subject_rows(subject_id, subject_rows)
        full_subject_rows = build_subject_taxonomy_rows(subject_rows)
        taxonomy, used_equal_abundance_fallback = build_subject_taxonomy(subject_rows)
        community_id = f"micom_subject_{subject_id}"
        subject_metadata = full_subject_rows[0]
        total_input_abundance_raw = sum(float(row["abundance_raw"]) for row in full_subject_rows)
        total_input_abundance_normalized = sum(float(row["abundance_normalized"]) for row in full_subject_rows)

        print(f"[{subject_index}/{len(selected_subject_ids)}] {subject_id}")

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
            summary_rows.append(
                {
                    "subject_id": subject_metadata["subject_id"],
                    "cohort": subject_metadata["cohort"],
                    "age_years": subject_metadata["age_years"],
                    "age_group": subject_metadata["age_group"],
                    "diet_name": HIGH_FIBER_DIET,
                    "solver_status": "community_build_failed",
                    "community_growth_rate": "",
                    "objective_value": "",
                    "tradeoff_fraction": TRADEOFF_FRACTION,
                    "num_taxa_total": len(full_subject_rows),
                    "num_taxa_with_nonzero_growth": "",
                    "matched_diet_metabolites": "",
                    "missing_diet_metabolites": "",
                    "total_input_abundance_raw": total_input_abundance_raw,
                    "total_input_abundance_normalized": total_input_abundance_normalized,
                    "pfba": True,
                    "fluxes": True,
                    "error_message": error_message,
                }
            )
            community_rows_written += 1
            continue

        try:
            solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
                community,
                high_fiber_bounds,
                TRADEOFF_FRACTION,
                fluxes=True,
                pfba=True,
            )
        except Exception as exc:
            error_message = str(exc)
            failures.append(f"{subject_id} | {HIGH_FIBER_DIET}: solve_failed -> {error_message}")
            report_lines.append(f"{subject_id} | {HIGH_FIBER_DIET}: solve_failed -> {error_message}")
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
                    "pfba": True,
                    "fluxes": True,
                    "error_message": error_message,
                }
            )
            community_rows_written += 1
            continue

        solver_status = str(solution.status)
        if solver_status != "optimal":
            nonoptimal_status_counts[solver_status] += 1
            error_message = f"non_optimal_solution_status:{solver_status}"
            failures.append(f"{subject_id} | {HIGH_FIBER_DIET}: {error_message}")
            report_lines.append(f"{subject_id} | {HIGH_FIBER_DIET}: {error_message}")
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
                    "pfba": True,
                    "fluxes": True,
                    "error_message": error_message,
                }
            )
            community_rows_written += 1
            continue

        input_rows_by_taxon = {str(row["model_species_id"]): row for row in full_subject_rows}
        num_taxa_growing = 0
        subject_taxon_rows: list[dict[str, object]] = []

        for member_row in members.itertuples(index=False):
            taxon_id = str(member_row.taxon_id)
            input_row = input_rows_by_taxon.get(taxon_id)
            if input_row is None:
                continue
            growth_rate = float(getattr(member_row, "growth_rate", 0.0))
            is_growing = growth_rate > GROWTH_THRESHOLD
            num_taxa_growing += int(is_growing)
            subject_taxon_rows.append(
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

        growth_rate = float(solution.growth_rate)
        if abs(growth_rate) <= GROWTH_THRESHOLD:
            zero_growth_subjects += 1

        summary_rows.append(
            {
                "subject_id": subject_metadata["subject_id"],
                "cohort": subject_metadata["cohort"],
                "age_years": subject_metadata["age_years"],
                "age_group": subject_metadata["age_group"],
                "diet_name": HIGH_FIBER_DIET,
                "solver_status": solver_status,
                "community_growth_rate": growth_rate,
                "objective_value": solution.objective_value,
                "tradeoff_fraction": TRADEOFF_FRACTION,
                "num_taxa_total": len(full_subject_rows),
                "num_taxa_with_nonzero_growth": num_taxa_growing,
                "matched_diet_metabolites": len(medium),
                "missing_diet_metabolites": len(missing_metabolites),
                "total_input_abundance_raw": total_input_abundance_raw,
                "total_input_abundance_normalized": total_input_abundance_normalized,
                "pfba": True,
                "fluxes": True,
                "error_message": "",
            }
        )
        community_rows_written += 1
        taxon_rows.extend(subject_taxon_rows)
        taxon_rows_written += len(subject_taxon_rows)

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
        flux_rows_written += len(subject_flux_rows)

        if used_equal_abundance_fallback:
            report_lines.append(
                f"{subject_id}: used equal-abundance fallback because normalized abundances summed to 0.0"
            )

    report_lines.append("")
    if nonoptimal_status_counts:
        report_lines.append("Non-optimal solver statuses")
        report_lines.extend(
            f"{status}: {count}" for status, count in sorted(nonoptimal_status_counts.items())
        )
        report_lines.append("")
    report_lines.append(f"Optimal subjects with community_growth_rate <= {GROWTH_THRESHOLD}: {zero_growth_subjects}")
    report_lines.append(f"Community rows written: {community_rows_written}")
    report_lines.append(f"Taxon rows written: {taxon_rows_written}")
    report_lines.append(f"Flux rows written: {flux_rows_written}")
    report_lines.append("")
    report_lines.append("Output files")
    report_lines.append(f"Community table: {SUMMARY_OUTPUT}")
    report_lines.append(f"Taxon table: {TAXON_OUTPUT}")
    report_lines.append(f"Flux table: {FLUX_OUTPUT}")
    report_lines.append(f"Build report: {BUILD_REPORT}")
    if failures:
        report_lines.append("")
        report_lines.append("Failure list")
        report_lines.extend(failures)

    write_csv(SUMMARY_OUTPUT, SUMMARY_FIELDNAMES, summary_rows)
    write_csv(TAXON_OUTPUT, TAXON_FIELDNAMES, taxon_rows)
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, CSV_OUTPUT_SPECS))

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TAXON_OUTPUT}")
    print(f"Wrote {FLUX_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
