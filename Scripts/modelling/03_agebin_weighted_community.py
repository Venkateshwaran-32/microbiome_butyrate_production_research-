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

GROWTH_THRESHOLD = UTILS_MODULE.GROWTH_THRESHOLD
build_shared_environment_community = UTILS_MODULE.build_shared_environment_community
load_diet_table = UTILS_MODULE.load_diet_table


AGEBIN_INPUT = Path("Suplementary_Data/processed_data/allcohort_agebin_median_abundance_10_species.csv")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_growth_summary_by_diet.csv")
SPECIES_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv")
WIDE_OUTPUT = Path("Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet_wide.csv")
BUILD_REPORT = Path("Results/cobrapy_fba/reports/03_agebin_community_model_build_report.txt")
EXPECTED_SPECIES_PER_AGE_BIN = 10


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
        [
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
        ],
        summary_rows,
    )
    write_csv(
        SPECIES_OUTPUT,
        [
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
        ],
        species_rows,
    )
    write_csv(
        WIDE_OUTPUT,
        ["species_name", "model_species_id", "diet_name", *ordered_age_groups],
        wide_rows,
    )
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text("\n".join(report_lines) + "\n")

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {SPECIES_OUTPUT}")
    print(f"Wrote {WIDE_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
