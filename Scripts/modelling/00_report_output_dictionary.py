from __future__ import annotations

import csv
import textwrap
from pathlib import Path
from typing import Any


SECTION_TITLE = "CSV Output Dictionary"
WRAP_WIDTH = 100


def col(name: str, meaning: str, formula: str | None = None) -> dict[str, str]:
    entry = {"name": name, "meaning": meaning}
    if formula:
        entry["formula"] = formula
    return entry


def dynamic_tail(label: str, meaning: str, formula: str | None = None) -> dict[str, str]:
    entry = {"label": label, "meaning": meaning}
    if formula:
        entry["formula"] = formula
    return entry


def csv_output_spec(
    path: str | Path,
    row_grain: str,
    columns: list[dict[str, str]],
    dynamic_columns: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "path": Path(path),
        "row_grain": row_grain,
        "columns": columns,
        "dynamic_columns": dynamic_columns,
    }


def read_csv_header(path: str | Path) -> list[str]:
    with open(path, newline="") as handle:
        return next(csv.reader(handle))


def _wrap_line(prefix: str, text: str) -> list[str]:
    wrapped = textwrap.wrap(
        text,
        width=WRAP_WIDTH,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped or [prefix.rstrip()]


def _validate_and_get_header(spec: dict[str, Any]) -> list[str]:
    path = Path(spec["path"])
    actual_header = read_csv_header(path)
    fixed_header = [entry["name"] for entry in spec["columns"]]

    if spec.get("dynamic_columns") is None:
        if actual_header != fixed_header:
            raise ValueError(
                f"Header mismatch for {path}. Expected {fixed_header}, found {actual_header}"
            )
    else:
        prefix = actual_header[: len(fixed_header)]
        if prefix != fixed_header:
            raise ValueError(
                f"Header prefix mismatch for {path}. Expected {fixed_header}, found {actual_header}"
            )
        if len(actual_header) <= len(fixed_header):
            raise ValueError(
                f"Expected dynamic columns after fixed prefix {fixed_header} in {path}, found none."
            )

    return actual_header


def render_csv_output_dictionary(specs: list[dict[str, Any]]) -> str:
    lines = [SECTION_TITLE, ""]

    for index, spec in enumerate(specs):
        path = Path(spec["path"])
        header = _validate_and_get_header(spec)

        lines.append(path.name)
        lines.append(f"Path: {path}")
        lines.append(f"Row grain: {spec['row_grain']}")
        lines.append("Columns:")

        for entry in spec["columns"]:
            text = f"{entry['name']}: {entry['meaning']}"
            if entry.get("formula"):
                text += f" Formula: {entry['formula']}"
            lines.extend(_wrap_line("- ", text))

        dynamic_spec = spec.get("dynamic_columns")
        if dynamic_spec is not None:
            dynamic_names = header[len(spec["columns"]) :]
            text = (
                f"{dynamic_spec['label']} ({len(dynamic_names)} total): {dynamic_spec['meaning']} "
                f"Exact column names: {', '.join(dynamic_names)}"
            )
            if dynamic_spec.get("formula"):
                text += f" Formula: {dynamic_spec['formula']}"
            lines.extend(_wrap_line("- ", text))

        if index != len(specs) - 1:
            lines.append("")

    return "\n".join(lines)


def strip_existing_csv_output_dictionary(report_text: str) -> str:
    stripped = report_text.rstrip()
    if stripped == SECTION_TITLE:
        return ""

    marker = f"\n{SECTION_TITLE}\n"
    position = stripped.find(marker)
    if position != -1:
        return stripped[:position].rstrip()

    if stripped.startswith(f"{SECTION_TITLE}\n"):
        return ""

    return stripped


def append_csv_output_dictionary_to_text(report_text: str, specs: list[dict[str, Any]]) -> str:
    base_text = strip_existing_csv_output_dictionary(report_text)
    dictionary_text = render_csv_output_dictionary(specs)
    if base_text:
        return f"{base_text}\n\n{dictionary_text}\n"
    return f"{dictionary_text}\n"


def build_report_text(report_lines: list[str], specs: list[dict[str, Any]]) -> str:
    return append_csv_output_dictionary_to_text("\n".join(report_lines), specs)
