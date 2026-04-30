from __future__ import annotations

import csv
import importlib.util
import math
from collections import Counter, defaultdict
from pathlib import Path


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


COMMUNITY_INPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_community_growth_summary_by_diet.csv")
TAXON_INPUT = Path("Results/subject_level_fba/tables/06_sg90_subject_taxon_growth_by_diet.csv")
QC_INPUT = Path("Suplementary_Data/processed_data/subject_level_micom_sg90/sg90_subject_input_qc_summary.csv")
BUILD_REPORT_INPUT = Path("Results/subject_level_fba/reports/06_sg90_subject_level_micom_build_report.txt")
FLAGGED_OUTPUT = Path("Results/subject_level_fba/tables/06c_sg90_subject_abnormality_review.csv")
REPORT_OUTPUT = Path("Results/subject_level_fba/reports/06c_sg90_subject_abnormality_review.txt")
FLAGGED_FIELDNAMES = [
    "subject_id",
    "age_group",
    "diets_affected",
    "flag_category",
    "evidence_values",
    "driver_pattern",
    "short_interpretation",
    "overall_assessment",
]

EXPECTED_SUBJECTS = 215
EXPECTED_ROWS = 430
SPARSE_INPUT_THRESHOLD = 2
LOW_GROWING_TAXA_THRESHOLD = 2
NEGATIVE_OBJECTIVE_TOLERANCE = -1e-9
DOMINANCE_THRESHOLD = 0.9
ROUND_DIGITS = 12
CSV_OUTPUT_SPECS = [
    csv_output_spec(
        FLAGGED_OUTPUT,
        "one row per flagged SG90 subject",
        [
            col("subject_id", "Subject identifier from the SG90 subject-level MICOM run."),
            col("age_group", "Age-bin label assigned from the subject metadata."),
            col("diets_affected", "Comma-separated list of diets whose outputs contributed to the abnormality flag."),
            col("flag_category", "Semicolon-separated list of abnormality categories assigned to this subject."),
            col("evidence_values", "Compact evidence string summarizing the key numeric values that triggered the flags."),
            col("driver_pattern", "Diet-specific summary labels describing whether the subject showed sparse, broad, or dominant taxon-growth structure."),
            col("short_interpretation", "Plain-English interpretation combining the flagged evidence and driver summaries."),
            col(
                "overall_assessment",
                "Top-level review classification for the flagged subject.",
                "overall_assessment is assigned from the flag combination: technical issue takes precedence, then sparse-but-valid case, then biologically interesting outlier",
            ),
        ],
    )
]


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


def safe_float(value: str) -> float:
    if value == "":
        return math.nan
    return float(value)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def parse_build_report(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {
            "Selected subjects for this run",
            "Included subjects with abundance rows",
            "Excluded subjects",
            "Subjects missing from abundance workbook",
            "Total SG90 subjects in QC table",
        }:
            values[key] = int(value)
    return values


def iqr_thresholds(values: list[float]) -> tuple[float, float, float, float]:
    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    iqr = q3 - q1
    return q1, q3, q1 - 1.5 * iqr, q3 + 1.5 * iqr


def summarize_driver(subject_taxa: list[dict[str, object]]) -> tuple[str, str]:
    growing_rows = [row for row in subject_taxa if row["growth_rate"] > 0]
    if not growing_rows:
        return "no_growth", "No taxa achieved positive growth in the exported taxon table."

    sorted_rows = sorted(growing_rows, key=lambda row: (-row["growth_rate"], row["taxon_id"]))
    total_growth = sum(row["growth_rate"] for row in growing_rows)
    top_row = sorted_rows[0]
    top_share = top_row["growth_rate"] / total_growth if total_growth > 0 else 0.0

    if len(growing_rows) <= 2:
        return (
            "very_sparse_growth",
            f"Only {len(growing_rows)} taxa grew; top grower {top_row['species_name']} contributed {top_share:.1%} of total taxon growth.",
        )
    if top_share >= DOMINANCE_THRESHOLD:
        return (
            "one_taxon_dominance",
            f"Top grower {top_row['species_name']} contributed {top_share:.1%} of total taxon growth.",
        )
    if len(growing_rows) >= 7:
        return (
            "broad_growth",
            f"{len(growing_rows)} taxa grew; top grower {top_row['species_name']} contributed {top_share:.1%} of total taxon growth.",
        )
    return (
        "moderately_sparse_growth",
        f"{len(growing_rows)} taxa grew; top grower {top_row['species_name']} contributed {top_share:.1%} of total taxon growth.",
    )


def main() -> None:
    community_rows = load_csv_rows(COMMUNITY_INPUT)
    taxon_rows = load_csv_rows(TAXON_INPUT)
    qc_rows = load_csv_rows(QC_INPUT)
    build_report_counts = parse_build_report(BUILD_REPORT_INPUT)

    if len(community_rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} subject-diet rows, found {len(community_rows)}")

    community_by_subject: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    solver_status_counts: Counter[str] = Counter()
    for row in community_rows:
        parsed = {
            **row,
            "age_years": safe_float(row["age_years"]),
            "community_growth_rate": safe_float(row["community_growth_rate"]),
            "objective_value": safe_float(row["objective_value"]),
            "tradeoff_fraction": safe_float(row["tradeoff_fraction"]),
            "num_taxa_total": int(row["num_taxa_total"]),
            "num_taxa_with_nonzero_growth": int(row["num_taxa_with_nonzero_growth"]),
            "matched_diet_metabolites": int(row["matched_diet_metabolites"]),
            "missing_diet_metabolites": int(row["missing_diet_metabolites"]),
            "total_input_abundance_raw": safe_float(row["total_input_abundance_raw"]),
            "total_input_abundance_normalized": safe_float(row["total_input_abundance_normalized"]),
        }
        community_by_subject[row["subject_id"]][row["diet_name"]] = parsed
        solver_status_counts[row["solver_status"]] += 1

    if set(solver_status_counts) != {"optimal"}:
        raise ValueError(f"Unexpected solver statuses detected: {dict(solver_status_counts)}")

    subject_ids = sorted(community_by_subject)
    if len(subject_ids) != EXPECTED_SUBJECTS:
        raise ValueError(f"Expected {EXPECTED_SUBJECTS} subjects, found {len(subject_ids)}")
    if build_report_counts.get("Selected subjects for this run") != EXPECTED_SUBJECTS:
        raise ValueError(
            "Build report selected subject count does not match expected count: "
            f"{build_report_counts.get('Selected subjects for this run')}"
        )

    qc_by_subject: dict[str, dict[str, object]] = {}
    for row in qc_rows:
        qc_by_subject[row["subject_id"]] = {
            **row,
            "age_years": safe_float(row["age_years"]) if row["age_years"] else math.nan,
            "has_abundance_workbook_row": row["has_abundance_workbook_row"] == "True",
            "include_in_subject_micom": row["include_in_subject_micom"] == "True",
            "n_modeled_taxa_total": int(row["n_modeled_taxa_total"]) if row["n_modeled_taxa_total"] else 0,
            "n_nonzero_modeled_taxa": int(row["n_nonzero_modeled_taxa"]) if row["n_nonzero_modeled_taxa"] else 0,
            "total_modeled_abundance_raw": safe_float(row["total_modeled_abundance_raw"]) if row["total_modeled_abundance_raw"] else 0.0,
            "total_modeled_abundance_normalized": safe_float(row["total_modeled_abundance_normalized"]) if row["total_modeled_abundance_normalized"] else 0.0,
        }

    taxon_by_subject_diet: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in taxon_rows:
        parsed = {
            **row,
            "age_years": safe_float(row["age_years"]),
            "abundance_raw": safe_float(row["abundance_raw"]),
            "abundance_normalized": safe_float(row["abundance_normalized"]),
            "growth_rate": safe_float(row["growth_rate"]),
            "is_growing": row["is_growing"] == "True",
            "reactions": int(row["reactions"]) if row["reactions"] else 0,
            "metabolites": int(row["metabolites"]) if row["metabolites"] else 0,
        }
        taxon_by_subject_diet[(row["subject_id"], row["diet_name"])].append(parsed)

    per_diet_growth_thresholds: dict[str, tuple[float, float, float, float]] = {}
    per_diet_matched_thresholds: dict[str, tuple[float, float, float, float]] = {}
    for diet_name in sorted({row["diet_name"] for row in community_rows}):
        growth_values = [
            community_by_subject[subject_id][diet_name]["community_growth_rate"]
            for subject_id in subject_ids
        ]
        matched_values = [
            float(community_by_subject[subject_id][diet_name]["matched_diet_metabolites"])
            for subject_id in subject_ids
        ]
        per_diet_growth_thresholds[diet_name] = iqr_thresholds(growth_values)
        per_diet_matched_thresholds[diet_name] = iqr_thresholds(matched_values)

    duplicate_signature_groups: dict[tuple[object, ...], list[str]] = defaultdict(list)
    for subject_id in subject_ids:
        qc_row = qc_by_subject[subject_id]
        west = community_by_subject[subject_id]["western"]
        fiber = community_by_subject[subject_id]["high_fiber"]
        signature = (
            round(west["community_growth_rate"], ROUND_DIGITS),
            round(fiber["community_growth_rate"], ROUND_DIGITS),
            west["matched_diet_metabolites"],
            fiber["matched_diet_metabolites"],
            qc_row["n_nonzero_modeled_taxa"],
        )
        duplicate_signature_groups[signature].append(subject_id)

    flagged_rows: list[dict[str, object]] = []
    category_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()

    for subject_id in subject_ids:
        qc_row = qc_by_subject[subject_id]
        west = community_by_subject[subject_id]["western"]
        fiber = community_by_subject[subject_id]["high_fiber"]
        flags: list[str] = []
        evidence_parts: list[str] = []
        interpretation_parts: list[str] = []
        diets_affected: list[str] = []
        severity = 0

        negative_objective_diets = [
            diet_name
            for diet_name, row in (("western", west), ("high_fiber", fiber))
            if row["objective_value"] < NEGATIVE_OBJECTIVE_TOLERANCE and row["community_growth_rate"] > 0
        ]
        if negative_objective_diets:
            flags.append("reporting/solver artifact")
            category_counts["reporting/solver artifact"] += 1
            diets_affected.extend(negative_objective_diets)
            severity += 3
            evidence_parts.append(
                "negative objective on "
                + ", ".join(
                    f"{diet} ({community_by_subject[subject_id][diet]['objective_value']:.6f})"
                    for diet in negative_objective_diets
                )
            )
            interpretation_parts.append(
                "MICOM reported positive community growth with a negative objective value, which looks more like a solver/reporting artifact than a failed biological solution."
            )

        if qc_row["n_nonzero_modeled_taxa"] <= SPARSE_INPUT_THRESHOLD:
            flags.append("sparse-input subject")
            category_counts["sparse-input subject"] += 1
            diets_affected.extend(["western", "high_fiber"])
            severity += 2
            evidence_parts.append(
                f"only {qc_row['n_nonzero_modeled_taxa']} nonzero modeled input taxa; total raw modeled abundance={qc_row['total_modeled_abundance_raw']:.6f}"
            )
            interpretation_parts.append(
                "This subject is structurally sparse at the input stage, so MICOM outputs are brittle and should be treated as sparse-but-valid unless other technical problems appear."
            )

        low_match_diets: list[str] = []
        for diet_name, row in (("western", west), ("high_fiber", fiber)):
            _, _, low_match_threshold, _ = per_diet_matched_thresholds[diet_name]
            if row["matched_diet_metabolites"] < low_match_threshold:
                low_match_diets.append(diet_name)
        if low_match_diets:
            flags.append("poor diet-medium coverage")
            category_counts["poor diet-medium coverage"] += 1
            diets_affected.extend(low_match_diets)
            severity += 2
            evidence_parts.append(
                "low medium matching on "
                + ", ".join(
                    f"{diet} ({community_by_subject[subject_id][diet]['matched_diet_metabolites']} matched, {community_by_subject[subject_id][diet]['missing_diet_metabolites']} missing)"
                    for diet in low_match_diets
                )
            )
            interpretation_parts.append(
                "A relatively large share of diet metabolites could not be mapped into the subject-specific community exchanges, so these outputs are less comparable to the cohort median subject."
            )

        low_growth_diets: list[str] = []
        high_growth_diets: list[str] = []
        for diet_name, row in (("western", west), ("high_fiber", fiber)):
            _, _, low_growth_threshold, high_growth_threshold = per_diet_growth_thresholds[diet_name]
            if row["community_growth_rate"] < low_growth_threshold:
                low_growth_diets.append(diet_name)
            if row["community_growth_rate"] > high_growth_threshold:
                high_growth_diets.append(diet_name)

        if low_growth_diets:
            flags.append("extreme low-growth outlier")
            category_counts["extreme low-growth outlier"] += 1
            diets_affected.extend(low_growth_diets)
            severity += 1
            evidence_parts.append(
                "low growth on "
                + ", ".join(
                    f"{diet} ({community_by_subject[subject_id][diet]['community_growth_rate']:.6f})"
                    for diet in low_growth_diets
                )
            )
            interpretation_parts.append(
                "Community growth sits below the robust lower-tail cohort threshold for at least one diet."
            )

        if high_growth_diets:
            flags.append("extreme high-growth outlier")
            category_counts["extreme high-growth outlier"] += 1
            diets_affected.extend(high_growth_diets)
            severity += 1
            evidence_parts.append(
                "high growth on "
                + ", ".join(
                    f"{diet} ({community_by_subject[subject_id][diet]['community_growth_rate']:.6f})"
                    for diet in high_growth_diets
                )
            )
            interpretation_parts.append(
                "Community growth sits above the robust upper-tail cohort threshold for at least one diet."
            )

        if (
            fiber["community_growth_rate"] > west["community_growth_rate"] + 1e-12
            and fiber["solver_status"] == "optimal"
            and west["solver_status"] == "optimal"
        ):
            flags.append("unusual diet-response pattern")
            category_counts["unusual diet-response pattern"] += 1
            diets_affected.extend(["western", "high_fiber"])
            severity += 1
            evidence_parts.append(
                f"high_fiber growth ({fiber['community_growth_rate']:.6f}) exceeded western growth ({west['community_growth_rate']:.6f})"
            )
            interpretation_parts.append(
                "This is rare in the current SG90 run and deserves review as a subject-specific diet-response deviation."
            )

        low_growing_taxa_diets = [
            diet_name
            for diet_name, row in (("western", west), ("high_fiber", fiber))
            if row["num_taxa_with_nonzero_growth"] <= LOW_GROWING_TAXA_THRESHOLD
        ]
        if low_growing_taxa_diets:
            evidence_parts.append(
                "very few growing taxa on "
                + ", ".join(
                    f"{diet} ({community_by_subject[subject_id][diet]['num_taxa_with_nonzero_growth']} taxa)"
                    for diet in low_growing_taxa_diets
                )
            )

        duplicate_group = []
        if qc_row["n_nonzero_modeled_taxa"] <= SPARSE_INPUT_THRESHOLD:
            signature = (
                round(west["community_growth_rate"], ROUND_DIGITS),
                round(fiber["community_growth_rate"], ROUND_DIGITS),
                west["matched_diet_metabolites"],
                fiber["matched_diet_metabolites"],
                qc_row["n_nonzero_modeled_taxa"],
            )
            duplicate_group = sorted(duplicate_signature_groups[signature])
            if len(duplicate_group) > 1:
                evidence_parts.append(
                    f"duplicate-looking sparse profile shared with {', '.join(other for other in duplicate_group if other != subject_id)}"
                )
                interpretation_parts.append(
                    "The repeated profile likely reflects very similar sparse subject inputs rather than a separate solver crash, but it should still be audited."
                )

        if not flags:
            continue

        driver_labels: list[str] = []
        driver_texts: list[str] = []
        for diet_name in ("western", "high_fiber"):
            driver_label, driver_text = summarize_driver(taxon_by_subject_diet[(subject_id, diet_name)])
            driver_labels.append(f"{diet_name}:{driver_label}")
            driver_texts.append(f"{diet_name}: {driver_text}")

        technical_flag = any(
            flag in {"reporting/solver artifact", "poor diet-medium coverage"} for flag in flags
        )
        sparse_flag = "sparse-input subject" in flags
        biological_flag = any(
            flag in {"extreme low-growth outlier", "extreme high-growth outlier", "unusual diet-response pattern"}
            for flag in flags
        )
        if technical_flag:
            overall_classification = "technical issue"
        elif sparse_flag and not biological_flag:
            overall_classification = "sparse-but-valid case"
        elif biological_flag:
            overall_classification = "biologically interesting outlier"
        else:
            overall_classification = "sparse-but-valid case"
        classification_counts[overall_classification] += 1

        unique_diets = sorted(set(diets_affected), key=lambda value: ("western", "high_fiber").index(value))
        flagged_rows.append(
            {
                "rank_score": severity,
                "subject_id": subject_id,
                "age_group": west["age_group"],
                "diets_affected": ",".join(unique_diets),
                "flag_category": "; ".join(flags),
                "evidence_values": " | ".join(evidence_parts),
                "driver_pattern": " | ".join(driver_labels),
                "short_interpretation": " ".join(interpretation_parts + driver_texts),
                "overall_assessment": overall_classification,
            }
        )

    flagged_rows.sort(
        key=lambda row: (
            -int(row["rank_score"]),
            row["overall_assessment"],
            row["subject_id"],
        )
    )

    output_rows = [
        {
            "subject_id": row["subject_id"],
            "age_group": row["age_group"],
            "diets_affected": row["diets_affected"],
            "flag_category": row["flag_category"],
            "evidence_values": row["evidence_values"],
            "driver_pattern": row["driver_pattern"],
            "short_interpretation": row["short_interpretation"],
            "overall_assessment": row["overall_assessment"],
        }
        for row in flagged_rows
    ]

    write_csv(
        FLAGGED_OUTPUT,
        FLAGGED_FIELDNAMES,
        output_rows,
    )

    report_lines = [
        "SG90 subject-level MICOM abnormality review",
        f"Community input: {COMMUNITY_INPUT}",
        f"Taxon input: {TAXON_INPUT}",
        f"QC input: {QC_INPUT}",
        f"Build report input: {BUILD_REPORT_INPUT}",
        "",
        "Validation checks",
        f"- expected subjects: {EXPECTED_SUBJECTS}",
        f"- observed subjects: {len(subject_ids)}",
        f"- expected subject-diet rows: {EXPECTED_ROWS}",
        f"- observed subject-diet rows: {len(community_rows)}",
        f"- solver status counts: {dict(solver_status_counts)}",
        f"- build report selected subjects: {build_report_counts.get('Selected subjects for this run')}",
        "",
        "Per-diet thresholds",
    ]

    for diet_name in ("western", "high_fiber"):
        g_q1, g_q3, g_low, g_high = per_diet_growth_thresholds[diet_name]
        m_q1, m_q3, m_low, _ = per_diet_matched_thresholds[diet_name]
        report_lines.append(
            f"- {diet_name}: growth q1={g_q1:.6f}, q3={g_q3:.6f}, low_outlier<{g_low:.6f}, high_outlier>{g_high:.6f}"
        )
        report_lines.append(
            f"- {diet_name}: matched metabolites q1={m_q1:.2f}, q3={m_q3:.2f}, low_outlier<{m_low:.2f}"
        )

    report_lines.extend(
        [
            "",
            "Flag counts",
            f"- flagged subjects total: {len(output_rows)}",
            *[f"- {category}: {count}" for category, count in sorted(category_counts.items())],
            "",
            "Overall assessment counts",
            *[f"- {category}: {count}" for category, count in sorted(classification_counts.items())],
            "",
            "Flagged subjects",
        ]
    )

    for row in output_rows:
        report_lines.append(
            f"- {row['subject_id']} [{row['age_group']}] {row['overall_assessment']} | {row['flag_category']} | {row['evidence_values']}"
        )

    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(build_report_text(report_lines, CSV_OUTPUT_SPECS))

    print(f"Wrote {FLAGGED_OUTPUT}")
    print(f"Wrote {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
