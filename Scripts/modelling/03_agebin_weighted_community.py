from __future__ import annotations

import csv
import importlib.util
from collections import defaultdict
from pathlib import Path

# Load the helper module living next to this script.
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
build_shared_environment_community = UTILS_MODULE.build_shared_environment_community
load_diet_table = UTILS_MODULE.load_diet_table
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


AGEBIN_INPUT = Path("Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_growth_summary_by_diet.csv")
SPECIES_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv")
WIDE_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet_wide.csv")
BUILD_REPORT = Path("Results/cobrapy_fba/reports/03_agebin_community_model_build_report.txt")
EXPECTED_SPECIES_PER_AGE_BIN = 10
SUMMARY_FIELDNAMES = [
    "age_group",
    "diet_name",
    "solver_status",
    "community_objective_value",
    "sum_species_biomass_flux",
    "num_species_with_nonzero_growth",
    "community_ex_but_flux",
    "matched_diet_metabolites",
    "missing_diet_metabolites",
    "n_subjects",
    "total_input_median_abundance",
    "total_input_normalized_weight",
]
SPECIES_FIELDNAMES = [
    "age_group",
    "diet_name",
    "species_name",
    "model_species_id",
    "objective_reaction_id",
    "median_abundance",
    "normalized_weight",
    "n_subjects",
    "species_biomass_flux",
    "is_growing",
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
        }
    return metadata


def build_wide_rows(species_rows: list[dict[str, object]], age_groups: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in species_rows:
        key = (str(row["species_name"]), str(row["diet_name"]))
        existing = grouped.get(key)
        if existing is None:
            existing = {
                "species_name": row["species_name"],
                "model_species_id": row["model_species_id"],
                "diet_name": row["diet_name"],
            }
            grouped[key] = existing
        existing[str(row["age_group"])] = row["species_biomass_flux"]

    wide_rows: list[dict[str, object]] = []
    for _, row in sorted(grouped.items()):
        for age_group in age_groups:
            row.setdefault(age_group, "")
        wide_rows.append(row)
    return wide_rows


def build_csv_output_specs(age_groups: list[str]) -> list[dict[str, object]]:
    return [
        csv_output_spec(
            SUMMARY_OUTPUT,
            "one row per age_group x diet_name",
            [
                col("age_group", "Age-bin label for the median-abundance community input."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("solver_status", "COBRApy solver status returned for the age-bin community optimization."),
                col(
                    "community_objective_value",
                    "Objective value returned by the weighted age-bin community optimization.",
                    "community_objective_value = optimized weighted objective reported by community.optimize()",
                ),
                col(
                    "sum_species_biomass_flux",
                    "Sum of biomass fluxes across all modeled species in this age-bin community.",
                    "sum_species_biomass_flux = sum(species_biomass_flux across all species_name within age_group + diet_name)",
                ),
                col(
                    "num_species_with_nonzero_growth",
                    "Count of species whose biomass flux exceeded the growth threshold.",
                    f"num_species_with_nonzero_growth = count(|species_biomass_flux| > {GROWTH_THRESHOLD})",
                ),
                col("community_ex_but_flux", "Flux through the shared butyrate exchange reaction when that exchange exists."),
                col(
                    "matched_diet_metabolites",
                    "Count of diet metabolite IDs that could be mapped into the shared community exchanges.",
                    "matched_diet_metabolites = number of diet metabolite_ids with a shared_exchange_ids match",
                ),
                col(
                    "missing_diet_metabolites",
                    "Count of diet metabolite IDs that could not be mapped into the shared community exchanges.",
                    "missing_diet_metabolites = total diet metabolite_ids - matched_diet_metabolites",
                ),
                col("n_subjects", "Number of subjects contributing to the median-abundance age-bin input."),
                col(
                    "total_input_median_abundance",
                    "Sum of the median abundances supplied for the 10 modeled species in this age bin.",
                    "total_input_median_abundance = sum(median_abundance across all model_species_id within age_group)",
                ),
                col(
                    "total_input_normalized_weight",
                    "Sum of the normalized objective weights used for the age-bin community objective.",
                    "total_input_normalized_weight = sum(normalized_weight across all model_species_id within age_group)",
                ),
            ],
        ),
        csv_output_spec(
            SPECIES_OUTPUT,
            "one row per age_group x diet_name x species_name",
            [
                col("age_group", "Age-bin label for the median-abundance community input."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                col("species_name", "Species label from the processed age-bin input table."),
                col("model_species_id", "Model species identifier used in the community model."),
                col("objective_reaction_id", "Biomass/objective reaction ID used for this species inside the combined model."),
                col("median_abundance", "Median abundance supplied for this species in the selected age bin."),
                col(
                    "normalized_weight",
                    "Normalized weight used in the weighted community objective for this species.",
                    "normalized_weight = median_abundance / sum(median_abundance within age_group)",
                ),
                col("n_subjects", "Number of subjects contributing to the median-abundance value for this age bin."),
                col("species_biomass_flux", "Solved biomass flux for this species under the selected age bin and diet."),
                col(
                    "is_growing",
                    "Boolean flag showing whether the species biomass flux exceeded the growth threshold.",
                    f"is_growing = abs(species_biomass_flux) > {GROWTH_THRESHOLD}",
                ),
            ],
        ),
        csv_output_spec(
            WIDE_OUTPUT,
            "one row per species_name x diet_name",
            [
                col("species_name", "Species label from the processed age-bin input table."),
                col("model_species_id", "Model species identifier used in the community model."),
                col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
                *[
                    col(
                        age_group,
                        f"Solved biomass flux for this species in age group {age_group}; blank means no row was written for that age group.",
                    )
                    for age_group in age_groups
                ],
            ],
        ),
    ]


def main() -> None:
    agebin_rows = load_agebin_table(AGEBIN_INPUT)
    diet_table = load_diet_table(DIET_CSV)

    report_lines = [
        "Age-bin weighted community build report",
        f"Input table: {AGEBIN_INPUT}",
        f"Age bins: {', '.join(sorted(agebin_rows))}",
        "",
        "Input validation",
    ]
    report_lines.extend(validate_agebin_rows(agebin_rows))
    report_lines.append("")

    ordered_age_groups = sorted(agebin_rows)
    reference_rows = agebin_rows[ordered_age_groups[0]]
    model_paths = [Path(row["model_file"]) for row in reference_rows]
    community, species_records, shared_exchange_ids, missing_exchange_metabolites = (
        build_shared_environment_community(model_paths)
    )

    species_ids_in_model = {record["species_name"] for record in species_records}
    expected_species_ids = {row["model_species_id"] for row in reference_rows}
    if species_ids_in_model != expected_species_ids:
        raise ValueError(
            f"Community species mismatch. Model has {sorted(species_ids_in_model)}, input has {sorted(expected_species_ids)}"
        )

    report_lines.append(f"Species count: {len(species_records)}")
    report_lines.append(f"Shared metabolites: {len(shared_exchange_ids)}")
    report_lines.append("")

    for species_name, missing in sorted(missing_exchange_metabolites.items()):
        if missing:
            report_lines.append(
                f"{species_name}: extracellular metabolites without direct single-species exchange -> {', '.join(missing)}"
            )
    report_lines.append("")

    summary_rows: list[dict[str, object]] = []
    species_rows: list[dict[str, object]] = []

    for age_group in ordered_age_groups:
        age_rows = agebin_rows[age_group]
        metadata_by_model_id = build_agebin_metadata(age_rows)
        objective_weights = {
            record["objective_reaction_id"]: metadata_by_model_id[record["species_name"]]["normalized_weight"]
            for record in species_records
        }
        total_input_median_abundance = sum(
            metadata["median_abundance"] for metadata in metadata_by_model_id.values()
        )
        total_input_normalized_weight = sum(
            metadata["normalized_weight"] for metadata in metadata_by_model_id.values()
        )
        n_subjects = next(iter(metadata_by_model_id.values()))["n_subjects"]

        report_lines.append(f"{age_group}:")
        report_lines.append(
            "  objective weights -> "
            + ", ".join(
                f"{record['species_name']}={metadata_by_model_id[record['species_name']]['normalized_weight']:.6f}"
                for record in species_records
            )
        )

        for diet_name, diet_bounds in diet_table.items():
            medium: dict[str, float] = {}
            missing_diet_metabolites: list[str] = []
            for metabolite_id, bound in diet_bounds.items():
                exchange_id = shared_exchange_ids.get(metabolite_id)
                if exchange_id is None:
                    missing_diet_metabolites.append(metabolite_id)
                    continue
                medium[exchange_id] = bound

            with community:
                community.objective = {
                    community.reactions.get_by_id(reaction_id): coefficient
                    for reaction_id, coefficient in objective_weights.items()
                }

                for exchange_id in shared_exchange_ids.values():
                    reaction = community.reactions.get_by_id(exchange_id)
                    reaction.lower_bound = 0.0
                    reaction.upper_bound = 1000.0
                for exchange_id, bound in medium.items():
                    reaction = community.reactions.get_by_id(exchange_id)
                    reaction.lower_bound = -bound
                    reaction.upper_bound = 1000.0

                solution = community.optimize()
                community_ex_but_flux = ""
                if "but" in shared_exchange_ids:
                    community_ex_but_flux = solution.fluxes.get(shared_exchange_ids["but"], 0.0)

                num_species_growing = 0
                total_species_biomass = 0.0
                for record in species_records:
                    biomass_flux = solution.fluxes.get(record["objective_reaction_id"], 0.0)
                    is_growing = abs(biomass_flux) > GROWTH_THRESHOLD
                    if not is_growing:
                        biomass_flux = 0.0
                    metadata = metadata_by_model_id[record["species_name"]]
                    num_species_growing += int(is_growing)
                    total_species_biomass += biomass_flux
                    species_rows.append(
                        {
                            "age_group": age_group,
                            "diet_name": diet_name,
                            "species_name": metadata["species_name"],
                            "model_species_id": record["species_name"],
                            "objective_reaction_id": record["objective_reaction_id"],
                            "median_abundance": metadata["median_abundance"],
                            "normalized_weight": metadata["normalized_weight"],
                            "n_subjects": metadata["n_subjects"],
                            "species_biomass_flux": biomass_flux,
                            "is_growing": is_growing,
                        }
                    )

                summary_rows.append(
                    {
                        "age_group": age_group,
                        "diet_name": diet_name,
                        "solver_status": solution.status,
                        "community_objective_value": solution.objective_value,
                        "sum_species_biomass_flux": total_species_biomass,
                        "num_species_with_nonzero_growth": num_species_growing,
                        "community_ex_but_flux": community_ex_but_flux,
                        "matched_diet_metabolites": len(medium),
                        "missing_diet_metabolites": len(missing_diet_metabolites),
                        "n_subjects": n_subjects,
                        "total_input_median_abundance": total_input_median_abundance,
                        "total_input_normalized_weight": total_input_normalized_weight,
                    }
                )

            report_lines.append(
                f"  {diet_name}: matched diet metabolites={len(medium)}, missing diet metabolites={len(missing_diet_metabolites)}"
            )
            if missing_diet_metabolites:
                report_lines.append(f"  {diet_name} missing metabolite_ids: {', '.join(sorted(missing_diet_metabolites))}")
        report_lines.append("")

    wide_rows = build_wide_rows(species_rows, ordered_age_groups)

    write_csv(
        SUMMARY_OUTPUT,
        SUMMARY_FIELDNAMES,
        summary_rows,
    )
    write_csv(
        SPECIES_OUTPUT,
        SPECIES_FIELDNAMES,
        species_rows,
    )
    write_csv(
        WIDE_OUTPUT,
        ["species_name", "model_species_id", "diet_name", *ordered_age_groups],
        wide_rows,
    )
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, build_csv_output_specs(ordered_age_groups)))

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {SPECIES_OUTPUT}")
    print(f"Wrote {WIDE_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
