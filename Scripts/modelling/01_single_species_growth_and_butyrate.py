from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

# Load the shared helper file that sits beside this script.
UTILS_PATH = Path(__file__).with_name("00_baseline_modeling_utils.py")
UTILS_SPEC = importlib.util.spec_from_file_location("baseline_modeling_utils", UTILS_PATH)
if UTILS_SPEC is None or UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load utility module from {UTILS_PATH}")
UTILS_MODULE = importlib.util.module_from_spec(UTILS_SPEC)
UTILS_SPEC.loader.exec_module(UTILS_MODULE)

# Pull in the helpers used in this single-species workflow.
GROWTH_THRESHOLD = UTILS_MODULE.GROWTH_THRESHOLD
build_medium_for_model = UTILS_MODULE.build_medium_for_model
find_butyrate_reactions = UTILS_MODULE.find_butyrate_reactions
get_active_objective_reaction = UTILS_MODULE.get_active_objective_reaction
load_diet_table = UTILS_MODULE.load_diet_table
load_model = UTILS_MODULE.load_model
load_species_model_paths = UTILS_MODULE.load_species_model_paths
species_name_from_path = UTILS_MODULE.species_name_from_path


MODELS_DIR = Path("Models/vmh_agora2_sbml")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/cobrapy_fba/tables/01_single_species_growth_and_butyrate_by_diet.csv")
REACTIONS_OUTPUT = Path("Results/cobrapy_fba/tables/01_single_species_butyrate_reactions_by_diet.csv")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    # Load the diet scenarios and the list of species models to test one by one.
    diet_table = load_diet_table(DIET_CSV)
    model_paths = load_species_model_paths(MODELS_DIR)

    summary_rows: list[dict[str, object]] = []
    reaction_rows: list[dict[str, object]] = []

    for model_path in model_paths:
        # For each species, load the model and identify the biomass objective
        # plus any reactions that look butyrate-related.
        species_name = species_name_from_path(model_path)
        model = load_model(model_path)
        objective_reaction = get_active_objective_reaction(model)
        butyrate_reactions = find_butyrate_reactions(model)
        has_ex_but = "EX_but(e)" in model.reactions

        for diet_name, diet_bounds in diet_table.items():
            with model:
                # Match diet metabolite IDs to this model's exchange reactions and
                # then run standard single-species FBA under that medium.
                medium, missing_metabolites = build_medium_for_model(model, diet_bounds)
                model.medium = medium
                solution = model.optimize()

                ex_but_flux = ""
                if has_ex_but:
                    ex_but_flux = solution.fluxes.get("EX_but(e)", 0.0)

                summary_rows.append(
                    {
                        "species_name": species_name,
                        "diet_name": diet_name,
                        "model_id": model.id,
                        "solver_status": solution.status,
                        "objective_reaction_id": objective_reaction.id,
                        "growth_value": solution.objective_value,
                        "is_growing": solution.objective_value > GROWTH_THRESHOLD,
                        "has_ex_but": has_ex_but,
                        "ex_but_flux": ex_but_flux,
                        "num_butyrate_reactions": len(butyrate_reactions),
                        "matched_diet_metabolites": len(medium),
                        "missing_diet_metabolites": len(missing_metabolites),
                    }
                )

                for reaction in butyrate_reactions:
                    reaction_rows.append(
                        {
                            "species_name": species_name,
                            "diet_name": diet_name,
                            "reaction_id": reaction.id,
                            "reaction_name": reaction.name,
                            "flux_value": solution.fluxes.get(reaction.id, 0.0),
                            "is_active": abs(solution.fluxes.get(reaction.id, 0.0)) > GROWTH_THRESHOLD,
                        }
                    )

    # Save both the growth summary and the per-reaction butyrate screen.
    write_csv(
        SUMMARY_OUTPUT,
        [
            "species_name",
            "diet_name",
            "model_id",
            "solver_status",
            "objective_reaction_id",
            "growth_value",
            "is_growing",
            "has_ex_but",
            "ex_but_flux",
            "num_butyrate_reactions",
            "matched_diet_metabolites",
            "missing_diet_metabolites",
        ],
        summary_rows,
    )
    write_csv(
        REACTIONS_OUTPUT,
        [
            "species_name",
            "diet_name",
            "reaction_id",
            "reaction_name",
            "flux_value",
            "is_active",
        ],
        reaction_rows,
    )

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {REACTIONS_OUTPUT}")


if __name__ == "__main__":
    main()
