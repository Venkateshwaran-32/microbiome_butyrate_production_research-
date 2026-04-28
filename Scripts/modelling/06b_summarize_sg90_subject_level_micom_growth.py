from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


COMMUNITY_INPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_community_growth_summary_by_diet.csv")
TAXON_INPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet.csv")
TOP_GROWER_OUTPUT = Path("Results/subject_level_fba/tables/06b_sg90_subject_top_grower_summary.csv")
GROWTH_SUMMARY_OUTPUT = Path("Results/subject_level_fba/tables/06b_sg90_subject_growth_summary_by_agegroup.csv")
PREVALENCE_OUTPUT = Path("Results/subject_level_fba/tables/06b_sg90_subject_species_prevalence_by_agegroup.csv")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    community_rows = list(csv.DictReader(open(COMMUNITY_INPUT, newline="")))
    taxon_rows = list(csv.DictReader(open(TAXON_INPUT, newline="")))

    successful_community_rows = [
        row for row in community_rows if row["solver_status"] == "optimal"
    ]
    solved_subject_diets = {(row["subject_id"], row["diet_name"]) for row in successful_community_rows}
    successful_taxon_rows = [
        row for row in taxon_rows if (row["subject_id"], row["diet_name"]) in solved_subject_diets
    ]

    top_grower_rows: list[dict[str, object]] = []
    by_subject_and_diet: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in successful_taxon_rows:
        by_subject_and_diet[(row["subject_id"], row["diet_name"])].append(row)

    for (subject_id, diet_name), rows in sorted(by_subject_and_diet.items()):
        top_row = max(
            rows,
            key=lambda row: (
                float(row["growth_rate"]),
                float(row["abundance_normalized"]),
                row["taxon_id"],
            ),
        )
        top_grower_rows.append(
            {
                "subject_id": subject_id,
                "cohort": top_row["cohort"],
                "age_years": top_row["age_years"],
                "age_group": top_row["age_group"],
                "diet_name": diet_name,
                "top_taxon_id": top_row["taxon_id"],
                "top_species_name": top_row["species_name"],
                "top_paper_taxon": top_row["paper_taxon"],
                "top_growth_rate": top_row["growth_rate"],
                "top_abundance_raw": top_row["abundance_raw"],
                "top_abundance_normalized": top_row["abundance_normalized"],
            }
        )

    growth_summary_rows: list[dict[str, object]] = []
    by_age_group_and_diet: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in successful_community_rows:
        key = (row["age_group"], row["diet_name"])
        by_age_group_and_diet[key].append(float(row["community_growth_rate"]))

    for (age_group, diet_name), values in sorted(by_age_group_and_diet.items()):
        growth_summary_rows.append(
            {
                "age_group": age_group,
                "diet_name": diet_name,
                "n_subjects": len(values),
                "community_growth_rate_mean": mean(values),
                "community_growth_rate_median": percentile(values, 0.5),
                "community_growth_rate_q1": percentile(values, 0.25),
                "community_growth_rate_q3": percentile(values, 0.75),
                "community_growth_rate_min": min(values),
                "community_growth_rate_max": max(values),
            }
        )

    prevalence_rows: list[dict[str, object]] = []
    by_age_group_diet_taxon: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in successful_taxon_rows:
        key = (row["age_group"], row["diet_name"], row["taxon_id"])
        by_age_group_diet_taxon[key].append(row)

    for (age_group, diet_name, taxon_id), rows in sorted(by_age_group_diet_taxon.items()):
        growth_values = [float(row["growth_rate"]) for row in rows]
        n_subjects_total = len(rows)
        n_subjects_growing = sum(row["is_growing"] == "True" for row in rows)
        prevalence_rows.append(
            {
                "age_group": age_group,
                "diet_name": diet_name,
                "taxon_id": taxon_id,
                "species_name": rows[0]["species_name"],
                "paper_taxon": rows[0]["paper_taxon"],
                "n_subjects_total": n_subjects_total,
                "n_subjects_growing": n_subjects_growing,
                "growth_prevalence_fraction": n_subjects_growing / n_subjects_total if n_subjects_total else 0.0,
                "mean_growth_rate": mean(growth_values),
                "median_growth_rate": percentile(growth_values, 0.5),
            }
        )

    write_csv(
        TOP_GROWER_OUTPUT,
        [
            "subject_id",
            "cohort",
            "age_years",
            "age_group",
            "diet_name",
            "top_taxon_id",
            "top_species_name",
            "top_paper_taxon",
            "top_growth_rate",
            "top_abundance_raw",
            "top_abundance_normalized",
        ],
        top_grower_rows,
    )
    write_csv(
        GROWTH_SUMMARY_OUTPUT,
        [
            "age_group",
            "diet_name",
            "n_subjects",
            "community_growth_rate_mean",
            "community_growth_rate_median",
            "community_growth_rate_q1",
            "community_growth_rate_q3",
            "community_growth_rate_min",
            "community_growth_rate_max",
        ],
        growth_summary_rows,
    )
    write_csv(
        PREVALENCE_OUTPUT,
        [
            "age_group",
            "diet_name",
            "taxon_id",
            "species_name",
            "paper_taxon",
            "n_subjects_total",
            "n_subjects_growing",
            "growth_prevalence_fraction",
            "mean_growth_rate",
            "median_growth_rate",
        ],
        prevalence_rows,
    )

    print(f"Wrote {TOP_GROWER_OUTPUT}")
    print(f"Wrote {GROWTH_SUMMARY_OUTPUT}")
    print(f"Wrote {PREVALENCE_OUTPUT}")


if __name__ == "__main__":
    main()
