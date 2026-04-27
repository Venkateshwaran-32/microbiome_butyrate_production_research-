from __future__ import annotations


import csv
import re
from pathlib import Path

from cobra import Model, Reaction, Metabolite
from cobra.io import read_sbml_model

# this guys below are constants meaning , a variable meant to stay fixed and reused 
GROWTH_THRESHOLD = 1e-9
SHARED_COMPARTMENT_ID = "u"
BUTYRATE_TERMS = ("butyr", "btcoa", "butcoa")


# defining many small functions that can be reused to perform one focussed job 


def load_species_model_paths(models_dir: str | Path) -> list[Path]:
    # Take a folder path and find all SBML XML model files inside it.
    # Input: a directory path as a string or Path object.
    # Output: a sorted list of Path objects, one for each species model file.
    return sorted(Path(models_dir).glob("*.xml"))


# i will just do a sample explanation here 
# def is just defining , the function its trying to introduce its caled "load_diet_table" ,
# the parameter is the diet_csv_path , which is what the input it expects , and the 
# str | Path is a type hint meaning it is telling th reader what kind of value is expected. 
# the | means "or"
# dict[str, dict[str, float]]: this is a return type hint so it is like what ind of value the fn gives back 
# open() is a python built-in function for opening files. 



def load_diet_table(diet_csv_path: str | Path) -> dict[str, dict[str, float]]:
    # Read the diet CSV file and reorganize it into a nested Python dictionary.
    # Input: the path to `diet.csv` as a string or Path object.
    # Output: {diet_name: {metabolite_id: uptake_bound_as_float}} for positive entries only.
    with open(diet_csv_path, newline="") as handle:
        rows = list(csv.DictReader(handle))

    diet_columns = [column for column in rows[0].keys() if column not in {"metabolite_id", "exchange_id", "metabolite_name"}]
    diets: dict[str, dict[str, float]] = {diet_name: {} for diet_name in diet_columns}

    for row in rows:
        metabolite_id = row["metabolite_id"]
        for diet_name in diet_columns:
            value = float(row[diet_name])
            if value > 0:
                diets[diet_name][metabolite_id] = value

    return diets


def base_metabolite_id(metabolite_id: str) -> str:
    # Remove the compartment suffix from a metabolite ID when one is present.
    # Input: a metabolite ID string like `glc_D[e]` or `glc_D`.
    # Output: the base metabolite ID like `glc_D`, which is easier to match across models.
    match = re.match(r"(.+)\[([^\]]+)\]$", metabolite_id)
    return match.group(1) if match else metabolite_id


def get_active_objective_reaction(model: Model) -> Reaction:
    # Find which reaction is currently being optimized in the model objective.
    # Input: one COBRApy Model object.
    # Output: the Reaction object acting as the objective, usually the biomass reaction.
    objective_reactions = [reaction for reaction in model.reactions if abs(reaction.objective_coefficient) > 0]
    if not objective_reactions:
        raise ValueError(f"No active objective reaction found for model {model.id}")
    if len(objective_reactions) > 1:
        positive = [reaction for reaction in objective_reactions if reaction.objective_coefficient > 0]
        if positive:
            return positive[0]
    return objective_reactions[0]


def get_exchange_metabolite(reaction: Reaction) -> Metabolite | None:
    # Get the one metabolite used by a simple exchange reaction, if there is exactly one.
    # Input: one COBRApy Reaction object.
    # Output: a Metabolite object for simple exchanges, or None for more complex reactions.
    if len(reaction.metabolites) != 1:
        return None
    return next(iter(reaction.metabolites))


def build_model_exchange_map(model: Model) -> dict[str, str]:
    # Build a lookup from metabolite base IDs to the model's exchange reaction IDs.
    # Input: one COBRApy Model object.
    # Output: a dictionary like `glc_D -> EX_glc_D(e)` for exchange matching.
    exchange_map: dict[str, str] = {}
    for reaction in model.exchanges:
        metabolite = get_exchange_metabolite(reaction)
        if metabolite is None:
            continue
        exchange_map[base_metabolite_id(metabolite.id)] = reaction.id
    return exchange_map


def build_medium_for_model(model: Model, diet_bounds: dict[str, float]) -> tuple[dict[str, float], list[str]]:
    # Convert a diet definition into the exact medium dictionary this model expects.
    # Input: one Model plus a diet dictionary like `metabolite_id -> bound`.
    # Output: `(medium, missing_metabolites)` where `medium` is ready for `model.medium`.
    exchange_map = build_model_exchange_map(model)
    medium: dict[str, float] = {}
    missing_metabolites: list[str] = []

    for metabolite_id, bound in diet_bounds.items():
        reaction_id = exchange_map.get(metabolite_id)
        if reaction_id is None:
            missing_metabolites.append(metabolite_id)
            continue
        medium[reaction_id] = bound

    return medium, missing_metabolites


def find_butyrate_reactions(model: Model) -> list[Reaction]:
    # Search the model for reactions whose ID, name, or equation text looks butyrate-related.
    # Input: one COBRApy Model object.
    # Output: a list of Reaction objects whose text matches the butyrate search terms.
    matches: list[Reaction] = []
    for reaction in model.reactions:
        searchable = " ".join(part for part in (reaction.id, reaction.name, reaction.reaction) if part).lower()
        if any(term in searchable for term in BUTYRATE_TERMS):
            matches.append(reaction)
    return matches


def species_name_from_path(path: Path) -> str:
    # Take one model file path and extract the filename without its extension.
    # Input: a Path object like `Bacteroides_uniformis.xml`.
    # Output: a species-style name string like `Bacteroides_uniformis`.
    return path.stem


def load_model(path: str | Path) -> Model:
    # Load one SBML model file from disk into a COBRApy Model object.
    # Input: a file path as a string or Path object.
    # Output: one in-memory Model object that later functions can inspect or optimize.
    return read_sbml_model(str(path))


def namespace_species_model(
    model: Model, species_name: str
) -> tuple[Model, Reaction, dict[str, str], list[str]]:
    # Copy one species model and rename its IDs so it can safely coexist with other species.
    # Input: one Model plus the species name that should be attached to its IDs.
    # Output: the renamed model, its objective reaction, extracellular metabolite lookup, and exchange IDs.
    member = model.copy()
    original_compartments = dict(member.compartments)
    compartment_map = {
        compartment_id: f"{species_name}_{compartment_id}" for compartment_id in original_compartments
    }
    extracellular_exchange_ids: list[str] = []
    for reaction in member.exchanges:
        metabolite = get_exchange_metabolite(reaction)
        if metabolite is None:
            continue
        if metabolite.compartment == "e":
            extracellular_exchange_ids.append(reaction.id)

    # Preserve the original IDs in notes so the merged model can still be traced
    # back to the underlying species model.
    for metabolite in member.metabolites:
        original_id = metabolite.id
        original_compartment = metabolite.compartment
        metabolite.notes = dict(metabolite.notes)
        metabolite.notes["community_original_id"] = original_id
        metabolite.notes["community_original_compartment"] = original_compartment
        metabolite.notes["community_species_name"] = species_name
        metabolite.id = f"{species_name}__{original_id}"
        metabolite.compartment = compartment_map.get(original_compartment, f"{species_name}_{original_compartment}")

    for gene in member.genes:
        gene.id = f"{species_name}__{gene.id}"

    for reaction in member.reactions:
        original_id = reaction.id
        reaction.notes = dict(reaction.notes)
        reaction.notes["community_original_id"] = original_id
        reaction.notes["community_species_name"] = species_name
        reaction.id = f"{species_name}__{original_id}"

    member.compartments = {
        compartment_map[compartment_id]: f"{species_name} {name}"
        for compartment_id, name in original_compartments.items()
    }
    member.id = f"community_member__{species_name}"

    objective_reaction = get_active_objective_reaction(member)
    extracellular_metabolites: dict[str, str] = {}
    # Build a lookup from base metabolite ID to the namespaced extracellular metabolite.
    for metabolite in member.metabolites:
        if metabolite.notes.get("community_original_compartment") != "e":
            continue
        extracellular_metabolites[base_metabolite_id(metabolite.notes["community_original_id"])] = metabolite.id

    namespaced_exchange_ids = [f"{species_name}__{reaction_id}" for reaction_id in extracellular_exchange_ids]
    return member, objective_reaction, extracellular_metabolites, namespaced_exchange_ids


def build_shared_environment_community(
    model_paths: list[Path],
) -> tuple[Model, list[dict[str, str]], dict[str, str], dict[str, list[str]]]:
    # Build one shared-environment community model from many species model files.
    # Input: a list of species SBML file paths.
    # Output: the merged community model plus metadata about species, exchanges, and missing mappings.
    community = Model("baseline_shared_environment_community")
    community.compartments[SHARED_COMPARTMENT_ID] = "Shared community environment"

    species_records: list[dict[str, str]] = []
    shared_metabolites: dict[str, Metabolite] = {}
    shared_exchange_ids: dict[str, str] = {}
    missing_exchange_metabolites: dict[str, list[str]] = {}

    for model_path in model_paths:
        # Load one species and namespace all of its IDs before merging it in.
        species_name = species_name_from_path(model_path)
        member = load_model(model_path)
        namespaced_member, biomass_reaction, extracellular_metabolites, member_exchange_ids = namespace_species_model(
            member, species_name
        )

        community.compartments.update(namespaced_member.compartments)
        community.add_reactions(namespaced_member.reactions)
        # Close each species' own exchange reactions so the species has to use
        # the shared community pool instead of a private external environment.
        for reaction_id in member_exchange_ids:
            community.reactions.get_by_id(reaction_id).bounds = (0.0, 0.0)

        species_records.append(
            {
                "species_name": species_name,
                "model_id": namespaced_member.id,
                "objective_reaction_id": biomass_reaction.id,
            }
        )

        for base_id, species_metabolite in sorted(extracellular_metabolites.items()):
            shared_metabolite = shared_metabolites.get(base_id)
            if shared_metabolite is None:
                # Create the shared version of this extracellular metabolite once.
                shared_metabolite_id = f"community__{base_id}[{SHARED_COMPARTMENT_ID}]"
                community.add_metabolites(
                    [
                        Metabolite(
                            id=shared_metabolite_id,
                            name=f"{base_id} [community]",
                            compartment=SHARED_COMPARTMENT_ID,
                        )
                    ]
                )
                shared_metabolite = community.metabolites.get_by_id(shared_metabolite_id)
                shared_metabolites[base_id] = shared_metabolite

                # This exchange reaction is where the whole community takes in
                # nutrients from the diet or secretes them back out.
                exchange_reaction = Reaction(f"EX_{base_id}({SHARED_COMPARTMENT_ID})")
                exchange_reaction.name = f"{base_id} community exchange"
                exchange_reaction.bounds = (-1000.0, 1000.0)
                exchange_reaction.add_metabolites({shared_metabolite: -1.0})
                community.add_reactions([exchange_reaction])
                shared_exchange_ids[base_id] = exchange_reaction.id

            species_metabolite_ref = community.metabolites.get_by_id(species_metabolite)
            # Connector reactions move metabolites between a species-specific
            # extracellular space and the shared community environment.
            connector = Reaction(f"connector__{species_name}__{base_id}")
            connector.name = f"{species_name} connector for {base_id}"
            connector.bounds = (-1000.0, 1000.0)
            connector.add_metabolites({species_metabolite_ref: -1.0, shared_metabolite: 1.0})
            community.add_reactions([connector])

        species_exchange_map = build_model_exchange_map(member)
        missing_exchange_metabolites[species_name] = sorted(
            base_id for base_id in extracellular_metabolites if base_id not in species_exchange_map
        )

    # Maximize the sum of all species biomass reactions as the community objective.
    biomass_reactions = [
        community.reactions.get_by_id(record["objective_reaction_id"]) for record in species_records
    ]
    community.objective = {reaction: 1.0 for reaction in biomass_reactions}

    return community, species_records, shared_exchange_ids, missing_exchange_metabolites
