from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

# Load the helper module living next to this script.
# We use importlib because the filename starts with `00_`, which is awkward to import
# with the usual `import ...` syntax.
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

# Pull the specific helpers we need from `00_baseline_modeling_utils.py`.
GROWTH_THRESHOLD = UTILS_MODULE.GROWTH_THRESHOLD
build_shared_environment_community = UTILS_MODULE.build_shared_environment_community
load_diet_table = UTILS_MODULE.load_diet_table
load_species_model_paths = UTILS_MODULE.load_species_model_paths
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


MODELS_DIR = Path("Models/vmh_agora2_sbml")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/cobrapy_fba/tables/02_community_growth_summary_by_diet.csv")
SPECIES_OUTPUT = Path("Results/cobrapy_fba/tables/02_community_species_growth_by_diet.csv")
BUILD_REPORT = Path("Results/cobrapy_fba/reports/02_community_model_build_report.txt")
SUMMARY_FIELDNAMES = [
    "diet_name",
    "solver_status",
    "community_objective_value",
    "sum_species_biomass_flux",
    "num_species_with_nonzero_growth",
    "community_ex_but_flux",
    "matched_diet_metabolites",
    "missing_diet_metabolites",
]
SPECIES_FIELDNAMES = [
    "diet_name",
    "species_name",
    "objective_reaction_id",
    "species_biomass_flux",
    "is_growing",
]
CSV_OUTPUT_SPECS = [
    csv_output_spec(
        SUMMARY_OUTPUT,
        "one row per diet_name",
        [
            col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
            col("solver_status", "COBRApy solver status returned for the community optimization."),
            col(
                "community_objective_value",
                "Objective value returned by the community optimization.",
                "community_objective_value = optimized weighted objective reported by community.optimize()",
            ),
            col(
                "sum_species_biomass_flux",
                "Sum of the species biomass fluxes read from the combined solution.",
                "sum_species_biomass_flux = sum(species_biomass_flux across all species_name within diet_name)",
            ),
            col(
                "num_species_with_nonzero_growth",
                "Number of species whose biomass flux exceeded the growth threshold.",
                f"num_species_with_nonzero_growth = count(|species_biomass_flux| > {GROWTH_THRESHOLD})",
            ),
            col(
                "community_ex_but_flux",
                "Flux through the shared butyrate exchange reaction when that exchange exists in the community model.",
            ),
            col(
                "matched_diet_metabolites",
                "Count of diet metabolite IDs that could be mapped to shared-environment exchange reactions.",
                "matched_diet_metabolites = number of diet metabolite_ids with a shared_exchange_ids match",
            ),
            col(
                "missing_diet_metabolites",
                "Count of diet metabolite IDs that could not be mapped into the shared community exchanges.",
                "missing_diet_metabolites = total diet metabolite_ids - matched_diet_metabolites",
            ),
        ],
    ),
    csv_output_spec(
        SPECIES_OUTPUT,
        "one row per diet_name x species_name",
        [
            col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
            col("species_name", "Model species included in the shared-environment community."),
            col("objective_reaction_id", "Biomass/objective reaction ID used for this species inside the combined model."),
            col("species_biomass_flux", "Solved biomass flux for this species under the selected diet."),
            col(
                "is_growing",
                "Boolean flag showing whether the species biomass flux exceeded the growth threshold.",
                f"is_growing = abs(species_biomass_flux) > {GROWTH_THRESHOLD}",
            ),
        ],
    ),
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    # Step 1: find all species models and load the available diet scenarios.
    model_paths = load_species_model_paths(MODELS_DIR)
    diet_table = load_diet_table(DIET_CSV)

    # Step 2: build one combined community model with a shared environment.
    # This helper comes from `00_baseline_modeling_utils.py`.
    community, species_records, shared_exchange_ids, missing_exchange_metabolites = (
        build_shared_environment_community(model_paths)
    )

    summary_rows: list[dict[str, object]] = []
    species_rows: list[dict[str, object]] = []
    # Build a plain-text report explaining how the community model was assembled.
    report_lines = [
        "Community build report",
        f"Species count: {len(species_records)}",
        f"Shared metabolites: {len(shared_exchange_ids)}",
        "",
    ]

    for species_name, missing in sorted(missing_exchange_metabolites.items()):
        if missing:
            report_lines.append(
                f"{species_name}: extracellular metabolites without direct single-species exchange -> {', '.join(missing)}"
            )

    report_lines.append("")

    for diet_name, diet_bounds in diet_table.items():
        # Translate diet metabolite IDs such as `glc_D` into the matching
        # shared-environment exchange reactions in the community model.
        medium: dict[str, float] = {}
        missing_diet_metabolites: list[str] = []
        for metabolite_id, bound in diet_bounds.items():
            exchange_id = shared_exchange_ids.get(metabolite_id)
            if exchange_id is None:
                missing_diet_metabolites.append(metabolite_id)
                continue
            medium[exchange_id] = bound

        with community:
            # Start by closing take-in for every shared metabolite while still
            # leaving secretion broadly open.
            for exchange_id in shared_exchange_ids.values():
                reaction = community.reactions.get_by_id(exchange_id)
                reaction.lower_bound = 0.0
                reaction.upper_bound = 1000.0
            # Re-open take-in only for metabolites present in the selected diet.
            # In exchange reactions, negative lower bounds allow import.
            for exchange_id, bound in medium.items():
                reaction = community.reactions.get_by_id(exchange_id)
                reaction.lower_bound = -bound
                reaction.upper_bound = 1000.0

            # Solve the flux balance analysis problem for the whole community.
            solution = community.optimize()
            community_ex_but_flux = ""
            if "but" in shared_exchange_ids:
                community_ex_but_flux = solution.fluxes.get(shared_exchange_ids["but"], 0.0)

            num_species_growing = 0
            total_species_biomass = 0.0
            for record in species_records:
                # Read the biomass flux for each species from the combined solution.
                biomass_flux = solution.fluxes.get(record["objective_reaction_id"], 0.0)
                is_growing = abs(biomass_flux) > GROWTH_THRESHOLD
                num_species_growing += int(is_growing)
                total_species_biomass += biomass_flux
                species_rows.append(
                    {
                        "diet_name": diet_name,
                        "species_name": record["species_name"],
                        "objective_reaction_id": record["objective_reaction_id"],
                        "species_biomass_flux": biomass_flux,
                        "is_growing": is_growing,
                    }
                )

            # Store one row per diet summarizing overall community behaviour.
            summary_rows.append(
                {
                    "diet_name": diet_name,
                    "solver_status": solution.status,
                    "community_objective_value": solution.objective_value,
                    "sum_species_biomass_flux": total_species_biomass,
                    "num_species_with_nonzero_growth": num_species_growing,
                    "community_ex_but_flux": community_ex_but_flux,
                    "matched_diet_metabolites": len(medium),
                    "missing_diet_metabolites": len(missing_diet_metabolites),
                }
            )

            report_lines.append(
                f"{diet_name}: matched diet metabolites={len(medium)}, missing diet metabolites={len(missing_diet_metabolites)}, solver_status={solution.status}"
            )
            if missing_diet_metabolites:
                report_lines.append(
                    f"{diet_name} missing metabolite_ids: {', '.join(sorted(missing_diet_metabolites))}"
                )
            report_lines.append("")

    # Save the machine-readable outputs and the build report to disk.
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
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, CSV_OUTPUT_SPECS))

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {SPECIES_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
