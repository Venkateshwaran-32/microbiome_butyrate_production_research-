# Community Modelling Script: Detailed Explanation

## What This Document Is For

This note explains how the community-modelling workflow in this repository works, why the script is written the way it is, and what each major design choice means biologically and computationally.

The main scripts involved are:

- [`../Scripts/modelling/00_baseline_modeling_utils.py`](../Scripts/modelling/00_baseline_modeling_utils.py)
- [`../Scripts/modelling/02_community_shared_environment.py`](../Scripts/modelling/02_community_shared_environment.py)
- [`../Medium_files/diet.csv`](../Medium_files/diet.csv)

## Big Picture

The purpose of the community model is to simulate multiple microbial species together in one shared environment and ask questions like:

- which species can grow in the same environment
- which species dominate growth
- whether species may produce or release metabolites such as butyrate-related compounds
- how growth changes under different diet scenarios

This is different from single-species modelling because each species is no longer simulated alone. Instead, they are forced to share nutrient availability and can potentially interact through secreted metabolites.

## Why A Community Model Is Needed

If you run each species alone, each species gets its own isolated environment. That is useful for checking whether a model can grow at all, but it does not capture competition or cross-feeding.

In a community model:

- species compete for the same available nutrients
- one species may release metabolites that another species can take in
- the optimizer decides how flux is distributed across the combined system

So a community model is the right tool when you want to ask how species behave together rather than individually.

## Why COBRApy Is Used

COBRApy is the Python package used to:

- read SBML metabolic models
- access reactions, metabolites, and exchange reactions
- set environmental constraints
- optimize the model using flux balance analysis

It is used here because the project is based on SBML genome-scale metabolic models and standard FBA workflows.

## What SBML Models Provide

Each XML model in `Models/vmh_agora2_sbml/` contains:

- metabolites
- reactions
- compartments
- exchange reactions
- a biomass or growth objective

The script does not invent metabolism from scratch. It starts from these existing species metabolic reconstructions and then combines them into one larger model.

## The Main Script Structure

The main community simulation is run in:

- [`../Scripts/modelling/02_community_shared_environment.py`](../Scripts/modelling/02_community_shared_environment.py)

The actual community-building machinery is placed in:

- [`../Scripts/modelling/00_baseline_modeling_utils.py`](../Scripts/modelling/00_baseline_modeling_utils.py)

This split is deliberate.

`00_baseline_modeling_utils.py` contains reusable helper functions.  
`02_community_shared_environment.py` contains the workflow that uses those helpers to run the analysis.

That is a good design because it keeps the reusable logic separate from the experiment-specific script.

## Why The Main Workflow Is Inside `main()`

The `def main()` function in script `02` is where the actual community analysis is performed.

This is standard Python script structure because it:

- keeps the workflow readable
- makes it obvious where execution starts
- allows helper functions to stay outside the execution flow
- makes later reuse easier

Inside `main()`, the script:

1. loads model paths
2. loads diet information
3. builds the community model
4. applies diet take-in constraints
5. optimizes the community
6. records growth outputs
7. writes result files

## Step 1: Loading The Species Models

The script gets all SBML files from the AGORA2 models folder.

This is done so every selected species model can become one member of the community.

Why this matters:

- each species begins as an independent metabolic network
- the community model is built by combining these species networks

## Step 2: Loading The Diet Table

The diet file is:

- [`../Medium_files/diet.csv`](../Medium_files/diet.csv)

It contains named diet scenarios such as:

- `western`
- `high_fiber`

For each metabolite, the file gives a numeric value for each diet.

These values are not best thought of as literal stored amounts in a pool.  
They are best interpreted as maximum allowed take-in fluxes from the environment.

That means:

- larger value -> more of that nutrient can be taken in
- smaller value -> less of that nutrient can be taken in
- zero value -> no take-in allowed

## What “Take In” Means Here

In this project, it is clearer to say “take in” rather than “uptake.”

When the script says a species or community can take in glucose, it means glucose is allowed to flow from the environment into the modeled system through an exchange reaction.

Important distinction:

- a bound is not the amount already present
- a bound is the maximum allowed flux through a reaction

So if the diet value for glucose is `0.14898579`, that means the model is allowed to take in glucose at up to `0.14898579` flux units.

It does not mean the model must use all of that glucose.

## Why Bounds Use Negative And Positive Values

In COBRA exchange reactions:

- negative flux usually means take in from the environment
- positive flux usually means secrete or release to the environment

So when the script sets:

- `lower_bound = -bound`

it is opening the take-in direction up to that maximum rate.

When the script sets:

- `upper_bound = 1000.0`

it is leaving secretion broadly open.

The number `1000` is not a biological measurement here.  
It is a large technical bound used to mean “this direction is effectively unconstrained for this model.”

## Why The Community Exchange Starts Closed For Take In

In script `02`, every shared exchange is first set to:

- `lower_bound = 0.0`
- `upper_bound = 1000.0`

This means:

- take in is initially not allowed
- secretion is allowed

Then only metabolites present in the selected diet are reopened for take in by changing the lower bound to a negative value.

This is a clean way to enforce diet constraints because:

- all possible secretions are left available
- only diet-permitted nutrients can be taken in

## Why Secretion Is Left Open

Microbial metabolism often produces byproducts.

A species may take in glucose and release:

- acetate
- lactate
- butyrate-related compounds
- carbon dioxide
- other overflow or waste metabolites

If secretion were blocked, the model could become artificially restrictive and many realistic metabolic states would be impossible.

Leaving secretion open is important because:

- microbes often need to release metabolites for metabolic balance
- secreted compounds can be used by other species
- cross-feeding is a central reason to build a community model

## Competition And Sharing In This Model

The diet bounds apply at the community exchange level.

This means the diet value is a limit for the whole community, not automatically for each species individually.

So if glucose has diet value `0.14898579`, then the whole community can take in at most that much glucose flux from the shared environment.

What happens next is determined by optimization:

- one species may use most of it
- several species may split it
- none may use it if it does not help the objective

That is why community modelling can show competition.

## Why Species Need To Be Renamed

When multiple species models are merged, many of them may contain the same IDs for:

- metabolites
- reactions
- genes
- compartments

If these are combined directly, the IDs would collide and the merged model would become ambiguous or broken.

So the script namespaces each species by adding the species name to IDs.

Why this is necessary:

- it preserves each species as a distinct network
- it avoids accidental ID collisions
- it allows multiple species to coexist in one model without overwriting each other

## Why A Shared Environment Is Created

Each species already has its own extracellular metabolites in its original model.  
However, those extracellular spaces are still species-specific.

To allow real community interaction, the script creates a new shared community compartment.

This shared compartment acts like a common environment where:

- all species can potentially access the same nutrient pool
- metabolites secreted by one species can become available to others

Without this shared pool, the models would still be effectively isolated.

## Why Connector Reactions Are Needed

The script does not directly merge all extracellular metabolites into one object.  
Instead, it creates connector reactions between:

- each species extracellular metabolite
- the shared community metabolite

This is a careful modeling choice because it:

- keeps each species network structurally intact
- makes the transfer to the shared pool explicit
- gives a clean place to inspect or control exchange between a species and the community environment

Connector reactions are what allow a species to:

- take in from the shared environment
- release into the shared environment

## Why The Objective Is The Sum Of Biomass Reactions

After all species are merged, the script sets the community objective as the sum of the species biomass reactions.

This means the optimizer tries to maximize total community growth.

Why use this:

- it gives a simple baseline community objective
- it allows comparison of which species end up growing under the same conditions
- it is straightforward to implement and interpret as a first-pass community model

But this choice also matters:

- linear optimization can produce sparse solutions
- some species may get zero growth even if they could grow alone
- a species winning the optimization does not automatically mean it is biologically dominant in vivo

This is why interpretation must stay cautious.

## Why Some Species May Not Grow In Community FBA

A species failing to grow in the community result does not automatically mean its SBML model is bad.

Possible reasons include:

- competition for limited nutrients
- the summed biomass objective favoring a subset of species
- alternative optima
- community constraints that differ from single-species growth

This is exactly why script `01` and script `02` complement each other:

- `01` asks whether a species can grow alone
- `02` asks whether it grows when placed in the shared community optimization problem

## Why Butyrate Is Checked Separately

The project is careful not to treat butyrate production as a single yes/no label.

Instead, the workflow separates:

- growth
- butyrate-related internal reaction activity
- exchange with the shared environment

This is a better design because a species may:

- grow without producing butyrate
- contain butyrate-related reactions without carrying flux
- secrete a related metabolite only under certain conditions

So butyrate interpretation should be layered on top of the growth analysis, not collapsed into one label.

## What The Community Script Actually Does During Simulation

At a high level, script `02` does this:

1. Build the community model from all species.
2. Build a map from diet metabolites to community exchange reactions.
3. For one diet at a time, allow take in only for the metabolites present in that diet.
4. Leave secretion broadly open.
5. Optimize the full community model.
6. Read each species biomass flux from the solution.
7. Write summary tables and a build report.

This is the core community-modelling workflow in the repository.

## What The `1000` Bound Means

The `1000` bound is used as a practical large limit.

It should be interpreted as:

- “open enough that this direction is not the main limiting factor”

It should not be interpreted as:

- an actual measured concentration
- a known biological secretion rate
- proof that species are secreting that much

The actual flux used may be far smaller than `1000`, or even zero.

## What The Diet Values Mean In Practice

For a metabolite like glucose:

- if `western` gives `0.14898579`
- then the community can take in glucose at up to `0.14898579` flux units

For secretion:

- the script allows release up to `1000.0`

So in plain words:

- take in is limited by the diet
- shit out is left broadly open

That does not mean the model must take in or secrete those values.  
It only means those are the allowed limits.

## Why This Design Is Good For Learning

This repository uses a relatively understandable community design:

- explicit shared environment
- explicit connector reactions
- explicit diet constraints
- explicit summed biomass objective

That makes it a good learning model because you can see each concept directly in code rather than hiding everything behind a high-level framework.

## How To Learn To Write This Yourself

The best learning path is:

1. Learn Python scripting basics.
2. Learn how to load one SBML model in COBRApy.
3. Learn how to inspect exchange reactions and set medium constraints.
4. Learn how to run `model.optimize()`.
5. Learn how to build a tiny 2-species community.
6. Then scale to a larger shared-environment model.

The best order for this repository is:

1. [`../Scripts/modelling/01_single_species_growth_and_butyrate.py`](../Scripts/modelling/01_single_species_growth_and_butyrate.py)
2. [`../Scripts/modelling/00_baseline_modeling_utils.py`](../Scripts/modelling/00_baseline_modeling_utils.py)
3. [`../Scripts/modelling/02_community_shared_environment.py`](../Scripts/modelling/02_community_shared_environment.py)

Why this order:

- script `01` teaches one species first
- script `00` teaches the reusable building blocks
- script `02` shows the full community workflow

## Final Summary

This community model works by:

- loading multiple species models
- renaming them so they can coexist in one combined model
- creating a shared extracellular environment
- connecting each species to that shared environment
- allowing take in according to diet constraints
- leaving secretion broadly open
- maximizing the sum of species biomass reactions

Biologically, this lets you study competition and possible cross-feeding.  
Computationally, it is a clear baseline shared-environment FBA community model.

If you want to learn to write this yourself, the most important concepts are:

- exchange reactions
- reaction bounds
- biomass objective
- shared environment design
- connector reactions
- cautious interpretation of community FBA results
