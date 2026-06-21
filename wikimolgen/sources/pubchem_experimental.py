"""
wikimolgen.sources.pubchem_experimental
========================================

Client for the `PubChem PUG View
<https://pubchem.ncbi.nlm.nih.gov/docs/pug-view>`_ JSON endpoint.

Fetches the full structured record and extracts experimental physical
properties, GHS classification, toxicity data, and identifiers.

No API key required — 5 requests/second recommended, free.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

PUGVIEW_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"

# Map (section_heading, subsection_heading) -> output key
_PROP_MAP: dict[tuple[str, str], str] = {
    ("Chemical and Physical Properties", "Melting Point"): "melting_point",
    ("Chemical and Physical Properties", "Boiling Point"): "boiling_point",
    ("Chemical and Physical Properties", "Flash Point"): "flash_point",
    ("Chemical and Physical Properties", "Solubility"): "solubility",
    ("Chemical and Physical Properties", "Vapor Pressure"): "vapor_pressure",
    ("Chemical and Physical Properties", "Density"): "density",
    ("Chemical and Physical Properties", "Decomposition"): "decomposition",
    ("Chemical and Physical Properties", "Physical Description"): "appearance",
    ("Chemical and Physical Properties", "Odor"): "odor",
    ("Chemical and Physical Properties", "Dissociation Constants"): "pka",
    ("Chemical and Physical Properties", "Autoignition Temperature"): "autoignition_point",
    ("Chemical and Physical Properties", "Refractive Index"): "refractive_index",
    ("Chemical and Physical Properties", "Viscosity"): "viscosity",
    ("Chemical and Physical Properties", "Optical Rotation"): "optical_rotation",
    ("Chemical and Physical Properties", "Henry's Law Constant"): "henry_constant",
    ("Chemical and Physical Properties", "LogP"): "logp_experimental",
    ("Safety and Hazards", "Flammable Limits"): "explosive_limits",
    ("Names and Identifiers", "UN Number"): "un_number",
    ("Names and Identifiers", "European Community (EC) Number"): "ec_number",
}


def _find_section(sections: list, heading: str) -> dict | None:
    """Find a section dict by ``TOCHeading`` in a list of sections."""
    for s in sections:
        if s.get("TOCHeading") == heading:
            return s
    return None


def _walk_sections(sections: list, *headings: str) -> list | None:
    """Walk a chain of ``Section`` arrays following ``TOCHeading`` values.

    Returns the ``Section`` list of the last matched heading, or ``None``
    if any step is missing.
    """
    current = sections
    for h in headings:
        section = _find_section(current, h)
        if section is None:
            return None
        current = section.get("Section", [])
    return current


def _find_leaf_section(sections: list, *headings: str) -> dict | None:
    """Walk to the last heading and return that section dict itself."""
    current = sections
    for h in headings:
        section = _find_section(current, h)
        if section is None:
            return None
        children = section.get("Section", [])
        if not children:
            return section
        current = children
    return current[-1] if current else None


def _first_string(information: list) -> str | None:
    """Return the first plain string from an ``Information`` array.

    Handles both ``StringWithMarkup`` and ``Number`` value types.
    """
    if not information:
        return None
    value = information[0].get("Value", {})
    swm = value.get("StringWithMarkup")
    if swm:
        return swm[0].get("String", "").strip() or None
    num = value.get("Number")
    if num:
        unit = value.get("Unit", "")
        s = str(num[0])
        if unit:
            s = f"{s} {unit}"
        return s
    return None


def _all_strings(information: list, separator: str = "; ") -> str | None:
    """Join all ``StringWithMarkup`` strings from an ``Information`` array."""
    parts: list[str] = []
    for item in information:
        value = item.get("Value", {})
        swm = value.get("StringWithMarkup")
        if swm:
            for entry in swm:
                s = entry.get("String", "").strip()
                if s:
                    parts.append(s)
        num = value.get("Number")
        if num is not None:
            unit = value.get("Unit", "")
            parts.append(f"{num[0]} {unit}".strip())
    return separator.join(parts) if parts else None


def _extract_value(sections: list, section_heading: str, heading: str) -> str | None:
    """Walk *section_heading* → *heading* and return the first string value."""
    leaf = _find_leaf_section(sections, section_heading, heading)
    if leaf is None:
        leaf = _find_leaf_section(sections, section_heading, "Experimental Properties", heading)
    if leaf is None:
        return None
    return _first_string(leaf.get("Information", []))


def _extract_ghs_data(sections: list) -> dict[str, Any]:
    """Extract GHS Classification data from Safety and Hazards section."""
    result: dict[str, Any] = {}
    ghs_section = _find_leaf_section(
        sections, "Safety and Hazards", "Hazards Identification", "GHS Classification"
    )
    if ghs_section is None:
        return result

    info = ghs_section.get("Information", [])
    for item in info:
        name = item.get("Name", "")
        value = item.get("Value", {})

        if name == "Pictogram(s)":
            swm = value.get("StringWithMarkup", [])
            codes: list[str] = []
            for entry in swm:
                markup = entry.get("Markup", [])
                for m in markup:
                    if m.get("Type") == "Icon":
                        url = m.get("URL", "")
                        code = url.rsplit("/", 1)[-1].replace(".svg", "")
                        if code:
                            codes.append(f"{{{{{code}}}}}")
            if codes:
                result["ghs_pictograms"] = "".join(codes)

        elif name == "Signal":
            swm = value.get("StringWithMarkup", [])
            if swm:
                result["ghs_signal_word"] = swm[0].get("String", "")

        elif name == "GHS Hazard Statements":
            statements = _all_strings([{"Value": value}], separator="\n")
            if statements:
                result["h_statements"] = statements

        elif name == "Precautionary Statement Codes":
            codes_str = _all_strings([{"Value": value}], separator="\n")
            if codes_str:
                result["p_statements"] = codes_str

    return result


def _extract_toxicity_data(sections: list) -> dict[str, Any]:
    """Extract toxicity data (LD50, LC50) from Toxicity section."""
    result: dict[str, Any] = {}
    tox_section = _find_leaf_section(
        sections, "Toxicity", "Toxicological Information", "Toxicity Data"
    )
    if tox_section is None:
        return result

    lines: list[str] = []
    for item in tox_section.get("Information", []):
        swm = item.get("Value", {}).get("StringWithMarkup", [])
        for entry in swm:
            s = entry.get("String", "").strip()
            if s:
                lines.append(s)

    if lines:
        result["toxicity_data"] = "; ".join(lines)
        # Also extract LD50 patterns
        ld50_vals: list[str] = []
        for line in lines:
            if "LD50" in line.upper():
                ld50_vals.append(line)
        if ld50_vals:
            result["ld50"] = "; ".join(ld50_vals)
    return result


def _extract_identifier_value(sections: list, heading: str) -> str | None:
    """Extract a value from Names and Identifiers → Other Identifiers."""
    subs = _walk_sections(sections, "Names and Identifiers", "Other Identifiers")
    if subs is None:
        return None
    for sub in subs:
        if sub.get("TOCHeading") == heading:
            return _first_string(sub.get("Information", []))
    return None


def fetch_experimental_data(
    pubchem_cid: int | str,
    timeout: float = 20,
) -> dict[str, Any]:
    """Fetch experimental, hazard, and identifier data from PubChem PUG View.

    Parameters
    ----------
    pubchem_cid
        PubChem compound identifier (numeric).
    timeout
        HTTP request timeout in seconds (longer than default because the
        full JSON record can be large).

    Returns
    -------
    dict
        Internal key → value mapping.  Common keys:

        - ``melting_point``, ``boiling_point``, ``flash_point``
        - ``solubility``, ``density``, ``vapor_pressure``
        - ``appearance``, ``odor``, ``decomposition``
        - ``pka``, ``autoignition_point``, ``refractive_index``
        - ``viscosity``, ``optical_rotation``, ``henry_constant``
        - ``logp_experimental``
        - ``ghs_pictograms``, ``ghs_signal_word``, ``h_statements``, ``p_statements``
        - ``ld50``, ``toxicity_data``
        - ``un_number``, ``ec_number``
        - ``explosive_limits``

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    from wikimolgen.sources._client import make_headers, requests

    cid = str(int(pubchem_cid))
    url = f"{PUGVIEW_BASE}/{cid}/JSON"

    resp = requests.get(
        url,
        headers=make_headers(description="experimental data fetcher"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    result: dict[str, Any] = {}
    record = data.get("Record", {})
    sections = record.get("Section", [])
    if not sections:
        return result

    # Phase 1: Simple property extraction via _PROP_MAP
    for (section_heading, heading), key in _PROP_MAP.items():
        val = _extract_value(sections, section_heading, heading)
        if val:
            result[key] = val

    # Phase 2: GHS Classification data
    result.update(_extract_ghs_data(sections))

    # Phase 3: Toxicity data
    result.update(_extract_toxicity_data(sections))

    # Phase 4: Identifier values that need deeper walking
    for ident_heading, key in [
        ("UN Number", "un_number"),
        ("European Community (EC) Number", "ec_number"),
    ]:
        val = _extract_identifier_value(sections, ident_heading)
        if val:
            result[key] = val

    # Phase 5: RTECS Number from Other Identifiers
    rtecs_val = _extract_identifier_value(sections, "RTECS Number")
    if rtecs_val:
        result["rtecs"] = rtecs_val

    return result
