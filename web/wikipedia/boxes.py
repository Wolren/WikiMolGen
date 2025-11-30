"""
web/boxes.py
=======================
Wikipedia boxes and metadata generation - EXACT ORIGINAL from wiki_web_optimized.py.
Displays automatically when structure is rendered, with Wikimedia metadata and drugbox/chembox side-by-side.
"""

from datetime import datetime

import streamlit as st

from wikipedia.generator import fetch_pubchem_data, generate_drugbox_code, generate_chembox_code

def render_wikipedia_metadata_section(compound: str, structure_type: str) -> None:
    """
    Render the EXACT ORIGINAL Wikipedia metadata and boxes section.
    This matches wiki_web_optimized.py precisely - NO generate buttons,
    displays automatically when structure is rendered.

    Parameters
    ----------
    compound : str
        Compound identifier
    structure_type : str
        "2D" or "3D"
    """

    # ===== METADATA & FEATURES SECTION =====
    # Only show if structure has been rendered
    if st.session_state.get("rendered_structure"):
        # Only trigger new metadata fetch if compound changed
        if compound != st.session_state.get("last_compound_fetched"):
            st.session_state.last_compound_fetched = compound
            with st.spinner("Fetching compound data from PubChem..."):
                try:
                    data = fetch_pubchem_data(compound)
                    st.session_state.pubchem_data = data
                except Exception as e:
                    st.session_state.pubchem_data = None
                    st.error(f"Error fetching PubChem data: {e}")

        # Display metadata / cached info
        col_dl1, col_dl2 = st.columns(2)

        pubchem_data = st.session_state.get("pubchem_data")

        if pubchem_data:
            synonyms = pubchem_data.get('synonyms', [])
            cid = pubchem_data.get('cid', 'NA')
            iupac = pubchem_data.get('iupac_name', '')
            primary_name = synonyms[0] if synonyms else (iupac if iupac else f"Compound {cid}")
        else:
            primary_name = compound

        with col_dl1:
            st.subheader("🗃️ Wikimedia Metadata")
            metadata = f"""{{{{Information
|description={{{{en|1={st.session_state.get("structure_type")} structure of {primary_name} generated using WikiMolGen (RDKit and PyMOL-based tool)}}}}
|date={datetime.now().strftime('%Y-%m-%d')}
|source={{{{Own work}}}}
|author=
}}}}

== License ==
{{{{Self|cc-by-sa-4.0}}}}

[[Category:Chemical structures]]"""
            st.code(metadata, language="wiki")

        with col_dl2:
            st.subheader("🔗 Chemical Links")
            identifiers_placeholder = st.empty()

        pubchem_data = st.session_state.get("pubchem_data")

        if pubchem_data:
            cid = str(pubchem_data.get("cid", "N/A"))
            inchi = pubchem_data.get("standard_inchi", "N/A")
            inchikey = pubchem_data.get("standard_inchikey", "N/A")
            smiles = pubchem_data.get("isomeric_smiles", "N/A")
            iupac = pubchem_data.get("iupac_name", "N/A")
            wikidata_q = pubchem_data.get("wikidata_qid", None)

            identifiers_markdown = f"""
| **Property**    | **Value** |
|:----------------|:----------|
| **CID**         | [{cid}](https://pubchem.ncbi.nlm.nih.gov/compound/{cid}) |
| **InChI**       | `{inchi}` |
| **InChIKey**    | `{inchikey}` |
| **SMILES**      | `{smiles}` |
| **IUPAC Name**  | `{iupac}` |
| **Wikidata**    | {'[' + wikidata_q + '](https://www.wikidata.org/wiki/' + wikidata_q + ')' if wikidata_q else 'N/A'} |
"""

            identifiers_placeholder.markdown(identifiers_markdown)

            col_drug, col_chem = st.columns(2)

            with col_drug:
                st.markdown("#### **Drugbox Template** (for pharmaceuticals)")
                st.session_state.last_drugbox = generate_drugbox_code(
                    pubchem_data, f"{compound}_{structure_type}.png"
                )
                st.code(st.session_state.last_drugbox, language="wiki")

            with col_chem:
                st.markdown("#### **Chembox Template** (for chemicals)")
                st.session_state.last_chembox = generate_chembox_code(
                    pubchem_data, f"{compound}_{structure_type}.png"
                )
                st.code(st.session_state.last_chembox, language="wiki")
        else:
            st.warning("Not able to fetch compound data from PubChem.")
    else:
        st.info("Generate a structure to see Wikipedia metadata and template.")
