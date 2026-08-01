"""wikimolgen.validation - Source data validation and cross-source consistency.

Pure functions with no I/O and no Streamlit dependency.  Every validator
returns a ``bool`` (or a list of violation tuples) so callers can log and
continue without breaking enrichment.

Covered checks
--------------
* Identifier formats: CAS (with checksum), UNII, InChI/InChIKey, ChEBI,
  ChEMBL, KEGG, MeSH, ChemSpider, ATC, SPL setid (UUID).
* Numeric sanity ranges for experimental physical properties.
* Cross-source consistency: molecular formula and molecular weight
  against the RDKit ground truth computed from the molecule itself.
"""

from __future__ import annotations

import re
from typing import Any

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors as _rdMolDescriptors
except ImportError:  # pragma: no cover - rdkit is a hard dependency, but keep import light
    Chem = None  # type: ignore[assignment]
    _rdMolDescriptors = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Identifier format validators
# ---------------------------------------------------------------------------


def is_valid_cas(cas: str) -> bool:
    """Validate a CAS Registry Number (format + checksum).

    Format: ``NNNNNN-NN-N``.  The check digit is the last digit; it equals
    ``sum(digit * position_from_right) mod 10`` over the body digits.
    """
    if not isinstance(cas, str):
        return False
    m = re.fullmatch(r"(\d{1,7})-(\d{2})-(\d)", cas.strip())
    if not m:
        return False
    body = m.group(1) + m.group(2)
    check = int(m.group(3))
    total = sum((i + 1) * int(d) for i, d in enumerate(reversed(body)))
    return total % 10 == check


def is_valid_unii(unii: str) -> bool:
    """Validate a UNII (Unique Ingredient Identifier).

    UNIIs are 10 alphanumeric characters containing at least one letter
    and one digit (e.g. ``R16CO5Y76E``).
    """
    if not isinstance(unii, str):
        return False
    u = unii.strip().upper()
    return (
        len(u) == 10
        and u.isalnum()
        and any(c.isalpha() for c in u)
        and any(c.isdigit() for c in u)
    )


def is_valid_inchikey(inchikey: str) -> bool:
    """Validate an InChIKey shape.

    Standard keys: ``14-10-1`` uppercase blocks (e.g.
    ``BSFYZMDRMSNJQR-UHFFFAOYSA-N``).  Non-standard keys have a 9-char
    third block.  Only the shape is checked, not the cryptographic checksum.
    """
    if not isinstance(inchikey, str):
        return False
    return bool(re.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z][A-Z0-9]{0,8}", inchikey.strip().upper()))


def is_valid_inchi(inchi: str) -> bool:
    """Validate an InChI string prefix (``InChI=1S/...`` or ``InChI=1/...``)."""
    if not isinstance(inchi, str):
        return False
    return bool(re.match(r"^InChI=1S?/", inchi.strip()))


def is_valid_chebi(chebi: str) -> bool:
    """Validate a ChEBI identifier (``CHEBI:1234`` or bare ``1234``)."""
    if not isinstance(chebi, str):
        return False
    return bool(re.fullmatch(r"(?:CHEBI:)?\d{1,9}", chebi.strip()))


def is_valid_chembl(chembl: str) -> bool:
    """Validate a ChEMBL identifier (``CHEMBL1234``)."""
    if not isinstance(chembl, str):
        return False
    return bool(re.fullmatch(r"CHEMBL\d{1,12}", chembl.strip().upper()))


def is_valid_kegg(kegg: str) -> bool:
    """Validate a KEGG compound/drug identifier (``C12345`` / ``D12345``)."""
    if not isinstance(kegg, str):
        return False
    return bool(re.fullmatch(r"[A-Z]\d{4,6}", kegg.strip().upper()))


def is_valid_mesh(mesh_id: str) -> bool:
    """Validate a MeSH identifier (``D000001`` / ``C123456``)."""
    if not isinstance(mesh_id, str):
        return False
    return bool(re.fullmatch(r"[A-Z]\d{6}", mesh_id.strip().upper()))


def is_valid_chemspider(chemspider_id: str) -> bool:
    """Validate a ChemSpider ID (positive integer)."""
    if not isinstance(chemspider_id, str):
        return False
    return bool(re.fullmatch(r"\d{1,12}", chemspider_id.strip()))


def is_valid_atc_code(prefix: str, suffix: str = "") -> bool:
    """Validate an ATC code.

    ATC structure is ``LETTERNN[LETTER][LETTERNN]`` (e.g. ``N02`` + ``BA01``
    -> ``N02BA01``).  The prefix is 1 letter + 2 digits with an optional
    third-level letter; the suffix is 1-2 letters + 1-2 digits.
    """
    if not isinstance(prefix, str) or not re.fullmatch(r"[A-Z]\d{2}[A-Z]?", prefix.strip().upper()):
        return False
    return not suffix or bool(re.fullmatch(r"[A-Z]{1,2}\d{1,2}", suffix.strip().upper()))


def is_valid_setid(setid: str) -> bool:
    """Validate an SPL setid (UUID v4 shape)."""
    if not isinstance(setid, str):
        return False
    return bool(re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        setid.strip().lower(),
    ))


def validate_identifier_fields(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Run all identifier validators over an enriched data dict.

    Returns a list of ``(field, message)`` violations.  Empty list means
    every present identifier passed.  Unknown/missing fields are skipped.
    """
    violations: list[tuple[str, str]] = []

    cas = data.get("cas_number")
    if cas and not is_valid_cas(str(cas)):
        violations.append(("cas_number", f"invalid CAS format/checksum: {cas!r}"))

    unii = data.get("unii")
    if unii and not is_valid_unii(str(unii)):
        violations.append(("unii", f"invalid UNII format: {unii!r}"))

    inchi = data.get("inchi")
    if inchi and not is_valid_inchi(str(inchi)):
        violations.append(("inchi", f"invalid InChI prefix: {inchi!r}"))

    inchikey = data.get("inchikey")
    if inchikey and not is_valid_inchikey(str(inchikey)):
        violations.append(("inchikey", f"invalid InChIKey format: {inchikey!r}"))

    chebi = data.get("chebi_id")
    if chebi and not is_valid_chebi(str(chebi)):
        violations.append(("chebi_id", f"invalid ChEBI identifier: {chebi!r}"))

    chembl = data.get("chembl_id")
    if chembl and not is_valid_chembl(str(chembl)):
        violations.append(("chembl_id", f"invalid ChEMBL identifier: {chembl!r}"))

    kegg = data.get("kegg_id")
    if kegg and not is_valid_kegg(str(kegg)):
        violations.append(("kegg_id", f"invalid KEGG identifier: {kegg!r}"))

    mesh = data.get("mesh_id")
    if mesh and not is_valid_mesh(str(mesh)):
        violations.append(("mesh_id", f"invalid MeSH identifier: {mesh!r}"))

    chemspider = data.get("chemspider_id")
    if chemspider and not is_valid_chemspider(str(chemspider)):
        violations.append(("chemspider_id", f"invalid ChemSpider ID: {chemspider!r}"))

    atc_prefix = data.get("atc_prefix")
    if atc_prefix and not is_valid_atc_code(str(atc_prefix), str(data.get("atc_suffix", "") or "")):
        violations.append(("atc_code", f"invalid ATC code: {atc_prefix!r}-{data.get('atc_suffix', '')!r}"))

    dailymed = data.get("dailymed_id")
    if dailymed and not is_valid_setid(str(dailymed)):
        violations.append(("dailymed_id", f"invalid SPL setid: {dailymed!r}"))

    return violations


# ---------------------------------------------------------------------------
# Numeric sanity ranges for experimental properties
# ---------------------------------------------------------------------------

# (min, max) in the property's natural unit.  Generous bounds: the goal is
# to catch unit/scale confusion and source corruption, not to be precise.
_NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "melting_point": (-273.15, 4000.0),
    "boiling_point": (-273.15, 6000.0),
    "flash_point": (-273.15, 1500.0),
    "autoignition_point": (-273.15, 2000.0),
    "density": (0.0, 30.0),
    "pka": (-30.0, 100.0),
    "refractive_index": (1.0, 4.0),
    "viscosity": (0.0, 1e9),
    "henry_constant": (0.0, 1e12),
    "vapor_pressure": (0.0, 1e9),
    "solubility": (0.0, 1e6),
}


def extract_first_number(value: str) -> float | None:
    """Extract the first decimal number from a unit-bearing string.

    ``"135 °C"`` -> ``135.0``; ``"1.2-1.5 g/cm3"`` -> ``1.2``;
    ``"no data"`` -> ``None``.
    """
    if not isinstance(value, str):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", value)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def check_numeric_ranges(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Range-check experimental property values.

    Returns ``(key, message)`` violations.  Values that do not contain a
    parseable number are skipped (missing data is not a violation).
    """
    violations: list[tuple[str, str]] = []
    for key, (lo, hi) in _NUMERIC_RANGES.items():
        raw = data.get(key)
        if not raw:
            continue
        num = extract_first_number(str(raw))
        if num is None:
            continue
        if not (lo <= num <= hi):
            violations.append((key, f"value {num} outside plausible range [{lo}, {hi}]: {raw!r}"))
    return violations


# ---------------------------------------------------------------------------
# Cross-source consistency against the RDKit ground truth
# ---------------------------------------------------------------------------


def compute_rdkit_formula(mol: Any) -> str | None:
    """Canonical molecular formula computed by RDKit (Hill order)."""
    if _rdMolDescriptors is None or mol is None:
        return None
    try:
        return _rdMolDescriptors.CalcMolFormula(mol)
    except Exception:
        return None


def compute_rdkit_mol_wt(mol: Any) -> float | None:
    """Average molecular weight computed by RDKit."""
    if Chem is None or mol is None:
        return None
    try:
        from rdkit.Chem import Descriptors

        return Descriptors.MolWt(mol)
    except Exception:
        return None


def _normalize_formula(formula: str) -> str:
    """Normalize a formula for comparison (uppercase, no whitespace)."""
    return "".join(formula.split()).upper()


def check_compound_consistency(
    smiles: str,
    data: dict[str, Any],
    mol: Any | None = None,
    *,
    mw_tolerance: float = 0.5,
) -> list[tuple[str, str]]:
    """Compare source-provided formula / molecular weight / InChIKey against
    the RDKit molecule computed from SMILES.

    Returns ``(field, message)`` violations.  Mismatches indicate a source
    returned data inconsistent with the structure itself — the value most
    likely to be trusted is the RDKit one.

    Parameters
    ----------
    smiles
        SMILES of the compound (canonical or raw).
    data
        Enriched compound dict (``molecular_formula``, ``molecular_weight``,
        ``inchikey`` keys are inspected).
    mol
        Optional pre-parsed RDKit molecule; parsed from *smiles* when None.
    mw_tolerance
        Absolute tolerance in daltons for molecular weight comparison.
    """
    violations: list[tuple[str, str]] = []
    if Chem is None:
        return violations

    if mol is None:
        try:
            mol = Chem.MolFromSmiles(smiles)
        except Exception:
            mol = None
    if mol is None:
        return violations

    # Formula
    rd_formula = compute_rdkit_formula(mol)
    src_formula = data.get("molecular_formula")
    if rd_formula and src_formula and _normalize_formula(rd_formula) != _normalize_formula(str(src_formula)):
        violations.append(
            (
                "molecular_formula",
                f"source {src_formula!r} != RDKit {rd_formula!r}",
            )
        )

    # Molecular weight
    rd_mw = compute_rdkit_mol_wt(mol)
    src_mw = data.get("molecular_weight")
    if rd_mw is not None and src_mw is not None:
        try:
            if abs(float(src_mw) - rd_mw) > mw_tolerance:
                violations.append(
                    (
                        "molecular_weight",
                        f"source {src_mw} != RDKit {rd_mw:.3f} (Δ > {mw_tolerance})",
                    )
                )
        except (TypeError, ValueError):
            violations.append(("molecular_weight", f"unparseable value: {src_mw!r}"))

    # InChIKey shape (content cannot be cross-checked without the InChI layer)
    inchikey = data.get("inchikey")
    if inchikey and not is_valid_inchikey(str(inchikey)):
        violations.append(("inchikey", f"invalid InChIKey format: {inchikey!r}"))

    return violations


__all__ = [
    "check_compound_consistency",
    "check_numeric_ranges",
    "compute_rdkit_formula",
    "compute_rdkit_mol_wt",
    "extract_first_number",
    "is_valid_atc_code",
    "is_valid_cas",
    "is_valid_chebi",
    "is_valid_chembl",
    "is_valid_chemspider",
    "is_valid_inchi",
    "is_valid_inchikey",
    "is_valid_kegg",
    "is_valid_mesh",
    "is_valid_setid",
    "is_valid_unii",
    "validate_identifier_fields",
]
