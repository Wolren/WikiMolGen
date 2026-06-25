"""
web/boxes.py
=======================
Wikipedia metadata and template display using tabs.
"""

from datetime import datetime
from urllib.parse import quote

import streamlit as st
from wikipedia.generator import fetch_pubchem_data, generate_chembox_code, generate_drugbox_code


def _esc(val: str) -> str:
    return val.replace("|", "\\|")


def _md_row(label: str, value: str) -> str:
    return f"| **{label}** | {_esc(value)} |\n" if value else ""


def _link(label: str, value: str, url: str) -> str:
    return f"| **{label}** | [{value}]({url}) |\n" if value else ""


def _code_row(label: str, value: str) -> str:
    return f"| **{label}** | `{_esc(value)}` |\n" if value else ""


def render_wikipedia_metadata_section(compound: str, structure_type: str) -> None:
    """
    Display Wikipedia metadata and template tabs.
    Fetches compound data when compound changes (independent of rendering).
    """
    if not compound:
        return

    # Initialize persistent config
    if "commons_license" not in st.session_state:
        st.session_state.commons_license = "cc-by-sa-4.0"
        st.session_state.commons_license_text = "Self|cc-by-sa-4.0"
        st.session_state.commons_license_picker = "cc-by-sa-4.0"
        st.session_state.commons_author = "WikiMolGen"
        st.session_state.commons_last_mode = None

    # Reset license to mode-appropriate default on mode switch
    last_mode = st.session_state.commons_last_mode
    if last_mode != structure_type:
        st.session_state.commons_last_mode = structure_type
        if structure_type == "2D":
            st.session_state.commons_license = "pd-chem"
            st.session_state.commons_license_text = "PD-chem"
            st.session_state.commons_license_picker = "PD-chem"
        else:
            st.session_state.commons_license = "cc-by-sa-4.0"
            st.session_state.commons_license_text = "Self|cc-by-sa-4.0"
            st.session_state.commons_license_picker = "cc-by-sa-4.0"

    # Derive license template and wp param from picker

    # Fetch data when compound changes
    if compound != st.session_state.get("last_compound_fetched"):
        st.session_state.last_compound_fetched = compound
        with st.spinner("Fetching compound data from PubChem..."):
            try:
                data = fetch_pubchem_data(compound)
                st.session_state.pubchem_data = data
            except Exception as e:
                st.session_state.pubchem_data = None
                st.error(f"Error fetching PubChem data: {e}")

    pubchem_data = st.session_state.get("pubchem_data")
    if not pubchem_data:
        return

    synonyms = pubchem_data.get("synonyms", [])
    cid_raw = pubchem_data.get("cid", "NA")
    iupac = pubchem_data.get("iupac_name", "")
    primary_name = synonyms[0] if synonyms else (iupac if iupac else f"Compound {cid_raw}")

    author = st.session_state.get("commons_author", "WikiMolGen")
    license_tmpl = st.session_state.get("commons_license_text", "Self|cc-by-sa-4.0")
    license_wp = st.session_state.get("commons_license", "cc-by-sa-4.0")

    metadata = f"""{{{{Information
|description={{{{en|1={structure_type} structure of {primary_name} generated using WikiMolGen (RDKit and PyMOL-based tool)}}}}
|date={datetime.now().strftime("%Y-%m-%d")}
|source={{{{Own work}}}}
|author={author}
}}}}

== License ==
{{{{{license_tmpl}}}}}

[[Category:Chemical structures]]"""

    filename = f"{primary_name.replace(' ', '_')}_{structure_type}.png"

    # Derive license template and wp param from picker
    pick = st.session_state.get("commons_license_picker", "cc-by-sa-4.0")
    _license_map = {
        "cc-by-sa-4.0": ("Self|cc-by-sa-4.0", "cc-by-sa-4.0"),
        "cc-zero": ("Self|cc-zero", "cc-zero"),
        "cc-by-4.0": ("Self|cc-by-4.0", "cc-by-4.0"),
        "cc-by-sa-3.0": ("Self|cc-by-sa-3.0", "cc-by-sa-3.0"),
        "PD-chem": ("PD-chem", ""),
        "PD-self": ("PD-self", "pd-self"),
        "Custom": (st.session_state.get("commons_custom_license", "{{Self|cc-by-sa-4.0}}"), ""),
    }
    license_tmpl, license_wp = _license_map.get(pick, ("Self|cc-by-sa-4.0", "cc-by-sa-4.0"))
    st.session_state.commons_license_text = license_tmpl
    st.session_state.commons_license = license_wp

    tab1, tab2, tab3, tab4 = st.tabs(["Wikimedia Metadata", "Chemical Links", "Drugbox", "Chembox"])

    with tab1:
        st.code(metadata, language="wiki")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.text_input(
                "Author",
                placeholder="Your username",
                max_chars=100,
                key="commons_author",
            )
        with col2:
            st.selectbox(
                "License",
                [
                    "cc-by-sa-4.0",
                    "cc-zero",
                    "cc-by-4.0",
                    "cc-by-sa-3.0",
                    "PD-chem",
                    "PD-self",
                    "Custom",
                ],
                key="commons_license_picker",
            )
            if st.session_state.get("commons_license_picker") == "Custom":
                st.text_input(
                    "Custom license template",
                    value="{{Self|cc-by-sa-4.0}}",
                    max_chars=200,
                    key="commons_custom_license",
                )

        upload_url = (
            f"https://commons.wikimedia.org/wiki/Special:Upload?"
            f"wpDestFile={quote(filename)}&"
            f"wpUploadDescription={quote(metadata)}"
        )
        if license_wp:
            upload_url += f"&wpLicense={quote(license_wp)}"

        st.link_button("Upload to Wikimedia Commons", upload_url, type="secondary")

    with tab2:
        cid = str(cid_raw)
        inchi = pubchem_data.get("inchi", "N/A")
        inchikey = pubchem_data.get("inchikey", "N/A")
        smiles = pubchem_data.get("smiles", "N/A")
        iupac_name = pubchem_data.get("iupac_name", "N/A")
        wikidata_q = pubchem_data.get("wikidata_qid", None)
        atc_prefix = pubchem_data.get("atc_prefix", "")
        atc_suffix = pubchem_data.get("atc_suffix", "")
        atc_code = f"{atc_prefix}{atc_suffix}" if atc_prefix else ""
        formula = pubchem_data.get("molecular_formula", "")
        chemspider_id = pubchem_data.get("chemspider_id", "")
        unii_val = pubchem_data.get("unii", "")
        drugbank_id = pubchem_data.get("drugbank_id", "")
        chebi_id = pubchem_data.get("chebi_id", "")
        chembl_id = pubchem_data.get("chembl_id", "")
        kegg_id = pubchem_data.get("kegg_id", "")
        mesh_id = pubchem_data.get("mesh_id", "")

        ids = "| **Property** | **Value** |\n|:---|:---|\n"
        ids += _code_row("CID", cid)
        ids += _code_row("InChI", inchi)
        ids += _code_row("InChIKey", inchikey)
        ids += _code_row("SMILES", smiles)
        ids += _code_row("IUPAC Name", iupac_name)
        ids += _md_row("Formula", formula)
        if wikidata_q:
            ids += _link("Wikidata", wikidata_q, f"https://www.wikidata.org/wiki/{wikidata_q}")
        if chemspider_id:
            ids += _link(
                "ChemSpider",
                chemspider_id,
                f"https://www.chemspider.com/Chemical-Structure.{chemspider_id}.html",
            )
        if unii_val:
            ids += _link("UNII", unii_val, f"https://fdasis.nlm.nih.gov/srs/unii/{unii_val}.json")
        ids += (
            _link("DrugBank", drugbank_id, f"https://go.drugbank.com/drugs/{drugbank_id}")
            if drugbank_id
            else ""
        )
        ids += _md_row("ChEBI", chebi_id)
        ids += _md_row("ChEMBL", chembl_id)
        ids += _md_row("KEGG", kegg_id)
        ids += _md_row("MeSH ID", mesh_id)
        ids += _code_row("ATC Code", atc_code)

        st.markdown(ids)

    with tab3:
        st.session_state.last_drugbox = generate_drugbox_code(
            pubchem_data, f"{compound}_{structure_type}.png"
        )
        st.code(st.session_state.last_drugbox, language="html")

    with tab4:
        st.session_state.last_chembox = generate_chembox_code(
            pubchem_data, f"{compound}_{structure_type}.png"
        )
        st.code(st.session_state.last_chembox, language="html")
