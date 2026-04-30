from __future__ import annotations

import importlib.util
from pathlib import Path

# Load the shared helper module that sits beside this script.
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
load_diet_table = UTILS_MODULE.load_diet_table
load_species_model_paths = UTILS_MODULE.load_species_model_paths
species_name_from_path = UTILS_MODULE.species_name_from_path

MICOM_UTILS_PATH = Path(__file__).with_name("00_micom_utils.py")
MICOM_UTILS_SPEC = importlib.util.spec_from_file_location("micom_utils", MICOM_UTILS_PATH)
if MICOM_UTILS_SPEC is None or MICOM_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load MICOM utility module from {MICOM_UTILS_PATH}")
MICOM_UTILS_MODULE = importlib.util.module_from_spec(MICOM_UTILS_SPEC)
MICOM_UTILS_SPEC.loader.exec_module(MICOM_UTILS_MODULE)

build_equal_abundance_taxonomy = MICOM_UTILS_MODULE.build_equal_abundance_taxonomy
run_cooperative_tradeoff = MICOM_UTILS_MODULE.run_cooperative_tradeoff
write_csv = MICOM_UTILS_MODULE.write_csv
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec

MODELS_DIR = Path("Models/vmh_agora2_sbml")
DIET_CSV = Path("Medium_files/diet.csv")
SUMMARY_OUTPUT = Path("Results/micom_fba/tables/04_micom_community_growth_summary_by_diet.csv")
TAXON_OUTPUT = Path("Results/micom_fba/tables/04_micom_taxon_growth_by_diet.csv")
BUILD_REPORT = Path("Results/micom_fba/reports/04_micom_model_build_report.txt")
COMMUNITY_ID = "micom_baseline_10_species"
TRADEOFF_FRACTION = 0.5
SUMMARY_FIELDNAMES = [
    "diet_name",
    "solver_status",
    "community_growth_rate",
    "objective_value",
    "tradeoff_fraction",
    "num_taxa_total",
    "num_taxa_with_nonzero_growth",
    "matched_diet_metabolites",
    "missing_diet_metabolites",
]
TAXON_FIELDNAMES = [
    "diet_name",
    "taxon_id",
    "abundance",
    "growth_rate",
    "is_growing",
    "reactions",
    "metabolites",
]
CSV_OUTPUT_SPECS = [
    csv_output_spec(
        SUMMARY_OUTPUT,
        "one row per diet_name",
        [
            col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
            col("solver_status", "MICOM solver status returned for the cooperative tradeoff solve."),
            col("community_growth_rate", "MICOM-reported community growth rate for the solved diet."),
            col(
                "objective_value",
                "Objective value returned by MICOM for this cooperative tradeoff solve.",
                "objective_value = optimization objective reported by MICOM after cooperative_tradeoff",
            ),
            col("tradeoff_fraction", "Tradeoff fraction passed into MICOM cooperative tradeoff."),
            col("num_taxa_total", "Number of taxa returned in the MICOM members table for this diet."),
            col(
                "num_taxa_with_nonzero_growth",
                "Count of taxa whose growth rate exceeded the growth threshold.",
                f"num_taxa_with_nonzero_growth = count(growth_rate > {GROWTH_THRESHOLD})",
            ),
            col(
                "matched_diet_metabolites",
                "Count of diet metabolite IDs translated into MICOM medium entries.",
                "matched_diet_metabolites = number of diet metabolite_ids with a MICOM medium mapping",
            ),
            col(
                "missing_diet_metabolites",
                "Count of diet metabolite IDs that could not be translated into MICOM medium entries.",
                "missing_diet_metabolites = total diet metabolite_ids - matched_diet_metabolites",
            ),
        ],
    ),
    csv_output_spec(
        TAXON_OUTPUT,
        "one row per diet_name x taxon_id",
        [
            col("diet_name", "Diet scenario name from Medium_files/diet.csv."),
            col("taxon_id", "MICOM taxon/model identifier."),
            col(
                "abundance",
                "Taxon abundance used in the equal-abundance baseline taxonomy table.",
                "abundance = 1 / number of taxa in the baseline community",
            ),
            col("growth_rate", "MICOM-reported taxon growth rate for this diet."),
            col(
                "is_growing",
                "Boolean flag showing whether the MICOM taxon growth rate exceeded the growth threshold.",
                f"is_growing = growth_rate > {GROWTH_THRESHOLD}",
            ),
            col("reactions", "Number of reactions present in the MICOM member model returned for this taxon."),
            col("metabolites", "Number of metabolites present in the MICOM member model returned for this taxon."),
        ],
    ),
]


def main() -> None:
    try:
        from micom import Community
    except ImportError as exc:
        raise ImportError(
            "MICOM is not installed in this environment. Install it first, for example with "
            "`pip install micom`, then rerun Scripts/modelling/04_micom_baseline_community.py."
        ) from exc

    model_paths = load_species_model_paths(MODELS_DIR)
    diet_table = load_diet_table(DIET_CSV)
    taxonomy = build_equal_abundance_taxonomy(model_paths, species_name_from_path)

    report_lines = [
        "MICOM baseline community build report",
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

    community = Community(taxonomy=taxonomy, model_db=None, id=COMMUNITY_ID, name=COMMUNITY_ID, progress=False)

    summary_rows: list[dict[str, object]] = []
    taxon_rows: list[dict[str, object]] = []

    report_lines.append("Diet mapping and solve summary")
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
            f"{diet_name}: solver_status={solution.status}, community_growth_rate={solution.growth_rate}, "
            f"matched_diet_metabolites={len(medium)}, missing_diet_metabolites={len(missing_metabolites)}"
        )
        if missing_metabolites:
            report_lines.append(f"{diet_name} missing metabolite_ids: {', '.join(sorted(missing_metabolites))}")
        report_lines.append("")

    write_csv(
        SUMMARY_OUTPUT,
        SUMMARY_FIELDNAMES,
        summary_rows,
    )
    write_csv(
        TAXON_OUTPUT,
        TAXON_FIELDNAMES,
        taxon_rows,
    )
    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, CSV_OUTPUT_SPECS))

    print(f"Wrote {SUMMARY_OUTPUT}")
    print(f"Wrote {TAXON_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")


if __name__ == "__main__":
    main()
