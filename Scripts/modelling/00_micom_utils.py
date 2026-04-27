from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_equal_abundance_taxonomy(model_paths: list[Path], species_name_from_path) -> pd.DataFrame:
    # Build the MICOM taxonomy table for an unweighted baseline community.
    if not model_paths:
        raise ValueError("No model paths were found for MICOM community construction.")

    abundance = 1.0 / len(model_paths)
    rows: list[dict[str, object]] = []
    for model_path in model_paths:
        species_id = species_name_from_path(model_path)
        rows.append(
            {
                "id": species_id,
                "species": species_id.replace("_", " "),
                "file": str(model_path),
                "abundance": abundance,
            }
        )
    return pd.DataFrame(rows)


def build_agebin_taxonomy(age_rows: list[dict[str, str]]) -> pd.DataFrame:
    # Build one MICOM taxonomy table from one age group's processed abundance rows.
    rows: list[dict[str, object]] = []
    for row in age_rows:
        rows.append(
            {
                "id": row["model_species_id"],
                "species": row["species_name"],
                "file": row["model_file"],
                "abundance": float(row["normalized_weight"]),
            }
        )
    return pd.DataFrame(rows)


def normalize_exchange_token(token: str) -> str:
    # Normalize MICOM exchange IDs and diet metabolite IDs into a shared form.
    normalized = token
    if normalized.startswith("EX_"):
        normalized = normalized[3:]
    normalized = re.sub(r"\[[^\]]+\]$", "", normalized)
    normalized = re.sub(r"\([^)]+\)$", "", normalized)
    normalized = re.sub(r"_(medium|m)$", "", normalized)
    return normalized


def build_micom_exchange_map(community) -> dict[str, str]:
    # Build a lookup from simplified exchange/metabolite tokens to MICOM exchange IDs.
    exchange_map: dict[str, str] = {}
    for reaction in community.exchanges:
        candidates = {normalize_exchange_token(reaction.id)}
        metabolites = list(reaction.metabolites)
        if len(metabolites) == 1:
            candidates.add(normalize_exchange_token(metabolites[0].id))
        for candidate in candidates:
            if candidate:
                exchange_map.setdefault(candidate, reaction.id)
    return exchange_map


def build_micom_medium(community, diet_bounds: dict[str, float]) -> tuple[dict[str, float], list[str]]:
    # Translate diet metabolite IDs into the actual MICOM community exchange IDs.
    exchange_map = build_micom_exchange_map(community)
    medium: dict[str, float] = {}
    missing_metabolites: list[str] = []

    for metabolite_id, bound in diet_bounds.items():
        exchange_id = exchange_map.get(normalize_exchange_token(metabolite_id))
        if exchange_id is None:
            missing_metabolites.append(metabolite_id)
            continue
        medium[exchange_id] = bound

    return medium, missing_metabolites


def solution_members_table(solution) -> pd.DataFrame:
    # Normalize MICOM's members table so downstream scripts can rely on `taxon_id`.
    members = solution.members.copy()
    members = members.reset_index()
    if "taxon_id" not in members.columns:
        if "id" in members.columns:
            members = members.rename(columns={"id": "taxon_id"})
        elif "compartment" in members.columns:
            members = members.rename(columns={"compartment": "taxon_id"})
        elif "index" in members.columns:
            members = members.rename(columns={"index": "taxon_id"})
        else:
            members = members.rename(columns={members.columns[0]: "taxon_id"})
    if "abundance" in members.columns:
        members = members[members["abundance"].notna()]
    return members


def run_cooperative_tradeoff(
    community,
    diet_bounds: dict[str, float],
    tradeoff_fraction: float,
    *,
    fluxes: bool = False,
    pfba: bool = False,
):
    # Apply the medium, solve the MICOM community, and return normalized member output.
    medium, missing_metabolites = build_micom_medium(community, diet_bounds)
    community.medium = medium
    solution = community.cooperative_tradeoff(fraction=tradeoff_fraction, fluxes=fluxes, pfba=pfba)
    members = solution_members_table(solution)
    return solution, members, medium, missing_metabolites
