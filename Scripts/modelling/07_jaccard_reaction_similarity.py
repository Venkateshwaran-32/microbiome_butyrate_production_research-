from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
from statistics import median


SCRIPT_DIR = Path(__file__).resolve().parent

# Load the shared baseline-modeling utility module.
UTILS_PATH = SCRIPT_DIR / "00_baseline_modeling_utils.py"
UTILS_SPEC = importlib.util.spec_from_file_location("baseline_modeling_utils", UTILS_PATH)
if UTILS_SPEC is None or UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load utility module from {UTILS_PATH}")
UTILS_MODULE = importlib.util.module_from_spec(UTILS_SPEC)
UTILS_SPEC.loader.exec_module(UTILS_MODULE)

# Load the shared report-output dictionary helpers.
REPORT_UTILS_PATH = SCRIPT_DIR / "00_report_output_dictionary.py"
REPORT_UTILS_SPEC = importlib.util.spec_from_file_location("report_output_dictionary", REPORT_UTILS_PATH)
if REPORT_UTILS_SPEC is None or REPORT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load report utility module from {REPORT_UTILS_PATH}")
REPORT_UTILS_MODULE = importlib.util.module_from_spec(REPORT_UTILS_SPEC)
REPORT_UTILS_SPEC.loader.exec_module(REPORT_UTILS_MODULE)

load_model = UTILS_MODULE.load_model
load_species_model_paths = UTILS_MODULE.load_species_model_paths
species_name_from_path = UTILS_MODULE.species_name_from_path
build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec


MODELS_DIR = Path("Models/vmh_agora2_sbml")
WIDE_OUTPUT = Path("Results/cobrapy_fba/tables/07_jaccard_reaction_matrix_wide.csv")
LONG_OUTPUT = Path("Results/cobrapy_fba/tables/07_jaccard_reaction_pairs_long.csv")
BUILD_REPORT = Path("Results/cobrapy_fba/reports/07_jaccard_reaction_similarity_report.txt")

EXPECTED_REACTION_COUNTS = {
    "Alistipes_onderdonkii_DSM_19147": 1189,
    "Alistipes_shahii_WAL_8301": 2434,
    "Bacteroides_dorei_DSM_17855": 2115,
    "Bacteroides_xylanisolvens_XB1A": 2657,
    "Bilophila_wadsworthia_3_1_6": 1240,
    "Escherichia_coli_UTI89_UPEC": 3198,
    "Faecalibacterium_prausnitzii_M21_2": 2046,
    "Klebsiella_pneumoniae_pneumoniae_MGH78578": 2113,
    "Parabacteroides_merdae_ATCC_43184": 2495,
    "Ruminococcus_torques_ATCC_27756": 998,
}

WIDE_FIELDNAMES = ["species_name"]
LONG_FIELDNAMES = [
    "species_a",
    "species_b",
    "n_reactions_a",
    "n_reactions_b",
    "intersection",
    "union",
    "jaccard",
    "dissimilarity",
]
CSV_OUTPUT_SPECS_TEMPLATE = [
    (
        WIDE_OUTPUT,
        "one row per species; columns are the same 10 species (wide-format Jaccard matrix)",
        [
            col("species_name", "Species identifier (SBML file stem); also the row label of the Jaccard matrix."),
        ],
    ),
    (
        LONG_OUTPUT,
        "one row per ordered species pair (100 rows for 10 species)",
        [
            col("species_a", "First species in the ordered pair; SBML file stem."),
            col("species_b", "Second species in the ordered pair; SBML file stem."),
            col("n_reactions_a", "Size of species_a's reaction-ID set."),
            col("n_reactions_b", "Size of species_b's reaction-ID set."),
            col("intersection", "Number of reaction IDs shared between species_a and species_b."),
            col("union", "Number of distinct reaction IDs across the two species combined."),
            col(
                "jaccard",
                "Jaccard similarity between the two reaction sets.",
                "jaccard = intersection / union",
            ),
            col(
                "dissimilarity",
                "Jaccard dissimilarity; complementary distance metric used for hierarchical clustering.",
                "dissimilarity = 1 - jaccard",
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
    model_paths = load_species_model_paths(MODELS_DIR)
    species_list = [species_name_from_path(p) for p in model_paths]

    if set(species_list) != set(EXPECTED_REACTION_COUNTS):
        raise RuntimeError(
            f"Loaded species set {species_list} does not match the 10 expected species "
            f"{sorted(EXPECTED_REACTION_COUNTS)}."
        )

    reaction_sets: dict[str, set[str]] = {}
    print("Loading SBML models and collecting reaction-ID sets:")
    for species_name, path in zip(species_list, model_paths):
        model = load_model(path)
        reaction_ids = {r.id for r in model.reactions}
        reaction_sets[species_name] = reaction_ids
        actual_count = len(reaction_ids)
        expected_count = EXPECTED_REACTION_COUNTS[species_name]
        marker = "OK" if actual_count == expected_count else f"!= EXPECTED({expected_count})"
        print(f"  {species_name}: {actual_count} reactions  [{marker}]")
        if actual_count != expected_count:
            raise AssertionError(
                f"Reaction count for {species_name} is {actual_count}; expected {expected_count}. "
                f"Either the SBML changed or .reactions iteration is filtering unexpectedly."
            )

    # Pairwise Jaccard.
    long_rows: list[dict[str, object]] = []
    wide_rows: list[dict[str, object]] = []
    jaccard_lookup: dict[tuple[str, str], float] = {}

    for species_a in species_list:
        wide_row: dict[str, object] = {"species_name": species_a}
        for species_b in species_list:
            set_a = reaction_sets[species_a]
            set_b = reaction_sets[species_b]
            if species_a == species_b:
                inter = len(set_a)
                union = len(set_a)
                jaccard_value = 1.0
            else:
                inter = len(set_a & set_b)
                union = len(set_a | set_b)
                jaccard_value = inter / union if union else 0.0
            jaccard_lookup[(species_a, species_b)] = jaccard_value
            wide_row[species_b] = jaccard_value
            long_rows.append(
                {
                    "species_a": species_a,
                    "species_b": species_b,
                    "n_reactions_a": len(set_a),
                    "n_reactions_b": len(set_b),
                    "intersection": inter,
                    "union": union,
                    "jaccard": jaccard_value,
                    "dissimilarity": 1.0 - jaccard_value,
                }
            )
        wide_rows.append(wide_row)

    # Inline asserts: diagonal == 1.0 exactly.
    for species in species_list:
        assert jaccard_lookup[(species, species)] == 1.0, (
            f"Diagonal Jaccard for {species} is {jaccard_lookup[(species, species)]}; expected 1.0."
        )
    print(f"\nDiagonal == 1.0 for all {len(species_list)} species: PASS")

    # Symmetry: jaccard[a,b] == jaccard[b,a].
    for a in species_list:
        for b in species_list:
            delta = abs(jaccard_lookup[(a, b)] - jaccard_lookup[(b, a)])
            assert delta < 1e-12, (
                f"Symmetry violated for ({a}, {b}): "
                f"jaccard_ab={jaccard_lookup[(a, b)]}, jaccard_ba={jaccard_lookup[(b, a)]}"
            )
    print("Symmetry within 1e-12 for all unordered pairs: PASS")

    # Summary statistics over the 45 unordered off-diagonal pairs.
    off_diagonal = [
        (a, b, jaccard_lookup[(a, b)])
        for i, a in enumerate(species_list)
        for j, b in enumerate(species_list)
        if i < j
    ]
    off_values = [j for _, _, j in off_diagonal]
    closest = max(off_diagonal, key=lambda t: t[2])
    farthest = min(off_diagonal, key=lambda t: t[2])

    # Wide CSV.
    wide_fieldnames = ["species_name"] + species_list
    write_csv(WIDE_OUTPUT, wide_fieldnames, wide_rows)

    # Long CSV.
    write_csv(LONG_OUTPUT, LONG_FIELDNAMES, long_rows)

    # Build report.
    report_lines = [
        "Jaccard reaction-set similarity across the 10 AGORA2 species",
        "",
        f"Models directory: {MODELS_DIR}",
        f"Number of species: {len(species_list)}",
        f"Number of ordered pairs written to long CSV: {len(long_rows)}",
        "",
        "Per-species reaction count",
    ]
    for species_name in species_list:
        report_lines.append(f"  {species_name}: {len(reaction_sets[species_name])}")

    report_lines.append("")
    report_lines.append("Pairwise Jaccard summary (off-diagonal, 45 unordered pairs)")
    report_lines.append(f"  Minimum: {min(off_values):.6f}")
    report_lines.append(f"  Median:  {median(off_values):.6f}")
    report_lines.append(f"  Maximum: {max(off_values):.6f}")
    report_lines.append(f"  Closest pair: {closest[0]} vs {closest[1]} -> Jaccard {closest[2]:.6f}")
    report_lines.append(f"  Farthest pair: {farthest[0]} vs {farthest[1]} -> Jaccard {farthest[2]:.6f}")
    report_lines.append("")
    report_lines.append("Verification asserts run inside this script")
    report_lines.append("  Diagonal == 1.0 for all species: PASS")
    report_lines.append("  Symmetry within 1e-12 for all pairs: PASS")
    report_lines.append("  Per-species reaction counts match expected (1189, 2434, 2115, 2657, 1240,")
    report_lines.append("                                              3198, 2046, 2113, 2495, 998): PASS")
    report_lines.append("")
    report_lines.append("Output files")
    report_lines.append(f"  Wide matrix: {WIDE_OUTPUT}")
    report_lines.append(f"  Long pairs:  {LONG_OUTPUT}")
    report_lines.append(f"  This report: {BUILD_REPORT}")

    # Build the CSV Output Dictionary specs (header for the wide CSV depends on species_list,
    # so we rebuild the spec list here with the runtime species columns appended).
    csv_specs = []
    for path, row_grain, base_cols in CSV_OUTPUT_SPECS_TEMPLATE:
        if path == WIDE_OUTPUT:
            extra_cols = [
                col(species_name, "Jaccard similarity between this species (column) and species_name (row).")
                for species_name in species_list
            ]
            csv_specs.append(csv_output_spec(path, row_grain, base_cols + extra_cols))
        else:
            csv_specs.append(csv_output_spec(path, row_grain, base_cols))

    BUILD_REPORT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_REPORT.write_text(build_report_text(report_lines, csv_specs))

    print(f"\nWrote {WIDE_OUTPUT}")
    print(f"Wrote {LONG_OUTPUT}")
    print(f"Wrote {BUILD_REPORT}")
    print(f"\nClosest pair (highest Jaccard): {closest[0]} vs {closest[1]} -> {closest[2]:.6f}")
    print(f"Farthest pair (lowest Jaccard): {farthest[0]} vs {farthest[1]} -> {farthest[2]:.6f}")


if __name__ == "__main__":
    main()
