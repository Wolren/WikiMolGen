"""
Wikipedia Drugbox Generator
===========================
Fetches compound data from PubChem and generates Wikipedia Drugbox/Chembox
template code.
"""

from __future__ import annotations

import re
from typing import Any

import pubchempy as pcp

try:
    from wikimolgen.core import enrich_compound_data
except ImportError:

    def enrich_compound_data(compound_data: dict[Any, Any] | None) -> dict[Any, Any] | None:
        return compound_data


_WIKI_UNSAFE_RE = re.compile(r"[|{}\[\]\n\r]")


def _sanitize_wiki(text: str) -> str:
    """Escape characters with special meaning in MediaWiki template values."""

    def _replace(m: re.Match) -> str:
        ch = m.group(0)
        if ch == "|":
            return "{{!}}"
        if ch == "{":
            return "&#123;"
        if ch == "}":
            return "&#125;"
        if ch == "[":
            return "&#91;"
        if ch == "]":
            return "&#93;"
        return " "  # newlines

    return _WIKI_UNSAFE_RE.sub(_replace, str(text))


def _pop_fields(dt: dict[str, Any], fields: list[tuple[str, str]]) -> str:
    """Build template lines from *fields* where values exist in *dt*."""
    lines = ""
    for key, tmpl in fields:
        val = dt.get(key)
        if val:
            lines += f"| {tmpl} = {_sanitize_wiki(val)}\n"
    return lines


def _format_h_statements(raw: str | None) -> str | None:
    """Convert PubChem GHS hazard statements to Wikipedia ``{{H-phrases}}``.

    Input: ``"H302 (95.6%): Harmful if swallowed ...; H319 (75.6%): ..."``
    Output: ``"{{H-phrases|302|319|...}}"``
    """
    if not raw:
        return None
    codes = re.findall(r"H\d{3,4}(?:\+H\d{3,4})*", raw)
    if not codes:
        return None
    numbers = [c[1:] for c in codes]
    return "{{H-phrases|" + "|".join(numbers) + "}}"


def _format_p_statements(raw: str | None) -> str | None:
    """Convert PubChem GHS precautionary statements to ``{{P-phrases}}``.

    Input: ``"P261, P264+P265, P270, ..."``
    Output: ``"{{P-phrases|261|264+P265|270|...}}"``
    """
    if not raw:
        return None
    codes = re.findall(r"P\d{3,4}(?:\+P\d{3,4})*", raw)
    if not codes:
        return None
    numbers = [c[1:] for c in codes]
    return "{{P-phrases|" + "|".join(numbers) + "}}"


def _ghs_line(dt: dict[str, Any]) -> str:
    """Build the GHS pictograms / signal word / H / P lines."""
    lines = ""
    pict = dt.get("ghs_pictograms")
    if pict:
        lines += f"| GHSPictograms = {pict}\n"
    sig = dt.get("ghs_signal_word")
    if sig:
        lines += f"| GHSSignalWord = {sig}\n"
    h_raw = dt.get("h_statements")
    h_fmt = _format_h_statements(h_raw)
    if h_fmt:
        lines += f"| HPhrases = {h_fmt}\n"
    p_raw = dt.get("p_statements")
    p_fmt = _format_p_statements(p_raw)
    if p_fmt:
        lines += f"| PPhrases = {p_fmt}\n"
    return lines


def fetch_pubchem_data(identifier: str) -> dict[str, Any] | None:
    """
    Fetch compound data from PubChem.

    Parameters
    ----------
    identifier : str
        PubChem CID, compound name, or SMILES

    Returns
    -------
    dict or None
        Dictionary with compound data or None if not found
    """
    try:
        if identifier.isdigit():
            compounds = pcp.get_compounds(identifier, "cid")
        else:
            compounds = pcp.get_compounds(identifier, "name")
            if not compounds:
                compounds = pcp.get_compounds(identifier, "smiles")

        if not compounds:
            return None

        compound = compounds[0]

        data = {
            "iupac_name": compound.iupac_name,
            "molecular_formula": compound.molecular_formula,
            "molecular_weight": compound.molecular_weight,
            "smiles": compound.smiles or compound.canonical_smiles,
            "inchi": compound.inchi,
            "inchikey": compound.inchikey,
            "cid": compound.cid,
            "synonyms": compound.synonyms[:10] if compound.synonyms else [],
        }

        return enrich_compound_data(data)

    except Exception as e:
        print(f"Error fetching PubChem data: {e}")
        return None


def generate_drugbox_code(compound_data: dict[str, Any], image_filename: str = "") -> str:
    """
    Generate Wikipedia Drugbox template code.

    Parameters
    ----------
    compound_data : dict
        Dictionary with compound data from PubChem
    image_filename : str, optional
        Filename of the uploaded structure image

    Returns
    -------
    str
        Wikipedia Drugbox template code
    """
    if not compound_data:
        return "<!-- Unable to generate Drugbox: No compound data available -->"

    dt = compound_data

    # Build dynamic sections — only output lines with non-empty values

    element_lines = ""
    for k, v in sorted(dt.items()):
        if k.endswith("_count") and v:
            element_lines += f"| {k[:-6].capitalize()} = {v}\n"

    clin = _pop_fields(
        dt,
        [
            ("pronounce", "pronounce"),
            ("tradename", "tradename"),
            ("drugs_com", "Drugs.com"),
            ("medlineplus", "MedlinePlus"),
            ("pregnancy_au", "pregnancy_AU"),
            ("pregnancy_au_comment", "pregnancy_AU_comment"),
            ("pregnancy_category", "pregnancy_category"),
            ("routes_of_administration", "routes_of_administration"),
            ("drug_class", "class"),
            ("atc_vet", "ATCvet"),
            ("atc_prefix", "ATC_prefix"),
            ("atc_suffix", "ATC_suffix"),
            ("atc_supplemental", "ATC_supplemental"),
        ],
    )
    legal = _pop_fields(
        dt,
        [
            ("legal_au", "legal_AU"),
            ("legal_au_comment", "legal_AU_comment"),
            ("legal_br", "legal_BR"),
            ("legal_br_comment", "legal_BR_comment"),
            ("legal_ca", "legal_CA"),
            ("legal_ca_comment", "legal_CA_comment"),
            ("legal_de", "legal_DE"),
            ("legal_de_comment", "legal_DE_comment"),
            ("legal_nz", "legal_NZ"),
            ("legal_nz_comment", "legal_NZ_comment"),
            ("legal_uk", "legal_UK"),
            ("legal_uk_comment", "legal_UK_comment"),
            ("legal_us", "legal_US"),
            ("legal_us_comment", "legal_US_comment"),
            ("legal_un", "legal_UN"),
            ("legal_un_comment", "legal_UN_comment"),
            ("licence_ca", "licence_CA"),
            ("licence_eu", "licence_EU"),
            ("licence_us", "licence_US"),
            ("legal_status", "legal_status"),
            ("dependency_liability", "dependency_liability"),
            ("addiction_liability", "addiction_liability"),
        ],
    )
    pk = _pop_fields(
        dt,
        [
            ("bioavailability", "bioavailability"),
            ("protein_bound", "protein_bound"),
            ("metabolism", "metabolism"),
            ("metabolites", "metabolites"),
            ("onset", "onset"),
            ("elimination_half_life", "elimination_half-life"),
            ("duration_of_action", "duration_of_action"),
            ("excretion", "excretion"),
        ],
    )
    ids = _pop_fields(
        dt,
        [
            ("cas_number", "CAS_number"),
            ("cas_supplemental", "CAS_supplemental"),
            ("cid", "PubChem"),
            ("pubchem_substance", "PubChemSubstance"),
            ("drugbank_id", "DrugBank"),
            ("chemspider_id", "ChemSpiderID"),
            ("chembl_id", "ChEMBL"),
            ("chebi_id", "ChEBI"),
            ("unii", "UNII"),
            ("kegg_id", "KEGG"),
            ("dailymed_id", "DailyMedID"),
            ("iuphar_ligand", "IUPHAR_ligand"),
            ("pdb_ligand", "PDB_ligand"),
            ("niaid_chemdb", "NIAID_ChemDB"),
        ],
    )
    chem = _pop_fields(
        dt,
        [
            ("iupac_name", "IUPAC_name"),
            ("molecular_formula", "chemical_formula"),
        ],
    )
    phys = _pop_fields(
        dt,
        [
            ("density", "density"),
            ("melting_point", "melting_point"),
            ("boiling_point", "boiling_point"),
            ("solubility", "solubility"),
        ],
    )
    syns = "; ".join(_sanitize_wiki(s) for s in dt.get("synonyms", [])[:3])
    syn_line = f"| synonyms = {syns}\n" if syns else ""

    mw_val = _sanitize_wiki(dt.get("molecular_weight", "") or "")
    mw_line = f"| molecular_weight = {mw_val} g/mol\n" if mw_val else ""
    smi_val = _sanitize_wiki(dt.get("smiles", "") or "")
    smi_line = f"| SMILES = {smi_val}\n" if smi_val else ""
    inchi_val = _sanitize_wiki(dt.get("inchi", "") or "")
    inchi_line = f"| StdInChI = {inchi_val}\n" if inchi_val else ""
    inkey_val = _sanitize_wiki(dt.get("inchikey", "") or "")
    inkey_line = f"| StdInChIKey = {inkey_val}\n" if inkey_val else ""

    lines = []
    lines.append("{{Infobox drug")
    lines.append(f"| image = {image_filename if image_filename else 'Example.png'}")
    lines.append("| image_class = skin-invert-image")
    lines.append("| width = 200px")

    def _add_section(lines_list: list, comment: str, content: str) -> None:
        stripped = content.strip()
        if stripped:
            lines_list.append("")
            lines_list.append(comment)
            lines_list.extend(stripped.split("\n"))

    _add_section(lines, "<!-- Clinical data -->", clin)
    _add_section(lines, "<!-- Legal status -->", legal)
    _add_section(lines, "<!-- Pharmacokinetic data -->", pk)

    ids_block = ids
    if syn_line.strip():
        ids_block += syn_line
    if smi_line.strip():
        ids_block += smi_line
    if inchi_line.strip():
        ids_block += inchi_line
    if inkey_line.strip():
        ids_block += inkey_line
    _add_section(lines, "<!-- Identifiers -->", ids_block)

    _add_section(lines, "<!-- Chemical data -->", chem + element_lines + mw_line)
    _add_section(lines, "<!-- Physical data -->", phys)

    lines.append("}}")
    return "\n".join(lines)


def generate_chembox_code(compound_data: dict[str, Any], image_filename: str = "") -> str:
    """
    Generate Wikipedia Chembox template code matching the full
    `Template:Chembox <https://en.wikipedia.org/wiki/Template:Chembox>`_ spec.

    Parameters
    ----------
    compound_data : dict
        Dictionary with compound data from PubChem
    image_filename : str, optional
        Filename of the uploaded structure image

    Returns
    -------
    str
        Wikipedia Chembox template code
    """
    if not compound_data:
        return "<!-- Unable to generate Chembox: No compound data available -->"

    dt = compound_data

    # Section 1 — Identifiers
    ids = _pop_fields(
        dt,
        [
            ("cas_number", "CASNo"),
            ("cas_supplemental", "CASNo_comment"),
            ("chebi_id", "ChEBI"),
            ("chembl_id", "ChEMBL"),
            ("chemspider_id", "ChemSpiderID"),
            ("drugbank_id", "DrugBank"),
            ("drugs_com", "Drugs_com"),
            ("ec_number", "EC_number"),
            ("iuphar_ligand", "IUPHAR_ligand"),
            ("kegg_id", "KEGG"),
            ("medlineplus", "MedlinePlus"),
            ("mesh_id", "MeSHName"),
            ("niaid_chemdb", "NIAID_ChemDB"),
            ("pdb_ligand", "PDB_ligand"),
            ("cid", "PubChem"),
            ("pubchem_substance", "PubChemSubstance"),
            ("rtecs", "RTECS"),
            ("unii", "UNII"),
            ("un_number", "UNNumber"),
        ],
    )
    smi_val = _sanitize_wiki(dt.get("smiles", "") or "")
    smi_line = f"| SMILES = {smi_val}\n" if smi_val else ""
    inchi_val = _sanitize_wiki(dt.get("inchi", "") or "")
    inchi_line = f"| StdInChI = {inchi_val}\n" if inchi_val else ""
    inkey_val = _sanitize_wiki(dt.get("inchikey", "") or "")
    inkey_line = f"| StdInChIKey = {inkey_val}\n" if inkey_val else ""

    # Section 2 — Properties
    elem_lines = ""
    for k, v in sorted(dt.items()):
        if k.endswith("_count") and v:
            elem_lines += f"| {k[:-6].capitalize()} = {_sanitize_wiki(str(v))}\n"
    props = _pop_fields(
        dt,
        [
            ("molecular_formula", "Formula"),
            ("appearance", "Appearance"),
            ("odor", "Odor"),
            ("density", "Density"),
            ("melting_point", "MeltingPt"),
            ("boiling_point", "BoilingPt"),
            ("decomposition", "Decomposition"),
            ("solubility", "Solubility"),
            ("vapor_pressure", "VaporPressure"),
            ("pka", "pKa"),
            ("autoignition_point", "AutoignitionPt"),
            ("refractive_index", "RefractIndex"),
            ("viscosity", "Viscosity"),
            ("optical_rotation", "SpecRotation"),
            ("henry_constant", "HenryConstant"),
            ("logp_experimental", "LogP"),
            ("xlogp", "LogP"),
        ],
    )
    mw_val = _sanitize_wiki(dt.get("molecular_weight", "") or "")
    mw_line = f"| MolarMass = {mw_val} g/mol\n" if mw_val else ""

    # Section 3 — Structure (only when data available)
    struct = _pop_fields(dt, [])

    # Section 4 — Thermochemistry (only when data available)
    thermo = _pop_fields(dt, [])

    # Section 5 — Pharmacology
    pharm = _pop_fields(
        dt,
        [
            ("inn", "INN"),
            ("atc_prefix", "ATCCodePrefix"),
            ("atc_suffix", "ATCCodeSuffix"),
            ("atc_supplemental", "ATC_Supplemental"),
            ("atc_vet", "ATCvet"),
            ("drug_class", "Drug_class"),
            ("routes_of_administration", "AdminRoutes"),
            ("bioavailability", "Bioavail"),
            ("protein_bound", "ProteinBound"),
            ("metabolism", "Metabolism"),
            ("metabolites", "Metabolites"),
            ("onset", "OnsetOfAction"),
            ("elimination_half_life", "HalfLife"),
            ("duration_of_action", "DurationOfAction"),
            ("excretion", "Excretion"),
            ("legal_status", "Legal_status"),
            ("legal_au", "Legal_AU"),
            ("legal_au_comment", "Legal_AU_comment"),
            ("legal_br", "Legal_BR"),
            ("legal_br_comment", "Legal_BR_comment"),
            ("legal_ca", "Legal_CA"),
            ("legal_ca_comment", "Legal_CA_comment"),
            ("legal_de", "Legal_DE"),
            ("legal_de_comment", "Legal_DE_comment"),
            ("legal_nz", "Legal_NZ"),
            ("legal_nz_comment", "Legal_NZ_comment"),
            ("legal_uk", "Legal_UK"),
            ("legal_uk_comment", "Legal_UK_comment"),
            ("legal_us", "Legal_US"),
            ("legal_us_comment", "Legal_US_comment"),
            ("legal_un", "Legal_UN"),
            ("legal_un_comment", "Legal_UN_comment"),
            ("licence_ca", "Licence_CA"),
            ("licence_eu", "Licence_EU"),
            ("licence_us", "Licence_US"),
            ("dependency_liability", "Dependence_liability"),
            ("addiction_liability", "Addiction_liability"),
            ("pregnancy_au", "Pregnancy_AU"),
            ("pregnancy_au_comment", "Pregnancy_AU_comment"),
            ("pregnancy_category", "Pregnancy_category"),
        ],
    )

    # Section 6 — Hazards
    ghs = _ghs_line(dt)
    hazard = _pop_fields(
        dt,
        [
            ("flash_point", "FlashPt"),
            ("explosive_limits", "ExploLimits"),
            ("ld50", "LD50"),
            ("toxicity_data", "Toxicity"),
            ("autoignition_point", "AutoignitionPt"),
        ],
    )

    # Section 7 — Related compounds (only when data available)
    related = _pop_fields(dt, [])

    # Build template — only include sections that have content
    chembox_template = f"""{{{{Chembox
| ImageFile = {image_filename if image_filename else "Example.png"}
| ImageSize = 225px
| ImageClass = skin-invert-image
| IUPACName = {_sanitize_wiki(dt.get("iupac_name", "") or "")}"""
    other = "; ".join(_sanitize_wiki(s) for s in dt.get("synonyms", [])[:3])
    if other:
        chembox_template += f"\n| OtherNames = {other}"

    if ids or smi_line or inchi_line or inkey_line:
        chembox_template += f"""
|Section1={{{{Chembox Identifiers
{ids}{smi_line}{inchi_line}{inkey_line}}}}}"""
    if props or mw_line or elem_lines:
        chembox_template += f"""
|Section2={{{{Chembox Properties
{elem_lines}{props}{mw_line}}}}}"""
    if struct:
        chembox_template += f"""
|Section3={{{{Chembox Structure
{struct}}}}}"""
    if thermo:
        chembox_template += f"""
|Section4={{{{Chembox Thermochemistry
{thermo}}}}}"""
    if pharm:
        chembox_template += f"""
|Section5={{{{Chembox Pharmacology
{pharm}}}}}"""
    if hazard or ghs:
        chembox_template += f"""
|Section6={{{{Chembox Hazards
{ghs}{hazard}}}}}"""
    if related:
        chembox_template += f"""
|Section7={{{{Chembox Related
{related}}}}}"""

    chembox_template = chembox_template.rstrip("\n") + "\n}}"

    return chembox_template
