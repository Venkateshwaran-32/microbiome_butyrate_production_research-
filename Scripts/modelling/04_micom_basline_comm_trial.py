# %%
from __future__ import annotations

import importlib.util
from pathlib import Path


# %%
# STEP 0: Find the project folders.
#
# In a normal Python script, __file__ exists.
# In a notebook / VS Code interactive cell, __file__ may not exist, so we fall
# back to the current working directory.
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent
except NameError:
    current_dir = Path.cwd().resolve()
    if current_dir.name == "modelling" and current_dir.parent.name == "Scripts":
        SCRIPT_DIR = current_dir
        PROJECT_ROOT = current_dir.parent.parent
    elif (current_dir / "Scripts" / "modelling").exists():
        PROJECT_ROOT = current_dir
        SCRIPT_DIR = current_dir / "Scripts" / "modelling"
    else:
        raise FileNotFoundError(
            "Run this from the project root or from the Scripts/modelling folder."
        )

print("PROJECT_ROOT:", PROJECT_ROOT)
print("SCRIPT_DIR:", SCRIPT_DIR)


# %%
# STEP 1: Load helper modules.
#
# These helper files start with numbers:
#   00_baseline_modeling_utils.py
#   00_micom_utils.py
#
# Python cannot import those with normal syntax, so we load them by file path.
def load_helper_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline_utils = load_helper_module(
    "baseline_modeling_utils",
    SCRIPT_DIR / "00_baseline_modeling_utils.py",
)
micom_utils = load_helper_module(
    "micom_utils",
    SCRIPT_DIR / "00_micom_utils.py",
)

GROWTH_THRESHOLD = baseline_utils.GROWTH_THRESHOLD
load_diet_table = baseline_utils.load_diet_table
load_species_model_paths = baseline_utils.load_species_model_paths
species_name_from_path = baseline_utils.species_name_from_path

build_equal_abundance_taxonomy = micom_utils.build_equal_abundance_taxonomy
run_cooperative_tradeoff = micom_utils.run_cooperative_tradeoff
write_csv = micom_utils.write_csv

print("Loaded helper functions.")


# %%
# STEP 2: Define the input and output files.
#
# The real baseline script writes to 04_micom_*.csv.
# This trial script writes to 04_micom_trial_*.csv so it does not overwrite
# your real baseline results while you are learning.
MODELS_DIR = PROJECT_ROOT / "Models" / "vmh_agora2_sbml"
DIET_CSV = PROJECT_ROOT / "Medium_files" / "diet.csv"

SUMMARY_OUTPUT = PROJECT_ROOT / "Results" / "micom_fba" / "tables" / "04_micom_trial_community_growth_summary_by_diet.csv"
TAXON_OUTPUT = PROJECT_ROOT / "Results" / "micom_fba" / "tables" / "04_micom_trial_taxon_growth_by_diet.csv"
BUILD_REPORT = PROJECT_ROOT / "Results" / "micom_fba" / "reports" / "04_micom_trial_model_build_report.txt"

COMMUNITY_ID = "micom_baseline_trial"
TRADEOFF_FRACTION = 0.5

print("MODELS_DIR exists:", MODELS_DIR.exists(), MODELS_DIR)
print("DIET_CSV exists:", DIET_CSV.exists(), DIET_CSV)


# %%
# STEP 3: Find the species model files.
#
# This returns a list of Path objects, one for each SBML XML model.
model_paths = load_species_model_paths(MODELS_DIR)

if not MODELS_DIR.exists():
    raise FileNotFoundError(f"Model directory does not exist: {MODELS_DIR}")
if not model_paths:
    raise FileNotFoundError(f"No .xml SBML models found in: {MODELS_DIR}")

print("Number of model files:", len(model_paths))
print("First three model files:")
for path in model_paths[:3]:
    print(" ", path.name)


# %%
# STEP 4: Load the diet table.
#
# load_diet_table returns a nested dictionary:
#   {
#       "western": {"metabolite_id": uptake_bound, ...},
#       "high_fiber": {"metabolite_id": uptake_bound, ...},
#   }
diet_table = load_diet_table(DIET_CSV)

print("Diet names:", list(diet_table))
for diet_name, diet_bounds in diet_table.items():
    print(diet_name, "has", len(diet_bounds), "positive uptake metabolites")


# %%
# STEP 5: Build the MICOM taxonomy table.
#
# MICOM needs a table with one row per organism.
# Important columns:
#   id        = model/taxon ID used by MICOM
#   species   = readable species name
#   file      = path to the SBML model file
#   abundance = relative abundance in the community
taxonomy = build_equal_abundance_taxonomy(model_paths, species_name_from_path)

print(taxonomy.head())
print("Taxonomy columns:", list(taxonomy.columns))
print("Total abundance:", taxonomy["abundance"].sum())


# %%
# STEP 6: Build the MICOM community.
#
# This is the slow part because MICOM reads all SBML models and merges them
# into one community object.
try:
    from micom import Community
except ImportError as exc:
    raise ImportError(
        "MICOM is not installed in this Python environment. Use `.venv_micom`, "
        "for example: .venv_micom/bin/python Scripts/modelling/04_micom_basline_comm_trial.py"
    ) from exc


community = Community(
    taxonomy=taxonomy,
    model_db=None,
    id=COMMUNITY_ID,
    name=COMMUNITY_ID,
    progress=True,
)

print("Built community:", community.id)
print("Number of taxa:", len(taxonomy))
print("Number of community exchange reactions:", len(community.exchanges))


# %%
# STEP 7: Run one diet first.
#
# The real script loops over every diet. For learning, start with one diet so
# you can inspect the solution before creating output tables.
diet_name = list(diet_table)[0]
diet_bounds = diet_table[diet_name]

solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
    community,
    diet_bounds,
    TRADEOFF_FRACTION,
)

print("Diet:", diet_name)
print("Solver status:", solution.status)
print("Community growth rate:", solution.growth_rate)
print("Matched diet metabolites:", len(medium))
print("Missing diet metabolites:", len(missing_metabolites))
print(members.head())


# %%
# STEP 8: Convert the one-diet MICOM result into rows.
#
# This is the same pattern used inside the loop in the real baseline script.
one_diet_summary_row = {
    "diet_name": diet_name,
    "solver_status": solution.status,
    "community_growth_rate": solution.growth_rate,
    "objective_value": solution.objective_value,
    "tradeoff_fraction": TRADEOFF_FRACTION,
    "num_taxa_total": len(members),
    "num_taxa_with_nonzero_growth": int(
        sum(float(row.growth_rate) > GROWTH_THRESHOLD for row in members.itertuples(index=False))
    ),
    "matched_diet_metabolites": len(medium),
    "missing_diet_metabolites": len(missing_metabolites),
}

one_diet_taxon_rows: list[dict[str, object]] = []
for row in members.itertuples(index=False):
    growth_rate = float(getattr(row, "growth_rate", 0.0))
    one_diet_taxon_rows.append(
        {
            "diet_name": diet_name,
            "taxon_id": row.taxon_id,
            "abundance": getattr(row, "abundance", ""),
            "growth_rate": growth_rate,
            "is_growing": growth_rate > GROWTH_THRESHOLD,
            "reactions": getattr(row, "reactions", ""),
            "metabolites": getattr(row, "metabolites", ""),
        }
    )

print(one_diet_summary_row)
print("First taxon row:")
print(one_diet_taxon_rows[0])


# %%
# STEP 9: Optional full loop over all diets.
#
# Set this to True when you are ready to reproduce the full structure of
# 04_micom_baseline_community.py.
RUN_FULL_DIET_LOOP = False

if RUN_FULL_DIET_LOOP:
    report_lines = [
        "MICOM baseline trial community build report",
        f"Community ID: {COMMUNITY_ID}",
        f"Model count: {len(model_paths)}",
        f"Diet file: {DIET_CSV}",
        f"Tradeoff fraction: {TRADEOFF_FRACTION}",
        "",
        "Taxonomy table",
    ]
    report_lines.extend(
        f"{row.id}: abundance={row.abundance:.6f}, file={row.file}"
        for row in taxonomy.itertuples(index=False)
    )
    report_lines.append("")
    report_lines.append("Diet mapping and solve summary")

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []

    for diet_name, diet_bounds in diet_table.items():
        solution, members, medium, missing_metabolites = run_cooperative_tradeoff(
            community,
            diet_bounds,
            TRADEOFF_FRACTION,
        )

        num_taxa_growing = 0
        for row in members.itertuples(index=False):
            growth_rate = float(getattr(row, "growth_rate", 0.0))
            is_growing = growth_rate > GROWTH_THRESHOLD
            num_taxa_growing += int(is_growing)
            taxon_rows.append(
                {
                    "diet_name": diet_name,
                    "taxon_id": row.taxon_id,
                    "abundance": getattr(row, "abundance", ""),
                    "growth_rate": growth_rate,
                    "is_growing": is_growing,
                    "reactions": getattr(row, "reactions", ""),
                    "metabolites": getattr(row, "metabolites", ""),
                }
            )

        summary_rows.append(
            {
                "diet_name": diet_name,
                "solver_status": solution.status,
                "community_growth_rate": solution.growth_rate,
                "objective_value": solution.objective_value,
                "tradeoff_fraction": TRADEOFF_FRACTION,
                "num_taxa_total": len(members),
                "num_taxa_with_nonzero_growth": num_taxa_growing,
                "matched_diet_metabolites": len(medium),
                "missing_diet_metabolites": len(missing_metabolites),
            }
        )

        report_lines.append(
            f"{diet_name}: solver_status={solution.status}, "
            f"community_growth_rate={solution.growth_rate}, "
            f"matched_diet_metabolites={len(medium)}, "
            f"missing_diet_metabolites={len(missing_metabolites)}"
        )
        if missing_metabolites:
            report_lines.append(
                f"{diet_name} missing metabolite_ids: {', '.join(sorted(missing_metabolites))}"
            )
        report_lines.append("")

    write_csv(
        SUMMARY_OUTPUT,
        [
            "diet_name",
            "solver_status",
            "community_growth_rate",
            "objective_value",
            "tradeoff_fraction",
            "num_taxa_total",
            "num_taxa_with_nonzero_growth",
            "matched_diet_metabolites",
            "missing_diet_metabolites",
        ],
        summary_rows,
    )
    write_csv(
        TAXON_OUTPUT,
        [
            "diet_name",
            "taxon_id",
            "abundance",
            "growth_rate",
            "is_growing",
            "reactions",
            "metabolites",
        ],
        taxon_rows,
    )
    BUILD_REPORT.write_text("\n".join(report_lines) + "\n")

    print("Wrote:", SUMMARY_OUTPUT)
    print("Wrote:", TAXON_OUTPUT)
    print("Wrote:", BUILD_REPORT)
else:
    print("Full diet loop skipped. Set RUN_FULL_DIET_LOOP = True when ready.")
