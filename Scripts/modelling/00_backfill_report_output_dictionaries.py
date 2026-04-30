from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable


SCRIPT_DIR = Path(__file__).resolve().parent

REPORT_UTILS_PATH = SCRIPT_DIR / "00_report_output_dictionary.py"
REPORT_UTILS_SPEC = importlib.util.spec_from_file_location("report_output_dictionary", REPORT_UTILS_PATH)
if REPORT_UTILS_SPEC is None or REPORT_UTILS_SPEC.loader is None:
    raise ImportError(f"Could not load report utility module from {REPORT_UTILS_PATH}")
REPORT_UTILS_MODULE = importlib.util.module_from_spec(REPORT_UTILS_SPEC)
REPORT_UTILS_SPEC.loader.exec_module(REPORT_UTILS_MODULE)

append_csv_output_dictionary_to_text = REPORT_UTILS_MODULE.append_csv_output_dictionary_to_text


def load_module(module_name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def specs_03(module) -> list[dict[str, object]]:
    return module.build_csv_output_specs(sorted(module.load_agebin_table(module.AGEBIN_INPUT)))


def specs_05(module) -> list[dict[str, object]]:
    return module.build_csv_output_specs(sorted(module.load_agebin_table(module.AGEBIN_INPUT)))


def specs_06(module) -> list[dict[str, object]]:
    return module.build_csv_output_specs(module.target_model_species_ids_in_order())


def module_specs(module) -> list[dict[str, object]]:
    return module.CSV_OUTPUT_SPECS


REPORT_TARGETS: list[tuple[str, str, Callable, str]] = [
    ("02", "02_community_shared_environment.py", module_specs, "BUILD_REPORT"),
    ("03", "03_agebin_weighted_community.py", specs_03, "BUILD_REPORT"),
    ("04", "04_micom_baseline_community.py", module_specs, "BUILD_REPORT"),
    ("05", "05_micom_agebin_weighted_community.py", specs_05, "BUILD_REPORT"),
    ("06", "06_micom_subject_level_sg90.py", specs_06, "BUILD_REPORT"),
    ("06c", "06c_review_sg90_subject_level_micom_abnormalities.py", module_specs, "REPORT_OUTPUT"),
    ("08", "08_micom_allcohort_subject_level_high_fiber_pfba.py", module_specs, "BUILD_REPORT"),
    ("09", "09_prepare_allcohort_high_fiber_reaction_pca_inputs.py", module_specs, "INPUT_REPORT"),
]


def main() -> None:
    for label, filename, spec_builder, report_attr in REPORT_TARGETS:
        module = load_module(f"report_module_{label}", filename)
        report_path = Path(getattr(module, report_attr))
        specs = spec_builder(module)
        existing_text = report_path.read_text() if report_path.exists() else ""
        report_path.write_text(append_csv_output_dictionary_to_text(existing_text, specs))
        print(f"Refreshed {report_path}")


if __name__ == "__main__":
    main()
