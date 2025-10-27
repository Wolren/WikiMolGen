"""
web/wikipedia_boxes.py
=======================

Streamlit UI component for rendering Wikipedia metadata and templates.

Provides the visual interface for displaying compound metadata, Wikipedia
templates (Drugbox, Chembox), and Wikimedia metadata.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any

from web.drugbox_generator import (
    fetch_pubchem_data,
    generate_drugbox_code,
    generate_chembox_code,
    TemplateGenerator
)
from web.data_sources import CompoundData


class WikipediaMetadataRenderer:
    """Handles rendering of Wikipedia metadata and template sections."""

    def __init__(self):
        """Initialize the renderer."""
        self.logger = None

    @staticmethod
    def render_metadata_section(compound: str, structure_type: str) -> None:
        """
        Render complete Wikipedia metadata and template section.

        Displays automatically when structure is rendered, showing:
        - Wikimedia metadata template
        - Chemical links and identifiers
        - Drugbox and Chembox templates

        Parameters
        ----------
        compound : str
            Compound identifier
        structure_type : str
            "2D" or "3D"
        """
        if not st.session_state.get("rendered_structure"):
            st.info("Generate a structure to see Wikipedia metadata and templates.")
            return

        # Fetch or use cached data
        compound_data = WikipediaMetadataRenderer._fetch_compound_data(compound)

        if not compound_data:
            st.warning("Unable to fetch compound data from PubChem.")
            return

        # Render metadata and templates
        st.divider()

        col_meta, col_ids = st.columns(2)

        with col_meta:
            WikipediaMetadataRenderer._render_wikimedia_metadata(compound)

        with col_ids:
            WikipediaMetadataRenderer._render_chemical_identifiers(compound_data)

        st.divider()

        # Render templates side-by-side
        col_drug, col_chem = st.columns(2)

        with col_drug:
            WikipediaMetadataRenderer._render_drugbox_template(
                compound_data,
                f"{compound}_{structure_type}.png"
            )

        with col_chem:
            WikipediaMetadataRenderer._render_chembox_template(
                compound_data,
                f"{compound}_{structure_type}.png"
            )

        st.divider()
        st.info(
            "💡 **Tip**: Copy the appropriate template and paste into "
            "Wikipedia article source. Choose Drugbox for pharmaceuticals, "
            "Chembox for chemicals."
        )

    @staticmethod
    def _fetch_compound_data(compound: str) -> Optional[CompoundData]:
        """
        Fetch compound data from cache or fetch fresh.

        Parameters
        ----------
        compound : str
            Compound identifier

        Returns
        -------
        Optional[CompoundData]
            Compound metadata or None
        """
        # Check if we need to fetch new data
        last_fetched = st.session_state.get("last_compound_fetched")
        cached_data = st.session_state.get("pubchem_data")

        if compound == last_fetched and cached_data:
            return cached_data

        # Fetch new data
        st.session_state.last_compound_fetched = compound

        with st.spinner("Fetching compound data from PubChem..."):
            try:
                data = fetch_pubchem_data(compound)
                st.session_state.pubchem_data = data
                return data
            except Exception as e:
                st.session_state.pubchem_data = None
                st.error(f"Error fetching PubChem data: {e}")
                return None

    @staticmethod
    def _render_wikimedia_metadata(compound: str) -> None:
        """
        Render Wikimedia metadata template for image uploads.

        Parameters
        ----------
        compound : str
            Compound identifier
        """
        st.subheader("📋 Wikimedia Metadata")

        metadata = f"""{{{{Information
|description={{{{en|1=Chemical structure of {compound}}}}}
|date={datetime.now().strftime('%Y-%m-%d')}
|source={{{{Own work}}}}
|author=[[User:YourUsername|Your Username]]
}}}}

== License ==

{{{{PD-chem}}}}
{{{{Self|cc-by-sa-4.0}}}}

[[Category:Chemical structures]]
[[Category:{compound}]]"""

        st.code(metadata, language="wiki")

        if st.button("📋 Copy Metadata", key="copy_metadata"):
            st.toast("✅ Metadata copied to clipboard (manual paste required)")

    @staticmethod
    def _render_chemical_identifiers(compound_data: CompoundData) -> None:
        """
        Render chemical identifiers and external links.

        Parameters
        ----------
        compound_data : CompoundData
            Compound metadata
        """
        st.subheader("🧪 Chemical Links & Identifiers")

        # Success message with primary name
        primary_name = WikipediaMetadataRenderer._get_primary_name(compound_data)
        st.success(f"🔍 Retrieved data for: {primary_name}")

        # Build identifiers table
        identifiers_data = {
            "Property": [],
            "Value": []
        }

        # Add available identifiers
        if compound_data.cid:
            identifiers_data["Property"].append("CID")
            identifiers_data["Value"].append(
                f"[{compound_data.cid}]"
                f"(https://pubchem.ncbi.nlm.nih.gov/compound/{compound_data.cid})"
            )

        if compound_data.inchikey:
            identifiers_data["Property"].append("InChIKey")
            identifiers_data["Value"].append(f"`{compound_data.inchikey}`")

        if compound_data.cas_number:
            identifiers_data["Property"].append("CAS Number")
            identifiers_data["Value"].append(compound_data.cas_number)

        if compound_data.smiles:
            identifiers_data["Property"].append("SMILES")
            identifiers_data["Value"].append(f"`{compound_data.smiles}`")

        if compound_data.iupac_name:
            identifiers_data["Property"].append("IUPAC Name")
            identifiers_data["Value"].append(compound_data.iupac_name)

        # Display as table
        if identifiers_data["Property"]:
            import pandas as pd
            df = pd.DataFrame(identifiers_data)
            st.dataframe(df, hide_index=True, use_container_width=True)

        # Display data sources
        if compound_data.sources:
            st.markdown("**Data Sources:**")
            sources_text = ", ".join([s.value.capitalize() for s in compound_data.sources])
            st.caption(f"📊 {sources_text}")

        if compound_data.confidence_score > 0:
            confidence_pct = int(compound_data.confidence_score * 100)
            st.progress(compound_data.confidence_score, f"Data Confidence: {confidence_pct}%")

    @staticmethod
    def _render_drugbox_template(
            compound_data: CompoundData,
            image_filename: str
    ) -> None:
        """
        Render Drugbox template for pharmaceuticals.

        Parameters
        ----------
        compound_data : CompoundData
            Compound metadata
        image_filename : str
            Structure image filename
        """
        st.markdown("#### 💉 **Drugbox Template** (for pharmaceuticals)")

        generator = TemplateGenerator()
        drugbox_code = generator.generate_drugbox(compound_data, image_filename)

        if drugbox_code:
            st.session_state.last_drugbox = drugbox_code
            st.code(drugbox_code, language="wiki")

            if st.button("📋 Copy Drugbox", key="copy_drugbox"):
                st.toast("✅ Drugbox copied (manual paste required)")
        else:
            st.info("No pharmaceutical data available for Drugbox")

    @staticmethod
    def _render_chembox_template(
            compound_data: CompoundData,
            image_filename: str
    ) -> None:
        """
        Render Chembox template for chemicals.

        Parameters
        ----------
        compound_data : CompoundData
            Compound metadata
        image_filename : str
            Structure image filename
        """
        st.markdown("#### 🔬 **Chembox Template** (for chemicals)")

        generator = TemplateGenerator()
        chembox_code = generator.generate_chembox(compound_data, image_filename)

        if chembox_code:
            st.session_state.last_chembox = chembox_code
            st.code(chembox_code, language="wiki")

            if st.button("📋 Copy Chembox", key="copy_chembox"):
                st.toast("✅ Chembox copied (manual paste required)")
        else:
            st.info("No chemical data available for Chembox")

    @staticmethod
    def _get_primary_name(compound_data: CompoundData) -> str:
        """
        Get the best primary name for display.

        Parameters
        ----------
        compound_data : CompoundData
            Compound metadata

        Returns
        -------
        str
            Primary name
        """
        if compound_data.trade_names:
            return compound_data.trade_names[0]

        if compound_data.common_names:
            return compound_data.common_names[0]

        if compound_data.synonyms:
            return compound_data.synonyms[0]

        if compound_data.iupac_name:
            return compound_data.iupac_name

        return f"Compound {compound_data.cid or 'Unknown'}"


# Convenience function for use in main app
def render_wikipedia_metadata_section(compound: str, structure_type: str) -> None:
    """
    Render Wikipedia metadata section (main interface function).

    Parameters
    ----------
    compound : str
        Compound identifier
    structure_type : str
        "2D" or "3D"
    """
    WikipediaMetadataRenderer.render_metadata_section(compound, structure_type)
