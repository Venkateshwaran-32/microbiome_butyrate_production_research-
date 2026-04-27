# Repairing AGORA2 SBML Files

This note documents the fix that was needed to make the VMH AGORA2 SBML files load in COBRApy for this project.

## Problem

Several files in:

- `Models/vmh_agora2_sbml/`

could not be loaded with:

- `cobra.io.read_sbml_model(...)`

COBRApy raised an SBML parse error because some XML files declared:

- `encoding="UTF-8"`

but actually contained invalid raw bytes that broke XML parsing.

Example symptom:

- `CobraSBMLError`
- `No SBML model detected in file`

Example failing file:

- `Models/vmh_agora2_sbml/Faecalibacterium_prausnitzii_M21_2.xml`

Example root cause:

- invalid bytes such as `0xDF`, `0xA0`, `0xE8` appeared inside XML text or attributes
- this made `libSBML` reject the file before COBRApy could construct the model

## What Was Fixed

A repair script was added:

- [repair_agora2_sbml_encoding.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/exploration/repair_agora2_sbml_encoding.py)

The script repairs malformed AGORA2 XML files into valid UTF-8.

### Repair logic

For each XML file:

1. read the file as raw bytes
2. try normal UTF-8 decoding
3. if decoding fails, decode with `surrogateescape`
4. convert invalid preserved bytes through `cp1252`
5. replace non-breaking spaces (`U+00A0`) with regular spaces
6. replace any remaining invalid XML characters with `U+FFFD`
7. write the repaired file back as valid UTF-8

The script only rewrites files that actually change.

## Backup Location

Before overwriting repaired files, the original versions were backed up to:

- `/tmp/agora2_sbml_backup/`

## Files Repaired

The following AGORA2 files were repaired:

- `Alistipes_shahii_WAL_8301.xml`
- `Bacteroides_dorei_DSM_17855.xml`
- `Bacteroides_xylanisolvens_XB1A.xml`
- `Escherichia_coli_UTI89_UPEC.xml`
- `Faecalibacterium_prausnitzii_M21_2.xml`
- `Parabacteroides_merdae_ATCC_43184.xml`

The remaining project AGORA2 files were already valid UTF-8 and were left unchanged.

## How To Re-run The Repair

From the project root:

```bash
python Scripts/exploration/repair_agora2_sbml_encoding.py
```

Optional custom target directory:

```bash
python Scripts/exploration/repair_agora2_sbml_encoding.py Models/vmh_agora2_sbml
```

Optional custom backup directory:

```bash
python Scripts/exploration/repair_agora2_sbml_encoding.py Models/vmh_agora2_sbml --backup-dir /tmp/agora2_sbml_backup
```

## How To Verify

### 1. Validate all AGORA2 project models

```bash
python - <<'PY'
from pathlib import Path
from cobra.io import read_sbml_model, validate_sbml_model

base = Path("Models/vmh_agora2_sbml")
for path in sorted(base.glob("*.xml")):
    model, errors = validate_sbml_model(str(path))
    total = sum(len(v) for v in errors.values())
    if total:
        print(path.name, "FAILED", total)
    else:
        loaded = read_sbml_model(str(path))
        print(path.name, "OK", loaded.id)
PY
```

### 2. Run the COBRApy learning script

```bash
python Scripts/exploration/learn_cobrapy_sbml.py
```

After the repair, the learning script should load:

- `Models/vmh_agora2_sbml/Faecalibacterium_prausnitzii_M21_2.xml`

and return an optimal solution instead of crashing.

## Related Script Change

The learning script was also updated to better fit AGORA2:

- [learn_cobrapy_sbml.py](/Users/taknev/Desktop/microbiome_butyrate_production_research/Scripts/exploration/learn_cobrapy_sbml.py)

Changes:

- uses `Models/vmh_agora2_sbml/...` instead of AGORA1.03
- finds the objective reaction dynamically instead of hardcoding an AGORA1.03 biomass ID

## Current Status

Current state after the repair:

- all 10 project files in `Models/vmh_agora2_sbml/` are valid UTF-8
- all 10 validate and load in COBRApy
- `learn_cobrapy_sbml.py` runs successfully on AGORA2
