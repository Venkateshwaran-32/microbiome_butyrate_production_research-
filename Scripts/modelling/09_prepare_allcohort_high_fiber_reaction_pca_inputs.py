from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent

REPORT_UTILS_PATH = SCRIPT_DIR / "00_report_output_dictionary.py"
REPORT_UTILS_SPEC = importlib.util.spec_from_file_location("report_output_dictionary", REPORT_UTILS_PATH)
if REPORT_UTILS_SPEC is None or REPORT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load report utility module from {REPORT_UTILS_PATH}")
REPORT_UTILS_MODULE = importlib.util.module_from_spec(REPORT_UTILS_SPEC)
REPORT_UTILS_SPEC.loader.exec_module(REPORT_UTILS_MODULE)

build_report_text = REPORT_UTILS_MODULE.build_report_text
col = REPORT_UTILS_MODULE.col
csv_output_spec = REPORT_UTILS_MODULE.csv_output_spec
dynamic_tail = REPORT_UTILS_MODULE.dynamic_tail


FLUX_INPUT = Path(
    "Results/subject_level_fba/tables/08_allcohort_subject_reaction_flux_nonzero_long_high_fiber_pfba.csv"
)
SUMMARY_INPUT = Path(
    "Results/subject_level_fba/tables/08_allcohort_subject_community_growth_high_fiber_pfba.csv"
)
TAXON_GROWTH_INPUT = Path(
    "Results/subject_level_fba/tables/08_allcohort_subject_taxon_growth_high_fiber_pfba.csv"
)

TABLES_DIR = Path("Results/subject_level_fba/tables")
REPORTS_DIR = Path("Results/subject_level_fba/reports")

REACTION_BY_SUBJECT_ALL = TABLES_DIR / "09_allcohort_high_fiber_reaction_by_subject_matrix_all516.csv"
REACTION_BY_SUBJECT_OPTIMAL = TABLES_DIR / "09_allcohort_high_fiber_reaction_by_subject_matrix_optimal414.csv"
SUBJECT_BY_REACTION_ALL = TABLES_DIR / "09_allcohort_high_fiber_subject_by_reaction_matrix_all516.csv"
SUBJECT_BY_REACTION_OPTIMAL = TABLES_DIR / "09_allcohort_high_fiber_subject_by_reaction_matrix_optimal414.csv"
SUBJECT_METADATA_ALL = TABLES_DIR / "09_allcohort_high_fiber_subject_metadata_all516.csv"
SUBJECT_METADATA_OPTIMAL = TABLES_DIR / "09_allcohort_high_fiber_subject_metadata_optimal414.csv"
TAXON_CONTRIBUTION_OUTPUT = TABLES_DIR / "09_allcohort_high_fiber_reaction_taxon_contribution_by_subject_set.csv"
INPUT_REPORT = REPORTS_DIR / "09_allcohort_high_fiber_reaction_pca_input_report.txt"

ALL_SUBJECT_SET = "all516"
OPTIMAL_SUBJECT_SET = "optimal414"
SUMMARY_COLUMNS = [
    "subject_id",
    "cohort",
    "age_years",
    "age_group",
    "solver_status",
    "community_growth_rate",
]
TOKEN_GROUPS = {
    "lysine": ("lys",),
    "butyrate": ("but", "btcoa"),
}
CSV_OUTPUT_SPECS = [
    csv_output_spec(
        REACTION_BY_SUBJECT_ALL,
        "one row per reaction_id for the all516 subject set",
        [
            col("reaction_id", "Collapsed reaction identifier after summing the same reaction across taxa within each subject."),
        ],
        dynamic_columns=dynamic_tail(
            "subject_id columns",
            "Each remaining column stores the collapsed signed flux for one subject in the all516 set.",
            "value = sum(taxon-level flux across all taxa within subject_id + reaction_id); missing subject-reaction pairs are filled with 0.0",
        ),
    ),
    csv_output_spec(
        REACTION_BY_SUBJECT_OPTIMAL,
        "one row per reaction_id for the optimal414 subject set",
        [
            col("reaction_id", "Collapsed reaction identifier after summing the same reaction across taxa within each subject."),
        ],
        dynamic_columns=dynamic_tail(
            "subject_id columns",
            "Each remaining column stores the collapsed signed flux for one optimal subject.",
            "value = sum(taxon-level flux across all taxa within subject_id + reaction_id); missing subject-reaction pairs are filled with 0.0",
        ),
    ),
    csv_output_spec(
        SUBJECT_BY_REACTION_ALL,
        "one row per subject_id for the all516 subject set",
        [
            col("subject_id", "Subject identifier from the all516 subject set."),
        ],
        dynamic_columns=dynamic_tail(
            "reaction_id columns",
            "Each remaining column stores the collapsed signed flux for one reaction in the all516 set.",
            "value = sum(taxon-level flux across all taxa within subject_id + reaction_id); missing subject-reaction pairs are filled with 0.0",
        ),
    ),
    csv_output_spec(
        SUBJECT_BY_REACTION_OPTIMAL,
        "one row per subject_id for the optimal414 subject set",
        [
            col("subject_id", "Subject identifier from the optimal414 subject set."),
        ],
        dynamic_columns=dynamic_tail(
            "reaction_id columns",
            "Each remaining column stores the collapsed signed flux for one reaction in the optimal414 set.",
            "value = sum(taxon-level flux across all taxa within subject_id + reaction_id); missing subject-reaction pairs are filled with 0.0",
        ),
    ),
    csv_output_spec(
        SUBJECT_METADATA_ALL,
        "one row per subject_id for the all516 subject set",
        [
            col("subject_id", "Subject identifier from the all516 subject set."),
            col("cohort", "Cohort label carried through from the subject metadata."),
            col("age_years", "Subject age in years from the metadata table."),
            col("age_group", "Age-bin label assigned from the metadata age."),
            col("solver_status", "Solver status carried over from the 08 all-cohort MICOM summary table."),
            col("community_growth_rate", "Community growth rate carried over from the 08 all-cohort MICOM summary table."),
        ],
    ),
    csv_output_spec(
        SUBJECT_METADATA_OPTIMAL,
        "one row per subject_id for the optimal414 subject set",
        [
            col("subject_id", "Subject identifier from the optimal414 subject set."),
            col("cohort", "Cohort label carried through from the subject metadata."),
            col("age_years", "Subject age in years from the metadata table."),
            col("age_group", "Age-bin label assigned from the metadata age."),
            col("solver_status", "Solver status carried over from the 08 all-cohort MICOM summary table."),
            col("community_growth_rate", "Community growth rate carried over from the 08 all-cohort MICOM summary table."),
        ],
    ),
    csv_output_spec(
        TAXON_CONTRIBUTION_OUTPUT,
        "one row per subject_set x reaction_id x taxon_id",
        [
            col("subject_set", "Subject-set label used for the contribution summary, either all516 or optimal414."),
            col("reaction_id", "Collapsed reaction identifier being summarized."),
            col("reaction_token_group", "Semicolon-separated token groups matched from the reaction ID for convenience filtering."),
            col("taxon_id", "MICOM taxon/model identifier contributing flux to this reaction."),
            col("species_name", "Species label mapped onto this model taxon."),
            col("paper_taxon", "Original paper taxon label mapped onto this model species."),
            col("n_subjects_in_set", "Total number of subjects in the selected subject set."),
            col("n_subjects_with_flux", "Number of subjects in the set where this taxon carried nonzero flux for this reaction."),
            col(
                "fraction_subjects_with_flux",
                "Prevalence of this taxon-reaction flux within the selected subject set.",
                "fraction_subjects_with_flux = n_subjects_with_flux / n_subjects_in_set",
            ),
            col("median_signed_flux", "Median signed taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
            col("median_abs_flux", "Median absolute taxon-level flux across the subjects with exported rows for this taxon-reaction pair."),
            col(
                "total_abs_flux",
                "Total absolute flux contributed by this taxon across all subjects in the selected set for this reaction.",
                "total_abs_flux = sum(abs(flux) across all exported subject rows within subject_set + reaction_id + taxon_id)",
            ),
            col(
                "fraction_of_total_abs_flux",
                "Share of the total absolute reaction flux carried by this taxon within the selected subject set.",
                "fraction_of_total_abs_flux = total_abs_flux / sum(total_abs_flux across all taxon_id within subject_set + reaction_id)",
            ),
        ],
    ),
]


def match_reaction_token_groups(reaction_id: str) -> str:
    reaction_lower = reaction_id.lower()
    matches: list[str] = []
    for group_name, tokens in TOKEN_GROUPS.items():
        if any(token in reaction_lower for token in tokens):
            matches.append(group_name)
    return ";".join(matches)


def load_subject_metadata() -> pd.DataFrame:
    subject_metadata = pd.read_csv(SUMMARY_INPUT, usecols=SUMMARY_COLUMNS)
    if subject_metadata["subject_id"].duplicated().any():
        duplicates = subject_metadata.loc[subject_metadata["subject_id"].duplicated(), "subject_id"].tolist()
        raise ValueError(f"Duplicate subject_id values found in {SUMMARY_INPUT}: {duplicates[:5]}")
    subject_metadata = subject_metadata.sort_values("subject_id").reset_index(drop=True)
    return subject_metadata


def load_taxon_lookup() -> pd.DataFrame:
    taxon_lookup = (
        pd.read_csv(TAXON_GROWTH_INPUT, usecols=["taxon_id", "species_name", "paper_taxon"])
        .drop_duplicates()
        .sort_values("taxon_id")
        .reset_index(drop=True)
    )
    return taxon_lookup


def load_taxon_flux_rows() -> pd.DataFrame:
    flux_rows = pd.read_csv(
        FLUX_INPUT,
        usecols=["subject_id", "taxon_id", "reaction_id", "flux", "abs_flux", "is_medium"],
    )
    taxon_flux_rows = flux_rows.loc[~flux_rows["is_medium"].astype(str).str.lower().eq("true")].copy()
    taxon_flux_rows = taxon_flux_rows.drop(columns=["is_medium"])
    return taxon_flux_rows


def build_subject_matrix(collapsed_flux: pd.DataFrame, ordered_subject_ids: list[str]) -> pd.DataFrame:
    subject_by_reaction = collapsed_flux.pivot(index="subject_id", columns="reaction_id", values="flux")
    subject_by_reaction = subject_by_reaction.reindex(ordered_subject_ids, fill_value=0.0).fillna(0.0)
    subject_by_reaction = subject_by_reaction.reindex(sorted(subject_by_reaction.columns), axis=1)
    subject_by_reaction = subject_by_reaction.reset_index()
    subject_by_reaction.columns.name = None
    return subject_by_reaction


def build_reaction_by_subject(subject_by_reaction: pd.DataFrame) -> pd.DataFrame:
    reaction_by_subject = subject_by_reaction.set_index("subject_id").T.reset_index()
    reaction_by_subject = reaction_by_subject.rename(columns={"index": "reaction_id"})
    return reaction_by_subject


def build_taxon_contribution_summary(
    taxon_flux_rows: pd.DataFrame,
    subject_metadata: pd.DataFrame,
    taxon_lookup: pd.DataFrame,
) -> pd.DataFrame:
    subject_sets = {
        ALL_SUBJECT_SET: set(subject_metadata["subject_id"]),
        OPTIMAL_SUBJECT_SET: set(
            subject_metadata.loc[subject_metadata["solver_status"] == "optimal", "subject_id"]
        ),
    }

    contribution_frames: list[pd.DataFrame] = []

    for subject_set_name, allowed_subject_ids in subject_sets.items():
        subject_count = len(allowed_subject_ids)
        subset = taxon_flux_rows.loc[taxon_flux_rows["subject_id"].isin(allowed_subject_ids)].copy()
        grouped = (
            subset.groupby(["reaction_id", "taxon_id"], as_index=False)
            .agg(
                n_subjects_with_flux=("subject_id", "nunique"),
                median_signed_flux=("flux", "median"),
                median_abs_flux=("abs_flux", "median"),
                total_abs_flux=("abs_flux", "sum"),
            )
            .sort_values(["reaction_id", "taxon_id"])
            .reset_index(drop=True)
        )
        grouped["subject_set"] = subject_set_name
        grouped["n_subjects_in_set"] = subject_count
        grouped["fraction_subjects_with_flux"] = grouped["n_subjects_with_flux"] / subject_count
        grouped["fraction_of_total_abs_flux"] = grouped["total_abs_flux"] / grouped.groupby("reaction_id")[
            "total_abs_flux"
        ].transform("sum")
        grouped["reaction_token_group"] = grouped["reaction_id"].map(match_reaction_token_groups)
        grouped = grouped.merge(taxon_lookup, on="taxon_id", how="left")
        contribution_frames.append(grouped)

    contribution_summary = pd.concat(contribution_frames, ignore_index=True)
    contribution_summary = contribution_summary[
        [
            "subject_set",
            "reaction_id",
            "reaction_token_group",
            "taxon_id",
            "species_name",
            "paper_taxon",
            "n_subjects_in_set",
            "n_subjects_with_flux",
            "fraction_subjects_with_flux",
            "median_signed_flux",
            "median_abs_flux",
            "total_abs_flux",
            "fraction_of_total_abs_flux",
        ]
    ]
    return contribution_summary


def write_report(
    *,
    subject_metadata: pd.DataFrame,
    optimal_metadata: pd.DataFrame,
    collapsed_flux: pd.DataFrame,
    optimal_collapsed_flux: pd.DataFrame,
    contribution_summary: pd.DataFrame,
) -> None:
    report_lines = [
        "All-cohort high-fiber reaction PCA input report",
        f"Flux input: {FLUX_INPUT}",
        f"Summary input: {SUMMARY_INPUT}",
        f"Taxon growth input: {TAXON_GROWTH_INPUT}",
        "",
        "Matrix construction",
        "- Source flux file stores only nonzero taxon-level rows.",
        "- Medium rows were excluded before matrix building.",
        "- Repeated subject_id + reaction_id entries were collapsed with a signed sum across taxa.",
        "- Missing subject-reaction pairs were filled with 0.0 in the final matrices.",
        "",
        f"Subjects in all516 set: {len(subject_metadata)}",
        f"Subjects in optimal414 set: {len(optimal_metadata)}",
        f"Collapsed subject-reaction rows in all516 set: {len(collapsed_flux)}",
        f"Collapsed subject-reaction rows in optimal414 set: {len(optimal_collapsed_flux)}",
        f"Unique reactions in all516 set: {collapsed_flux['reaction_id'].nunique()}",
        f"Unique reactions in optimal414 set: {optimal_collapsed_flux['reaction_id'].nunique()}",
        "",
        "Contribution summary rows by subject set",
    ]

    contribution_counts = (
        contribution_summary.groupby("subject_set").size().sort_index().to_dict()
    )
    for subject_set_name, count in contribution_counts.items():
        report_lines.append(f"{subject_set_name}: {count}")

    report_lines.extend(
        [
            "",
            "Output files",
            f"Reaction-by-subject matrix (all516): {REACTION_BY_SUBJECT_ALL}",
            f"Reaction-by-subject matrix (optimal414): {REACTION_BY_SUBJECT_OPTIMAL}",
            f"Subject-by-reaction matrix (all516): {SUBJECT_BY_REACTION_ALL}",
            f"Subject-by-reaction matrix (optimal414): {SUBJECT_BY_REACTION_OPTIMAL}",
            f"Subject metadata (all516): {SUBJECT_METADATA_ALL}",
            f"Subject metadata (optimal414): {SUBJECT_METADATA_OPTIMAL}",
            f"Taxon contribution summary: {TAXON_CONTRIBUTION_OUTPUT}",
        ]
    )

    INPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    INPUT_REPORT.write_text(build_report_text(report_lines, CSV_OUTPUT_SPECS))


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    subject_metadata = load_subject_metadata()
    optimal_metadata = subject_metadata.loc[subject_metadata["solver_status"] == "optimal"].copy()
    taxon_lookup = load_taxon_lookup()
    taxon_flux_rows = load_taxon_flux_rows()

    collapsed_flux = (
        taxon_flux_rows.groupby(["subject_id", "reaction_id"], as_index=False)["flux"].sum().sort_values(
            ["subject_id", "reaction_id"]
        )
    )
    optimal_collapsed_flux = collapsed_flux.loc[
        collapsed_flux["subject_id"].isin(set(optimal_metadata["subject_id"]))
    ].copy()

    subject_by_reaction_all = build_subject_matrix(collapsed_flux, subject_metadata["subject_id"].tolist())
    subject_by_reaction_optimal = build_subject_matrix(
        optimal_collapsed_flux,
        optimal_metadata["subject_id"].tolist(),
    )
    reaction_by_subject_all = build_reaction_by_subject(subject_by_reaction_all)
    reaction_by_subject_optimal = build_reaction_by_subject(subject_by_reaction_optimal)

    contribution_summary = build_taxon_contribution_summary(
        taxon_flux_rows,
        subject_metadata,
        taxon_lookup,
    )

    subject_by_reaction_all.to_csv(SUBJECT_BY_REACTION_ALL, index=False)
    subject_by_reaction_optimal.to_csv(SUBJECT_BY_REACTION_OPTIMAL, index=False)
    reaction_by_subject_all.to_csv(REACTION_BY_SUBJECT_ALL, index=False)
    reaction_by_subject_optimal.to_csv(REACTION_BY_SUBJECT_OPTIMAL, index=False)
    subject_metadata.to_csv(SUBJECT_METADATA_ALL, index=False)
    optimal_metadata.to_csv(SUBJECT_METADATA_OPTIMAL, index=False)
    contribution_summary.to_csv(TAXON_CONTRIBUTION_OUTPUT, index=False)

    write_report(
        subject_metadata=subject_metadata,
        optimal_metadata=optimal_metadata,
        collapsed_flux=collapsed_flux,
        optimal_collapsed_flux=optimal_collapsed_flux,
        contribution_summary=contribution_summary,
    )

    print(f"Wrote {SUBJECT_BY_REACTION_ALL}")
    print(f"Wrote {SUBJECT_BY_REACTION_OPTIMAL}")
    print(f"Wrote {REACTION_BY_SUBJECT_ALL}")
    print(f"Wrote {REACTION_BY_SUBJECT_OPTIMAL}")
    print(f"Wrote {SUBJECT_METADATA_ALL}")
    print(f"Wrote {SUBJECT_METADATA_OPTIMAL}")
    print(f"Wrote {TAXON_CONTRIBUTION_OUTPUT}")
    print(f"Wrote {INPUT_REPORT}")


if __name__ == "__main__":
    main()
