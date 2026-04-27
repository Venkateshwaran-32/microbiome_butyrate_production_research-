# Learn Community Modelling Script

If your goal is to write community-modelling scripts yourself, the best path is:

1. Learn basic COBRApy first.
2. Learn how SBML models are structured.
3. Then learn either a community framework or how to build a simple shared-environment model manually.

For this repository, the most useful reading order is:

1. [`../Scripts/modelling/00_baseline_modeling_utils.py`](../Scripts/modelling/00_baseline_modeling_utils.py)
2. [`../Scripts/modelling/01_single_species_growth_and_butyrate.py`](../Scripts/modelling/01_single_species_growth_and_butyrate.py)
3. [`../Scripts/modelling/02_community_shared_environment.py`](../Scripts/modelling/02_community_shared_environment.py)
4. [`../README.md`](../README.md)

## What To Learn First

- Python basics for scripting: `pathlib`, loops, dictionaries, CSV handling
- COBRApy basics: loading a model, inspecting reactions and metabolites, setting media, running `model.optimize()`
- Exchange reactions and media constraints
- Objective functions and growth reactions
- Community model design:
  species namespacing, a shared extracellular compartment, connector reactions, and a summed biomass objective
- Interpretation limits of community FBA, especially sparse or winner-take-all solutions

## Best Learning Order

Do not start by writing a full community script immediately.

Instead, build up in stages:

1. Write a script that loads one SBML model.
2. Apply a medium and print the growth result.
3. Inspect exchange reactions.
4. Add butyrate-related reaction checks if needed.
5. Build a 2-species shared-environment model.
6. Scale that design to more species.

## Best Primary Resources

- COBRApy getting started:
  https://cobrapy.readthedocs.io/en/0.25.0/getting_started.html
- COBRApy documentation:
  https://cobrapy.readthedocs.io/en/0.25.0/
- COBRApy FBA and simulation docs:
  https://cobrapy.readthedocs.io/en/0.24.0/simulating.html
- MICOM documentation:
  https://micom-dev.github.io/micom/
- MICOM community modelling page:
  https://micom-dev.github.io/micom/community.html
- MICOM logic and assumptions:
  https://micom-dev.github.io/micom/logic.html
- SBML background reference:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6167037/

## How This Repo Fits

In this project:

- `00_baseline_modeling_utils.py` is the shared toolbox
- `01_single_species_growth_and_butyrate.py` is the easier script to learn first
- `02_community_shared_environment.py` is the actual baseline community-modelling script

## Diet Uptake Bounds Used In The Community Model

The community model reads its diet bounds from:

- [`../Medium_files/diet.csv`](../Medium_files/diet.csv)

The diet file has these columns:

- `metabolite_id`
- `exchange_id`
- `metabolite_name`
- `western`
- `high_fiber`

In the community script, the values from the selected diet column are used as uptake limits.

The key implementation is in:

- [`../Scripts/modelling/02_community_shared_environment.py`](../Scripts/modelling/02_community_shared_environment.py)

The logic is:

1. Start with every shared community exchange closed for uptake:
   `lower_bound = 0.0`
2. For each metabolite present in the selected diet, open uptake using:
   `lower_bound = -bound`
3. Keep secretion open using:
   `upper_bound = 1000.0`

This means a CSV value such as `0.14898579` becomes an uptake bound of `-0.14898579` in the model.

Examples from `diet.csv`:

- `glc_D`:
  western = `0.14898579`, high_fiber = `0.03947368`
- `inulin`:
  western = `0.00047019`, high_fiber = `0.01041667`
- `glyc`:
  western = `1.79965486`, high_fiber = `0.89982743`
- `ala_L`:
  western = `1.0`, high_fiber = `1.0`

So if the selected diet is `western`:

- glucose uptake is set to `-0.14898579`
- inulin uptake is set to `-0.00047019`
- glycerol uptake is set to `-1.79965486`

If the selected diet is `high_fiber`:

- glucose uptake is set to `-0.03947368`
- inulin uptake is set to `-0.01041667`
- glycerol uptake is set to `-0.89982743`

Important detail:

- only metabolites that can be matched to a shared community exchange are actually applied
- unmatched diet metabolites are counted and written into the build report

So the right way to learn from this repo is:

1. Understand how one model is loaded and simulated.
2. Understand how diet metabolites are matched to exchange reactions.
3. Understand how species are renamed to avoid ID collisions in one combined model.
4. Understand how the shared environment and connector reactions are created.
5. Understand how the summed biomass objective is optimized.

## Practical Goal

If you can write these three things yourself, you are already on the right track:

1. A script that loads one SBML model and runs FBA.
2. A script that applies a diet medium from a CSV file.
3. A script that combines two species into a shared-environment community model.
