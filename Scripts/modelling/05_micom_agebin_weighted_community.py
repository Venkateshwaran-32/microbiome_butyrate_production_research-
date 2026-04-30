from __future__ import annotations

import csv
import importlib.util
from collections import defaultdict
from pathlib import Path

# Load the shared COBRApy helper module.
UTILS_PATH = Path(__file__).with_name("00_baseline_modeling_utils.py")
UTILS_SPEC = importlib.util.spec_from_file_location("baseline_modeling_utils", UTILS_PATH)
if UTILS_SPEC is None or UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load utility module from {UTILS_PATH}")
UTILS_MODULE = importlib.util.module_from_spec(UTILS_SPEC)
UTILS_SPEC.loader.exec_module(UTILS_MODULE)

REPORT_UTILS_PATH = Path(__file__).with_name("00_report_output_dictionary.py")
REPORT_UTILS_SPEC = importlib.util.spec_from_file_location("report_output_dictionary", REPORT_UTILS_PATH)
if REPORT_UTILS_SPEC is None or REPORT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load report utility module from {REPORT_UTILS_PATH}")
REPORT_UTILS_MODULE = importlib.util.module_from_spec(REPORT_UTILS_SPEC)
REPORT_UTILS_SPEC.loader.exec_module(REPORT_UTILS_MODULE)

GROWTH_THRESHOLD = UTILS_MODULE.GROWTH_THRESHOLD
load_diet_table = UTILS_MODULE.load_diet_table

MICOM_UTILS_PATH = Path(__file__).with_name("00_micom_utils.py")
MICOM_UTILS_SPEC = importlib.util.spec_from_file_location("micom_utils", MICOM_UTILS_PATH)
if MICOM_UTILS_SPEC is None or MICOM_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load MICOM utility module from {MICOM_UTILS_PATH}")
MICOM_UTILS_MODULE = importlib.util.module_from_spec(MICOM_UTILS_SPEC)
MICOM_UTILS_SPEC.loader.exec_module(MICOM_UTILS_MODULE)

build_agebin_taxonomy = MICOM_UTILS_MODULE.build_agebin_taxonomy
run_cooperative_tradeoff = MICOM_UTILS_MODULE.run_cooperative_tradeoff
write_csv = MICOM_UTILS_MODULE.write_csv
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


AGEBIN_INPUT = Path("Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/micom_fba/tables/05_micom_agebin_community_growth_summary_by_diet.csv")
TAXON_OUTPUT = Path("Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet.csv")
WIDE_OUTPUT = Path("Results/micom_fba/tables/05_micom_agebin_taxon_growth_by_diet_wide.csv")
BUILD_REPORT = Path("Results/micom_fba/reports/05_micom_agebin_model_build_report.txt")
EXPECTED_SPECIES_PER_AGE_BIN = 10
TRADEOFF_FRACTION = 0.5
SUMMARY_FIELDNAMES = [
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
    "n_subjects",
    "total_input_median_abundance",
    "total_input_normalized_weight",
]
TAXON_FIELDNAMES = [
    "age_group",
    "diet_name",
    "taxon_id",
    "species_name",
    "paper_taxon",
    "median_abundance",
    "normalized_weight",
    "n_subjects",
    "growth_rate",
    "is_growing",
    "reactions",
    "metabolites",
]


def load_agebin_table(path: Path) -> dict[str, list[dict[str, str]]]:
    rows = list(csv.DictReader(open(path, newline="")))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["age_group"]].append(row)
    return dict(sorted(grouped.items()))


def validate_agebin_rows(agebin_rows: dict[str, list[dict[str, str]]]) -> list[str]:
    report_lines: list[str] = []
    for age_group, rows in agebin_rows.items():
        if len(rows) != EXPECTED_SPECIES_PER_AGE_BIN:
            raise ValueError(
                f"Expected {EXPECTED_SPECIES_PER_AGE_BIN} rows for age group {age_group}, found {len(rows)}"
            )
        total_weight = sum(float(row["normalized_weight"]) for row in rows)
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError(f"Normalized weights for age group {age_group} sum to {total_weight}, not 1.0")
        model_ids = {row["model_species_id"] for row in rows}
        if len(model_ids) != EXPECTED_SPECIES_PER_AGE_BIN:
            raise ValueError(f"Age group {age_group} contains duplicate model_species_id values")
        for row in rows:
            model_path = Path(row["model_file"])
            if not model_path.exists():
                raise FileNotFoundError(f"Missing model file referenced by age-bin input: {model_path}")
        report_lines.append(
            f"{age_group}: rows={len(rows)}, total_normalized_weight={total_weight}, n_subjects={rows[0]['n_subjects']}"
        )
    return report_lines


def build_agebin_metadata(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    metadata: dict[str, dict[str, object]] = {}
    for row in rows:
        metadata[row["model_species_id"]] = {
            "species_name": row["species_name"],
            "paper_taxon": row["paper_taxon"],
            "median_abundance": float(row["median_abundance"]),
            "normalized_weight": float(row["normalized_weight"]),
            "n_subjects": int(row["n_subjects"]),
            "model_file": row["model_file"],
        }
    return metadata


def build_wide_rows(taxon_rows: list[dict[str, object]], age_groups: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in taxon_rows:
        key = (str(row["taxon_id"]), str(row["diet_name"]))
        existing = grouped.get(key)
        if existing is None:
            existing = {
                "taxon_id": row["taxon_id"],
                "species_name": row["species_name"],
                "paper_taxon": row["paper_taxon"],
                "diet_name": row["diet_name"],
            }
            grouped[key] = existing
        existing[str(row["age_group"])] = row["growth_rate"]

    wide_rows: list[dict[str, object]] = []
    for _, row in sorted(grouped.items()):
        for age_group in age_groups:
            row.setdefault(age_group, "")
        wide_rows.append(row)
    return wide_rows


def classify_growth_trend(observed_values: list[float]) -> str:
    if len(observed_values) < 2:
        return "insufficient_range"
    if all(abs(observed_values[i] - observed_values[i + 1]) <= GROWTH_THRESHOLD for i in range(len(observed_values) - 1)):
        return "constant"
    if all(observed_values[i] <= observed_values[i + 1] + GROWTH_THRESHOLD for i in range(len(observed_values) - 1)):
        return "increasing_across_observed_bins"
    if all(observed_values[i] + GROWTH_THRESHOLD >= observed_values[i + 1] for i in range(len(observed_values) - 1)):
        return "decreasing_across_observed_bins"
    return "mixed_nonmonotonic"


def build_trend_report_lines(wide_rows: list[dict[str, object]], age_groups: list[str]) -> list[str]:
    report_lines = ["Taxon growth trend summary"]
    for row in wide_rows:
        observed_bins = [age_group for age_group in age_groups if row.get(age_group, "") != ""]
        observed_values = [float(row[age_group]) for age_group in observed_bins]
        trend = classify_growth_trend(observed_values)
        values_text = ", ".join(f"{age_group}={float(row[age_group]):.6f}" for age_group in observed_bins)
        report_lines.append(
            f"{row['diet_name']} | {row['taxon_id']}: observed_bins={', '.join(observed_bins)}; "
            f"trend={trend}; values -> {values_text}"
        )
    return report_lines


def build_csv_output_specs(age_groups: list[str]) -> list[dict[str, object]]:
    return [
        csv_output_spec(
            SUMMARY_OUTPUT,
            "one row per age_group x diet_name",
            [
                col("age_group", "Age-bin label for the MICOM median-abundance community."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("solver_status", "MICOM solver status returned for the cooperative tradeoff solve."),
                col("community_growth_rate", "MICOM-reported community growth rate for the selected age bin and diet."),
                col(
                    "objective_value",
                    "Objective value returned by MICOM for this age-bin cooperative tradeoff solve.",
                    "objective_value = optimization objective reported by MICOM after cooperative_tradeoff",
                ),
                col("tradeoff_fraction", "Tradeoff fraction passed into MICOM cooperative tradeoff."),
                col("num_taxa_total", "Number of taxa returned in the MICOM members table for this age bin and diet."),
                col(
                    "num_taxa_with_nonzero_growth",
                    "Count of taxa whose MICOM growth rate exceeded the growth threshold.",
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
                col("n_subjects", "Number of subjects contributing to the median-abundance age-bin input."),
                col(
                    "total_input_median_abundance",
                    "Sum of the median abundances supplied for the 10 modeled taxa in this age bin.",
                    "total_input_median_abundance = sum(median_abundance across all taxon_id within age_group)",
                ),
                col(
                    "total_input_normalized_weight",
                    "Sum of the normalized abundances used for the age-bin MICOM taxonomy.",
                    "total_input_normalized_weight = sum(normalized_weight across all taxon_id within age_group)",
                ),
            ],
        ),
        csv_output_spec(
            TAXON_OUTPUT,
            "one row per age_group x diet_name x taxon_id",
            [
                col("age_group", "Age-bin label for the MICOM median-abundance community."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("taxon_id", "MICOM taxon/model identifier."),
                col("species_name", "Species label from the processed age-bin input table."),
                col("paper_taxon", "Original paper taxon label mapped onto this model species."),
                col("median_abundance", "Median abundance supplied for this taxon in the selected age bin."),
                col(
                    "normalized_weight",
                    "Normalized abundance used in the age-bin MICOM taxonomy table.",
                    "normalized_weight = median_abundance / sum(median_abundance within age_group)",
                ),
                col("n_subjects", "Number of subjects contributing to the median-abundance value for this age bin."),
                col("growth_rate", "MICOM-reported taxon growth rate for this age bin and diet."),
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
            "one row per taxon_id x diet_name",
            [
                col("taxon_id", "MICOM taxon/model identifier."),
                col("species_name", "Species label from the processed age-bin input table."),
                col("paper_taxon", "Original paper taxon label mapped onto this model species."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                *[
                    col(
                        age_group,
                        f"MICOM taxon growth rate for age group {age_group}; blank means no row was written for that age group.",
                    )
                    for age_group in age_groups
                ],
            ],
        ),
    ]


def main() -> None:
    try:
        from micom import Community
    except ImportError as exc:
        raise ImportError(
            "MICOM is not installed in this environment. Install it first, for example with "
            "`pip install micom`, then rerun Scripts/modelling/05_micom_agebin_weighted_community.py."
        ) from exc

    agebin_rows = load_agebin_table(AGEBIN_INPUT)
    diet_table = load_diet_table(DIET_CSV)
    ordered_age_groups = sorted(agebin_rows)

    report_lines = [
        "MICOM age-bin community build report",
        f"Input table: {AGEBIN_INPUT}",
        f"Diet file: {DIET_CSV}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        f"Age bins: {', '.join(ordered_age_groups)}",
        "",
        "Input validation",
    ]
    report_lines.extend(validate_agebin_rows(agebin_rows))
    report_lines.append("")

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []

    for age_group in ordered_age_groups:
        age_rows = agebin_rows[age_group]
        metadata_by_model_id = build_agebin_metadata(age_rows)
        taxonomy = build_agebin_taxonomy(age_rows)
        community_id = f"micom_agebin_{age_group}"
        community = Community(taxonomy=taxonomy, model_db=None, id=community_id, name=community_id, progress=False)

        total_input_median_abundance = sum(
            metadata["median_abundance"] for metadata in metadata_by_model_id.values()
        )
        total_input_normalized_weight = sum(
            metadata["normalized_weight"] for metadata in metadata_by_model_id.values()
        )
        n_subjects = next(iter(metadata_by_model_id.values()))["n_subjects"]

        report_lines.append(f"{age_group}:")
        report_lines.append(
            "  abundances -> "
            + ", ".join(
                f"{row['model_species_id']}={float(row['normalized_weight']):.6f}"
                for row in age_rows
            )
        )

        for diet_name, diet_bounds in diet_table.items():
            solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
                community,
                diet_bounds,
                TRADEOFF_FRACTION,
            )

            num_taxa_growing = 0
            for row in members.itertuples(index=False):
                taxon_id = str(row.taxon_id)
                metadata = metadata_by_model_id[taxon_id]
                growth_rate = float(getattr(row, "growth_rate", 0.0))
                is_growing = growth_rate > GROWTH_THRESHOLD
                num_taxa_growing += int(is_growing)
                taxon_rows.append(
                    {
                        "age_group": age_group,
                        "diet_name": diet_name,
                        "taxon_id": taxon_id,
                        "species_name": metadata["species_name"],
                        "paper_taxon": metadata["paper_taxon"],
                        "median_abundance": metadata["median_abundance"],
                        "normalized_weight": metadata["normalized_weight"],
                        "n_subjects": metadata["n_subjects"],
                        "growth_rate": growth_rate,
                        "is_growing": is_growing,
                        "reactions": getattr(row, "reactions", ""),
                        "metabolites": getattr(row, "metabolites", ""),
                    }
                )

            summary_rows.append(
                {
                    "age_group": age_group,
                    "diet_name": diet_name,
                    "solver_status": solution.status,
                    "community_growth_rate": solution.growth_rate,
                    "objective_value": solution.objective_value,
                    "tradeoff_fraction": TRADEOFF_FRACTION,
                    "num_taxa_total": len(members),
                    "num_taxa_with_nonzero_growth": num_taxa_growing,
                    "matched_diet_metabolites": len(medium),
                    "missing_diet_metabolites": len(missing_metabolites),
                    "n_subjects": n_subjects,
                    "total_input_median_abundance": total_input_median_abundance,
                    "total_input_normalized_weight": total_input_normalized_weight,
                }
            )

            report_lines.append(
                f"  {diet_name}: solver_status={solution.status}, community_growth_rate={solution.growth_rate}, "
                f"matched_diet_metabolites={len(medium)}, missing_diet_metabolites={len(missing_metabolites)}"
            )
            if missing_metabolites:
                report_lines.append(f"  {diet_name} missing metabolite_ids: {', '.join(sorted(missing_metabolites))}")
        report_lines.append("")

    wide_rows = build_wide_rows(taxon_rows, ordered_age_groups)
    report_lines.append("")
    report_lines.extend(build_trend_report_lines(wide_rows, ordered_age_groups))

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
        ["taxon_id", "species_name", "paper_taxon", "diet_name", *ordered_age_groups],
        wide_rows,
    )
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, build_csv_output_specs(ordered_age_groups)))

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TAXON_OUTPUT}")
    print(f"Wrote {WIDE_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
