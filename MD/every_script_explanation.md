# Every Script Explanation

## What This Note Is For

This note is meant to teach you how to read the main data-processing and modelling scripts in this repository in the right order:

1. [01_prepare_supplementary_agebin_inputs.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py:1)
2. [01_single_species_growth_and_butyrate.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:39)
3. [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:16)
4. [02_community_shared_environment.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:38)
5. [03_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/03_agebin_weighted_community.py:1)

The goal is not just to say what each script does.  
The goal is to help you understand:

- what COBRApy functions and objects are being used
- why they are being used
- what role each script plays in the full workflow
- how the code maps to the biology and modelling logic

## The Big Picture First

These scripts form one workflow:

- `Scripts/data_processing/01` asks: how do the supplementary spreadsheets become model-ready age-bin abundance inputs for the 10 AGORA2 species?
- `01` asks: can each species grow by itself under each diet, and does it show butyrate-related signals?
- `00` contains the shared helper functions that make the workflow reusable
- `02` asks: what happens when all species are placed together in one shared environment?
- `03` asks: how does community growth change when each age bin uses its own abundance-weighted objective?

So:

- `Scripts/data_processing/01` = prepares the abundance inputs
- `01` = easiest place to learn the COBRApy basics
- `00` = toolbox that explains the mechanics
- `02` = full community modelling script
- `03` = age-bin-weighted version of the community analysis

That is why reading them in the order `data processing -> 01 -> 00 -> 02 -> 03` makes sense.

## Script 01 In `Scripts/data_processing`: Prepare Supplementary Age-Bin Inputs

File:

- [01_prepare_supplementary_agebin_inputs.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py:1)

## Why This Script Comes First

This script is the bridge between the paper-derived supplementary spreadsheets and the downstream modelling scripts.

It is not a COBRApy script.  
It is a data preparation script.

You should read it first if your goal is to understand:

- where the age-bin abundance inputs came from
- how the 10 modeled species were selected from the supplementary workbook
- how subject-level abundance values were converted into pooled age-bin medians
- how normalized abundance weights were created for downstream community modelling

## What This Script Reads

It reads:

- `Suplementary_Data/Metadata_by_cohort.xlsx`
- `Suplementary_Data/subject_level_taxonomic_relative_abundance_values.xlsx`

The important inputs are:

- subject IDs
- subject ages
- subject-level species relative abundance values

## What This Script Writes

It writes processed outputs under:

- `Suplementary_Data/processed_data/`

The main outputs are:

- `subject_level_abundance_10_species.csv`
- `allcohort_agebin_median_abundance_10_species.csv`
- `allcohort_agebin_median_abundance_10_species_wide.csv`
- `agebin_input_qc_summary.csv`

There is also a cohort-specific output:

- `cohort_agebin_median_abundance_10_species.csv`

but the pooled all-cohort age-bin files are the main ones for age-bin community modelling.

## What This Script Does

At a high level, it:

1. reads the supplementary metadata workbook
2. reads the subject-level species abundance workbook
3. keeps only the 10 target species used in the AGORA2 community model
4. assigns each subject to an age bin
5. computes the median abundance for each species within each age bin
6. normalizes those medians into weights that sum to `1` within each age bin
7. writes tidy and wide-format CSV outputs

## Why The Wide And Long Files Both Exist

The pooled long file:

- `allcohort_agebin_median_abundance_10_species.csv`

is better for scripts and downstream analysis.

The pooled wide file:

- `allcohort_agebin_median_abundance_10_species_wide.csv`

is better for quickly reading the median abundance of one species across all age bins.

## Important Interpretation Point

The script outputs both:

- `median_abundance`
- `normalized_weight`

These are not the same thing.

- `median_abundance` is the pooled age-bin summary from the subject-level paper data
- `normalized_weight` is the modelling-ready version of those medians, scaled so the 10 species weights sum to `1` within an age bin

That normalization is useful when the next modelling step needs a relative abundance weighting vector rather than raw abundance magnitudes.

## What COBRApy Is Doing In This Project

COBRApy is the main Python package used for constraint-based metabolic modelling.

In this repository, COBRApy is used to:

- read SBML models
- inspect reactions and metabolites
- identify exchange reactions
- apply environmental constraints
- run flux balance analysis
- build a larger community model from multiple species models

The most important COBRApy ideas in this project are:

- `Model`
- `Reaction`
- `Metabolite`
- exchange reactions
- the objective reaction
- `model.medium`
- `model.optimize()`

If you understand those, the scripts become much easier to follow.

## Core COBRApy Objects Used Here

### `Model`

Imported in:

- [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:7)

What it is:

- a whole metabolic network

What it contains:

- reactions
- metabolites
- genes
- compartments
- an objective

Big picture role:

- one species SBML file becomes one COBRApy `Model`
- the community is also represented as one larger `Model`

Why it matters:

- almost everything happens through the `Model` object

### `Reaction`

Imported in:

- [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:7)

What it is:

- one biochemical or exchange process

Examples:

- a biomass reaction
- a glucose exchange reaction
- a connector reaction between a species and the shared pool

Big picture role:

- reactions are where flux happens
- bounds on reactions define what is allowed

Why it matters:

- the model does not think in “amounts”
- it thinks in allowed flux through reactions

### `Metabolite`

Imported in:

- [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:7)

What it is:

- one chemical species in a compartment

Examples:

- glucose in extracellular space
- butyrate in the shared community environment

Big picture role:

- metabolites connect reactions together
- in the community model, a shared metabolite is created for the common environment

## COBRApy Functions And Features Used In The Scripts

### `read_sbml_model`

Used in:

- [load_model()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:106)

What it does:

- loads an SBML XML file into a COBRApy `Model`

Why used:

- all the species reconstructions are stored as SBML files
- this is the entry point from file to working Python model

Big picture:

- without this, there is no species model to simulate

### `model.reactions`

Used in:

- all three scripts, directly or indirectly

Examples in code:

- [script 01 checks `model.reactions`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:54)
- [script 00 loops through `model.reactions`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:95)

What it does:

- gives access to the reactions in a model

Why used:

- to inspect objective reactions
- to search for butyrate-related reactions
- to fetch exchange reactions by ID
- to read flux values after optimization

Big picture:

- reactions are the main control points for growth, take in, and secretion

### `model.exchanges`

Used in:

- [build_model_exchange_map()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:65)

What it does:

- gives the exchange reactions in a model

Why used:

- exchange reactions are how the model takes in nutrients or secretes metabolites
- the scripts need them to match diet metabolites to actual model reaction IDs

Big picture:

- if you want to control what can enter or leave the model, exchange reactions are the place

### `model.medium`

Used in:

- [script 01 applies `model.medium`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:60)

What it does:

- lets you set the medium for a single model using a dictionary of exchange reaction IDs and allowed take-in values

Why used:

- this is the simplest COBRApy way to apply diet constraints for one species model

Big picture:

- in script `01`, this is how the chosen diet is applied before running FBA

Important note:

- script `02` does not use `model.medium` because the community model is more custom and uses manually built shared exchange reactions

### `model.optimize()`

Used in:

- [script 01 calls `model.optimize()`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:62)
- [script 02 calls `community.optimize()`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:94)

What it does:

- solves the flux balance analysis problem for the model

Why used:

- to get the best flux distribution under the current constraints

What it returns:

- a solution object with objective value, status, and fluxes

Big picture:

- this is the step where the model actually computes a result

### `solution.objective_value`

Used in:

- [script 01 reads `solution.objective_value`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:75)
- [script 02 reads `solution.objective_value`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:122)

What it does:

- gives the optimized value of the objective function

Why used:

- to measure growth or total community objective

Big picture:

- this is the main number telling you how well the objective was achieved

### `solution.fluxes`

Used in:

- [script 01 reads `solution.fluxes`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:66)
- [script 02 reads `solution.fluxes`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:97)

What it does:

- gives the flux value for each reaction in the solution

Why used:

- to read biomass flux
- to read butyrate exchange flux
- to inspect butyrate-related reactions

Big picture:

- this is how you move from “the model solved” to “what actually happened”

### `with model:`

Used in:

- [script 01 uses `with model:`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:57)
- [script 02 uses `with community:`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:79)

What it does:

- creates a temporary context where model changes are automatically undone afterward

Why used:

- each diet scenario changes bounds
- the script needs a clean model state for the next diet

Big picture:

- this prevents one diet simulation from accidentally carrying over settings into the next one

## Script 01: Single-Species Growth And Butyrate

File:

- [01_single_species_growth_and_butyrate.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:39)

## Why Start With Script 01

This is the easiest script to understand because:

- it handles one species at a time
- it uses standard COBRApy operations
- it does not yet build a custom community structure

This is where you should learn:

- model loading
- medium application
- optimization
- reading flux results

## What Script 01 Does

For each species model:

1. load the model
2. find the growth objective reaction
3. find butyrate-related reactions
4. apply one diet
5. optimize the model
6. record growth and butyrate-related output
7. repeat for the next diet

## What It Uses From COBRApy

### Loading the model

Script `01` uses a helper from `00`:

- [load_model()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:106)

That helper calls:

- [`read_sbml_model`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:108)

Why:

- each species starts as an SBML file

### Finding the objective reaction

Script `01` uses:

- [get_active_objective_reaction()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:46)

This checks which reaction currently has an objective coefficient.

Why:

- the script needs to know which reaction represents growth

Big picture:

- the objective is what the optimizer is trying to maximize

### Applying the diet

Script `01` uses:

- [build_medium_for_model()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:76)
- [script 01 sets `model.medium = medium`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:61)

Why:

- the diet file uses metabolite IDs like `glc_D`
- the model needs exact exchange reaction IDs
- the helper maps from diet metabolite ID to the right exchange reaction ID

Big picture:

- this is how the environment is imposed on the species model

### Running FBA

Script `01` uses:

- [script 01 runs `model.optimize()`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:62)

Why:

- to compute the best growth solution under that diet

### Reading the results

Script `01` reads:

- [growth from `solution.objective_value`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:75)
- [reaction fluxes from `solution.fluxes[...]`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:92)

Why:

- growth is read from the objective value
- butyrate reaction activity is read from individual reaction fluxes

## What You Should Learn From Script 01

When reading `01`, focus on these ideas:

- how one SBML file becomes one model
- how one diet becomes one medium
- how `optimize()` gives a solution
- how fluxes are read afterward

If you understand script `01`, you understand the basic COBRApy loop:

1. load model
2. set constraints
3. optimize
4. inspect solution

That loop is the foundation for script `02`.

## Script 00: Shared Helper Functions

File:

- [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:16)

## Why Script 00 Exists

Script `00` is not the main analysis script.  
It is a toolbox.

It exists because multiple scripts need the same logic, such as:

- loading diet tables
- loading models
- matching diet metabolites to exchange reactions
- finding the objective reaction
- building the community structure

This is good programming practice because:

- repeated code is avoided
- logic stays consistent between scripts
- the code is easier to maintain

## Most Important Helpers In Script 00

### `load_diet_table()`

Code:

- [load_diet_table()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:21)

What it does:

- reads `diet.csv`
- returns a dictionary of diet names and metabolite bounds

Why used:

- both single-species and community scripts need the same diet information

Big picture:

- converts the CSV into something the scripts can actually work with

### `build_model_exchange_map()`

Code:

- [build_model_exchange_map()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:65)

What it does:

- maps a metabolite base ID to its exchange reaction ID in a model

Why used:

- the diet file says things like `glc_D`
- the model reactions have IDs like `EX_glc(e)`
- the script needs to connect those two worlds

Big picture:

- this is what makes the diet file usable by the model

### `build_medium_for_model()`

Code:

- [build_medium_for_model()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:76)

What it does:

- builds the medium dictionary for one species model

Why used:

- script `01` needs to apply diet constraints to one model

Big picture:

- this helper is the bridge between the CSV diet and COBRApy `model.medium`

### `find_butyrate_reactions()`

Code:

- [find_butyrate_reactions()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:92)

What it does:

- searches reaction IDs, names, and equations for butyrate-related terms

Why used:

- the project wants a simple screen for possible butyrate-related metabolism

Important caution:

- this is a text-based search, not full biochemical pathway proof

### `namespace_species_model()`

Code:

- [namespace_species_model()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:111)

What it does:

- copies a species model
- renames metabolite, gene, reaction, and compartment IDs by adding the species name

Why used:

- different species models often reuse the same IDs
- when models are merged, those IDs would collide

Big picture:

- this is what makes multi-species merging possible without ambiguity

### `build_shared_environment_community()`

Code:

- [build_shared_environment_community()](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:169)

What it does:

- builds the full combined community model

This is the most important helper for community modelling.

It:

1. creates a new empty community `Model`
2. adds a shared community compartment
3. loads each species model
4. namespaces it
5. merges it into the community
6. creates shared metabolites
7. creates shared exchange reactions
8. creates connector reactions
9. sets the community objective as the sum of species biomass reactions

## What It Uses From COBRApy

### Creating a new model

It uses:

- [`Model("baseline_shared_environment_community")`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:174)

Why:

- the merged community itself must be represented as one COBRApy model

### Creating new metabolites

It uses:

- [`Metabolite(...)`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:212)

Why:

- the shared environment needs shared metabolite objects

Big picture:

- one shared metabolite represents the common pool version of something like glucose or butyrate

### Creating new reactions

It uses:

- [shared exchange `Reaction(...)`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:224)
- [connector `Reaction(...)`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:234)

Why:

- the script must create new shared exchange reactions and connector reactions

Big picture:

- these are not pre-existing in the SBML files
- they are new model structure added for the community design

### `community.add_metabolites(...)`

Why used:

- to place the new shared metabolites into the community model

Code:

- [`community.add_metabolites(...)`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:210)

### `community.add_reactions(...)`

Why used:

- to add the namespaced species reactions
- to add shared exchange reactions
- to add connector reactions

Code:

- [add namespaced species reactions](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:191)
- [add shared exchange reaction](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:228)
- [add connector reaction](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:238)

### `community.objective = {...}`

Why used:

- to define the community objective as the sum of all species biomass reactions

Code:

- [`community.objective = {...}`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:249)

Big picture:

- the optimization then tries to maximize total community biomass

## What You Should Learn From Script 00

When reading `00`, focus on:

- how the diet table is converted into usable data
- how exchange reactions are identified
- how IDs are renamed safely
- how a shared environment is physically created in the model
- how the community objective is built

This file teaches the structure of the model, not just the simulation loop.

## Script 02: Community Shared Environment

File:

- [02_community_shared_environment.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:38)

## What Script 02 Does

Script `02` is the main community analysis script.

It:

1. loads species models
2. loads the diet table
3. calls the helper that builds the full community model
4. applies one diet at a time to the shared community exchanges
5. optimizes the community
6. records overall and per-species growth
7. writes summary files

## What It Uses From COBRApy

Script `02` mostly uses COBRApy through the helpers built in `00`, but there are still a few direct concepts to understand.

### Shared exchange reactions

The community model contains exchange reactions for the shared environment.

Why:

- this is where the whole community takes in nutrients from the diet
- this is also where metabolites can be secreted back out

### `reaction.lower_bound` and `reaction.upper_bound`

Used in:

- [script 02 exchange bound setup](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:82)

What they do:

- directly control allowed flux through the shared exchange reaction

Why used:

- `lower_bound = 0.0` closes take in
- `lower_bound = -bound` opens take in up to the diet limit
- `upper_bound = 1000.0` leaves secretion broadly open

Big picture:

- this is how the diet gets translated into community-level take-in constraints

### `community.optimize()`

Used in:

- [script 02 runs `community.optimize()`](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:94)

What it does:

- solves the community FBA problem after the diet has been applied

Why used:

- to find the best total biomass solution for all species together

### Reading biomass fluxes from `solution.fluxes`

Script `02` reads each species biomass reaction from the solved community model.

Code:

- [read species biomass fluxes](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:101)

Why:

- this tells you which species actually grew in the combined optimization

Big picture:

- this is the output that lets you compare single-species and community behaviour

## What You Should Learn From Script 02

When reading `02`, focus on:

- how the community helper is called
- how diet bounds are applied to the shared exchanges
- why take in is limited by the diet values
- why secretion is left broadly open
- how species growth is extracted from one combined solution

This script teaches the simulation workflow for the already-built community model.

## Script 03: Age-Bin Weighted Community

File:

- [03_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/03_agebin_weighted_community.py:1)

## What Script 03 Does

Script `03` extends the baseline shared-environment community analysis by using the pooled age-bin abundance table as an input.

It:

1. reads `allcohort_agebin_median_abundance_10_species.csv`
2. validates that each age bin contains the full 10-species panel
3. builds the same AGORA2 shared-environment community model used in script `02`
4. replaces the unweighted sum-of-biomass objective with age-bin-specific biomass weights
5. applies each diet to the shared exchanges
6. solves the community once per `age_group + diet`
7. writes community-level and per-species growth outputs

The outputs follow the same pattern as the earlier modelling scripts and are written under:

- `Results/cobrapy_fba/tables/03_agebin_community_growth_summary_by_diet.csv`
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet.csv`
- `Results/cobrapy_fba/tables/03_agebin_community_species_growth_by_diet_wide.csv`

## What Changes Relative To Script 02

The community structure does not change.

The main change is the objective:

- script `02`: each species biomass reaction has coefficient `1.0`
- script `03`: each species biomass reaction has coefficient equal to that age bin's `normalized_weight`

This means the age-bin abundance table affects optimization directly, not just the reporting layer.

## Why The Outputs Include Input Abundance Columns

The species-level output from script `03` includes:

- `median_abundance`
- `normalized_weight`
- `species_biomass_flux`
- `is_growing`

That is useful because it keeps the input abundance signal and the modelled growth result in the same table.

So for one species in one age bin and one diet, you can immediately compare:

- how abundant it was in the input data
- how much weight it received in the objective
- whether it actually grew in the community model

## What You Should Learn From Script 03

When reading `03`, focus on:

- how the pooled age-bin CSV is loaded and validated
- how age-bin weights are mapped onto biomass reactions
- how the same community model is reused across different age bins
- how weighted optimization can still lead to sparse growth outcomes
- how long and wide result tables are generated for downstream interpretation

## The Most Important Big-Picture Ideas Across All Three Scripts

### Idea 1: A model is a constrained network

The scripts are not tracking concentrations over time.  
They are defining what reactions are possible and how much flux is allowed through them.

### Idea 2: Diet values are take-in limits

The values in `diet.csv` are used as maximum allowed take-in bounds.

They are not best interpreted as literal amounts sitting in a pool.

### Idea 3: Secretion is kept broadly open

The `1000` bound is a practical large limit so the model can release metabolites if needed.

### Idea 4: Community modelling needs explicit structure

You cannot just place species models side by side and call that a community.  
You need:

- safe namespacing
- a shared environment
- connector reactions
- a clear community objective

### Idea 5: Optimization decides the final flux pattern

Even if a metabolite can be taken in, the model may use none of it.  
The final fluxes depend on the objective and all the constraints together.

## A Good Way To Study These Scripts

Read them in this order:

1. [01_prepare_supplementary_agebin_inputs.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/data_processing/01_prepare_supplementary_agebin_inputs.py:1)
2. [01_single_species_growth_and_butyrate.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/01_single_species_growth_and_butyrate.py:39)
3. [00_baseline_modeling_utils.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/00_baseline_modeling_utils.py:16)
4. [02_community_shared_environment.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/02_community_shared_environment.py:38)
5. [03_agebin_weighted_community.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/modelling/03_agebin_weighted_community.py:1)

For each script, ask:

- what COBRApy object is being used here
- what biological idea does it represent
- what problem is this line solving
- how does this fit into the final optimization

## If You Want To Learn To Write This Yourself

The minimal set of COBRApy skills you need is:

1. load an SBML model
2. inspect exchange reactions
3. set a medium
4. optimize a model
5. read objective value and fluxes
6. create a new reaction
7. create a new metabolite
8. merge model content into a bigger model

Once those make sense, the community script stops looking mysterious and starts looking like a sequence of understandable design choices.

## Final Summary

The repository teaches community modelling in five layers:

- `Scripts/data_processing/01` teaches how supplementary spreadsheet data becomes age-bin model inputs
- `01` teaches basic single-species COBRApy use
- `00` teaches the reusable mechanics and model construction logic
- `02` teaches the final community simulation workflow
- `03` teaches how age-bin abundance weights are turned into weighted community objectives

The key COBRApy pieces to understand are:

- `Model`
- `Reaction`
- `Metabolite`
- `read_sbml_model`
- `model.exchanges`
- `model.medium`
- `lower_bound` and `upper_bound`
- `model.optimize()`
- `solution.objective_value`
- `solution.fluxes`

If you understand why those are used, then you understand most of what the scripts are doing.
