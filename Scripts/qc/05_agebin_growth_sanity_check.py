from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median, mean


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SUBJECT_LEVEL = PROJECT_ROOT / "Suplementary_Data" / "processed_data" / "subject_level_abundance_10_species.csv"
COHORT_AGEBIN = PROJECT_ROOT / "Suplementary_Data" / "processed_data" / "cohort_agebin_median_abundance_10_species.csv"
ALLCOHORT_AGEBIN = PROJECT_ROOT / "Suplementary_Data" / "processed_data" / "allcohort_agebin_median_abundance_10_species.csv"
SCRIPT05_TAXON = PROJECT_ROOT / "Results" / "micom_fba" / "tables" / "05_micom_agebin_taxon_growth_by_diet.csv"
SCRIPT05_SUMMARY = PROJECT_ROOT / "Results" / "micom_fba" / "tables" / "05_micom_agebin_community_growth_summary_by_diet.csv"

OUT_DIR = PROJECT_ROOT / "Results" / "qc" / "tables"

AGE_BIN_ORDER = ["21_40", "41_60", "61_70", "71_80", "81_90", "91_100"]
COHORT_ORDER = ["T2D", "CRE", "SPMP", "SG90"]
SPECIES_ORDER = [
    "Alistipes onderdonkii",
    "Alistipes shahii",
    "Bacteroides dorei",
    "Bacteroides xylanisolvens",
    "Bilophila wadsworthia",
    "Escherichia coli",
    "Faecalibacterium prausnitzii",
    "Klebsiella pneumoniae",
    "Parabacteroides merdae",
    "Ruminococcus torques",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = pos - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def build_per_subject_contribution(subject_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    # Bucket abundance values by (cohort, age_group, species_name) AND by (all_cohort, age_group, species_name).
    buckets: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in subject_rows:
        cohort = row["cohort"]
        age_group = row["age_group"]
        species = row["species_name"]
        abundance = float(row["abundance"])
        buckets[(cohort, age_group, species)].append(abundance)
        buckets[("all_cohort", age_group, species)].append(abundance)

    out_rows: list[dict[str, object]] = []

    age_index = {age: i for i, age in enumerate(AGE_BIN_ORDER)}
    cohort_index = {coh: i for i, coh in enumerate(["all_cohort"] + COHORT_ORDER)}
    species_index = {sp: i for i, sp in enumerate(SPECIES_ORDER)}

    for (cohort, age_group, species), values in buckets.items():
        sorted_vals = sorted(values)
        n_total = len(sorted_vals)
        n_pos = sum(1 for v in sorted_vals if v > 0)
        pct_pos = (n_pos / n_total * 100.0) if n_total else 0.0
        out_rows.append(
            {
                "cohort": cohort,
                "age_group": age_group,
                "species_name": species,
                "n_subjects": n_total,
                "n_positive": n_pos,
                "pct_positive": round(pct_pos, 2),
                "median_abundance": median(sorted_vals) if sorted_vals else 0.0,
                "mean_abundance": mean(sorted_vals) if sorted_vals else 0.0,
                "p25_abundance": percentile(sorted_vals, 0.25),
                "p75_abundance": percentile(sorted_vals, 0.75),
                "max_abundance": max(sorted_vals) if sorted_vals else 0.0,
            }
        )

    out_rows.sort(
        key=lambda r: (
            species_index.get(r["species_name"], 99),
            cohort_index.get(r["cohort"], 99),
            age_index.get(r["age_group"], 99),
        )
    )
    return out_rows


def build_cohort_composition(subject_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    # Distinct subjects per (age_group, cohort).
    seen: set[tuple[str, str, str]] = set()
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in subject_rows:
        key = (row["subject_id"], row["age_group"], row["cohort"])
        if key in seen:
            continue
        seen.add(key)
        counts[(row["age_group"], row["cohort"])] += 1

    age_totals: dict[str, int] = defaultdict(int)
    for (age, coh), n in counts.items():
        age_totals[age] += n

    age_index = {age: i for i, age in enumerate(AGE_BIN_ORDER)}
    cohort_index = {coh: i for i, coh in enumerate(COHORT_ORDER)}

    out_rows: list[dict[str, object]] = []
    for age_group in AGE_BIN_ORDER:
        for cohort in COHORT_ORDER:
            n = counts.get((age_group, cohort), 0)
            total = age_totals.get(age_group, 0)
            frac = (n / total) if total else 0.0
            out_rows.append(
                {
                    "age_group": age_group,
                    "cohort": cohort,
                    "n_subjects": n,
                    "n_subjects_age_bin_total": total,
                    "cohort_fraction_within_age_bin": round(frac, 4),
                }
            )
    return out_rows


def build_plot_inventory(taxon_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    # Every (age_group, diet, species_name) point that appears (or is missing) in the figure.
    present: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in taxon_rows:
        key = (row["age_group"], row["diet_name"], row["species_name"])
        present[key] = row

    out_rows: list[dict[str, object]] = []
    for species in SPECIES_ORDER:
        for diet in ("western", "high_fiber"):
            for age in AGE_BIN_ORDER:
                row = present.get((age, diet, species))
                if row is None:
                    out_rows.append(
                        {
                            "species_name": species,
                            "age_group": age,
                            "diet_name": diet,
                            "median_abundance_input": "",
                            "normalized_weight_input": "",
                            "growth_rate_plotted": "",
                            "is_growing": "",
                            "row_in_05_csv": False,
                            "reason_if_missing": "zero median abundance -> dropped by MICOM Community(taxonomy=...) constructor",
                        }
                    )
                else:
                    out_rows.append(
                        {
                            "species_name": species,
                            "age_group": age,
                            "diet_name": diet,
                            "median_abundance_input": float(row["median_abundance"]),
                            "normalized_weight_input": float(row["normalized_weight"]),
                            "growth_rate_plotted": float(row["growth_rate"]),
                            "is_growing": row["is_growing"],
                            "row_in_05_csv": True,
                            "reason_if_missing": "",
                        }
                    )
    return out_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    subject_rows = read_csv_rows(SUBJECT_LEVEL)
    taxon_rows = read_csv_rows(SCRIPT05_TAXON)

    per_subject = build_per_subject_contribution(subject_rows)
    cohort_comp = build_cohort_composition(subject_rows)
    plot_inv = build_plot_inventory(taxon_rows)

    write_csv(
        OUT_DIR / "sanity_05_per_subject_contribution.csv",
        [
            "cohort",
            "age_group",
            "species_name",
            "n_subjects",
            "n_positive",
            "pct_positive",
            "median_abundance",
            "mean_abundance",
            "p25_abundance",
            "p75_abundance",
            "max_abundance",
        ],
        per_subject,
    )

    write_csv(
        OUT_DIR / "sanity_05_cohort_composition_by_age_bin.csv",
        [
            "age_group",
            "cohort",
            "n_subjects",
            "n_subjects_age_bin_total",
            "cohort_fraction_within_age_bin",
        ],
        cohort_comp,
    )

    write_csv(
        OUT_DIR / "sanity_05_plot_inventory.csv",
        [
            "species_name",
            "age_group",
            "diet_name",
            "median_abundance_input",
            "normalized_weight_input",
            "growth_rate_plotted",
            "is_growing",
            "row_in_05_csv",
            "reason_if_missing",
        ],
        plot_inv,
    )

    print(f"Wrote {OUT_DIR / 'sanity_05_per_subject_contribution.csv'} ({len(per_subject)} rows)")
    print(f"Wrote {OUT_DIR / 'sanity_05_cohort_composition_by_age_bin.csv'} ({len(cohort_comp)} rows)")
    print(f"Wrote {OUT_DIR / 'sanity_05_plot_inventory.csv'} ({len(plot_inv)} rows)")


if __name__ == "__main__":
    main()
