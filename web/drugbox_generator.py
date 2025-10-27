"""
web/drugbox_generator.py
=========================

Enhanced Wikipedia template generator for chemical compounds.

This module provides sophisticated Drugbox, Chembox, and Infobox generation
with support for comprehensive compound metadata from multiple sources.
Fully modularized with clean separation of concerns.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from web.data_sources import (
    DataAggregator,
    CompoundData,
    get_default_aggregator,
    DataSourceType
)

logger = logging.getLogger(__name__)


class TemplateGenerator:
    """
    Generates Wikipedia infobox templates for chemical compounds.

    Supports Drugbox (pharmaceuticals), Chembox (chemicals), and
    extended infobox formats with comprehensive metadata.
    """

    def __init__(self, data_aggregator: Optional[DataAggregator] = None):
        """
        Initialize template generator.

        Parameters
        ----------
        data_aggregator : Optional[DataAggregator]
            Aggregator for fetching compound data. If None, uses default.
        """
        self.aggregator = data_aggregator or get_default_aggregator()
        self.logger = logging.getLogger(__name__)

    def fetch_and_generate_all(
            self,
            identifier: str,
            image_filename: str = ""
    ) -> Dict[str, Optional[str]]:
        """
        Fetch compound data and generate all available templates.

        Parameters
        ----------
        identifier : str
            Compound identifier (CID, name, SMILES)
        image_filename : str
            Filename of the structure image

        Returns
        -------
        Dict[str, Optional[str]]
            Dictionary with keys: 'drugbox', 'chembox', 'infobox', 'metadata'
        """
        # Fetch compound data
        compound_data = self.aggregator.fetch_compound(identifier)
        if not compound_data:
            self.logger.warning(f"Could not fetch data for {identifier}")
            return {
                'drugbox': None,
                'chembox': None,
                'infobox': None,
                'metadata': None
            }

        return {
            'drugbox': self.generate_drugbox(compound_data, image_filename),
            'chembox': self.generate_chembox(compound_data, image_filename),
            'infobox': self.generate_infobox(compound_data, image_filename),
            'metadata': self.generate_metadata(compound_data)
        }

    def generate_drugbox(
            self,
            compound_data: CompoundData,
            image_filename: str = ""
    ) -> str:
        """
        Generate Wikipedia Drugbox template for pharmaceutical compounds.

        Parameters
        ----------
        compound_data : CompoundData
            Comprehensive compound metadata
        image_filename : str
            Filename of the structure image

        Returns
        -------
        str
            Drugbox template code
        """
        if not compound_data.iupac_name and not compound_data.smiles:
            return ""

        primary_name = self._get_primary_name(compound_data)

        drugbox = "{{Drugbox\n"
        drugbox += "| Verifiedfields = changed\n"
        drugbox += "| Watchedfields = changed\n"
        drugbox += f"| IUPAC_name = {compound_data.iupac_name or ''}\n"
        drugbox += f"| image = {image_filename or 'Example.png'}\n"
        drugbox += f"| alt = Chemical structure of {primary_name}\n"
        drugbox += "| caption = Chemical structure\n"

        # Drug Information
        if compound_data.drug_class:
            drugbox += f"| class = {'; '.join(compound_data.drug_class)}\n"

        if compound_data.atc_code:
            drugbox += f"| ATC_prefix = {compound_data.atc_code[:3]}\n"
            if len(compound_data.atc_code) > 3:
                drugbox += f"| ATC_suffix = {compound_data.atc_code[3:]}\n"

        # Routes of Administration
        if compound_data.routes_of_administration:
            drugbox += f"| routes_of_administration = {'; '.join(compound_data.routes_of_administration)}\n"

        # Identifiers
        if compound_data.cid:
            drugbox += f"| PubChem = {compound_data.cid}\n"

        if compound_data.chemspider_id:
            drugbox += f"| ChemSpiderID = {compound_data.chemspider_id}\n"

        if compound_data.unii_code:
            drugbox += f"| UNII = {compound_data.unii_code}\n"

        if compound_data.kegg_id:
            drugbox += f"| KEGG = {compound_data.kegg_id}\n"

        if compound_data.chebi_id:
            drugbox += f"| ChEBI = {compound_data.chebi_id}\n"

        if compound_data.chembl_id:
            drugbox += f"| ChEMBL = {compound_data.chembl_id}\n"

        if compound_data.drugbank_id:
            drugbox += f"| DrugBank = {compound_data.drugbank_id}\n"

        # Pharmacodynamics
        if compound_data.mechanism_of_action:
            drugbox += f"| mechanism_of_action = {compound_data.mechanism_of_action}\n"

        if compound_data.protein_binding:
            drugbox += f"| protein_bound = {compound_data.protein_binding}\n"

        if compound_data.half_life:
            drugbox += f"| elimination_half-life = {compound_data.half_life}\n"

        if compound_data.bioavailability:
            drugbox += f"| bioavailability = {compound_data.bioavailability}\n"

        if compound_data.metabolism:
            drugbox += f"| metabolism = {compound_data.metabolism}\n"

        # Chemical Properties
        drugbox += f"| synonyms = {'; '.join(compound_data.synonyms[:3])}\n"
        drugbox += f"| chemical_formula = {compound_data.molecular_formula or ''}\n"

        if compound_data.molecular_weight:
            drugbox += f"| molecular_weight = {compound_data.molecular_weight} g/mol\n"

        drugbox += f"| SMILES = {compound_data.smiles or ''}\n"
        drugbox += f"| StdInChI = {compound_data.inchi or ''}\n"
        drugbox += f"| StdInChIKey = {compound_data.inchikey or ''}\n"

        if compound_data.cas_number:
            drugbox += f"| CAS_number = {compound_data.cas_number}\n"

        # Physical Properties
        if compound_data.melting_point:
            drugbox += f"| melting_point = {compound_data.melting_point}\n"

        if compound_data.boiling_point:
            drugbox += f"| boiling_point = {compound_data.boiling_point}\n"

        if compound_data.appearance:
            drugbox += f"| appearance = {compound_data.appearance}\n"

        drugbox += "}}\n"

        return drugbox

    def generate_chembox(
            self,
            compound_data: CompoundData,
            image_filename: str = ""
    ) -> str:
        """
        Generate Wikipedia Chembox template for chemical compounds.

        Parameters
        ----------
        compound_data : CompoundData
            Comprehensive compound metadata
        image_filename : str
            Filename of the structure image

        Returns
        -------
        str
            Chembox template code
        """
        if not compound_data.molecular_formula and not compound_data.smiles:
            return ""

        primary_name = self._get_primary_name(compound_data)

        chembox = "{{Chembox\n"
        chembox += "| Verifiedfields = changed\n"
        chembox += "| Watchedfields = changed\n"
        chembox += f"| Name = {primary_name}\n"
        chembox += f"| ImageFile = {image_filename or 'Example.png'}\n"
        chembox += f"| IUPACName = {compound_data.iupac_name or ''}\n"
        chembox += f"| OtherNames = {'; '.join(compound_data.synonyms[:3])}\n"

        # Identifiers Section
        chembox += "|Section1={{Chembox Identifiers\n"

        if compound_data.cas_number:
            chembox += f"| CASNo = {compound_data.cas_number}\n"

        if compound_data.cid:
            chembox += f"| PubChem = {compound_data.cid}\n"

        if compound_data.chemspider_id:
            chembox += f"| ChemSpiderID = {compound_data.chemspider_id}\n"

        if compound_data.unii_code:
            chembox += f"| UNII = {compound_data.unii_code}\n"

        if compound_data.kegg_id:
            chembox += f"| KEGG = {compound_data.kegg_id}\n"

        if compound_data.chebi_id:
            chembox += f"| ChEBI = {compound_data.chebi_id}\n"

        if compound_data.chembl_id:
            chembox += f"| ChEMBL = {compound_data.chembl_id}\n"

        chembox += f"| SMILES = {compound_data.smiles or ''}\n"
        chembox += f"| StdInChI = {compound_data.inchi or ''}\n"
        chembox += f"| StdInChIKey = {compound_data.inchikey or ''}\n"
        chembox += "}}\n"

        # Properties Section
        chembox += "|Section2={{Chembox Properties\n"
        chembox += f"| Formula = {compound_data.molecular_formula or ''}\n"

        if compound_data.molecular_weight:
            chembox += f"| MolarMass = {compound_data.molecular_weight} g/mol\n"

        if compound_data.appearance:
            chembox += f"| Appearance = {compound_data.appearance}\n"

        if compound_data.density:
            chembox += f"| Density = {compound_data.density}\n"

        if compound_data.melting_point:
            chembox += f"| MeltingPt = {compound_data.melting_point}\n"

        if compound_data.boiling_point:
            chembox += f"| BoilingPt = {compound_data.boiling_point}\n"

        if compound_data.solubility:
            chembox += f"| Solubility = {compound_data.solubility}\n"

        chembox += "}}\n"

        # Hazards Section
        if compound_data.hazards:
            chembox += "|Section3={{Chembox Hazards\n"
            for hazard_type, hazard_value in compound_data.hazards.items():
                chembox += f"| {hazard_type} = {hazard_value}\n"
            chembox += "}}\n"

        chembox += "}}\n"

        return chembox

    def generate_infobox(
            self,
            compound_data: CompoundData,
            image_filename: str = ""
    ) -> str:
        """
        Generate generic Wikipedia Infobox for compounds.

        Parameters
        ----------
        compound_data : CompoundData
            Comprehensive compound metadata
        image_filename : str
            Filename of the structure image

        Returns
        -------
        str
            Infobox template code
        """
        primary_name = self._get_primary_name(compound_data)

        infobox = "{{Infobox chemical compound\n"
        infobox += f"| name = {primary_name}\n"
        infobox += f"| image = {image_filename or 'Example.png'}\n"
        infobox += f"| systematic_name = {compound_data.iupac_name or ''}\n"
        infobox += f"| other_names = {'; '.join(compound_data.synonyms[:3])}\n"

        # Identifiers
        infobox += "| identifiers = \n"
        if compound_data.cas_number:
            infobox += f"* CAS: {compound_data.cas_number}\n"
        if compound_data.cid:
            infobox += f"* PubChem: {compound_data.cid}\n"
        if compound_data.inchikey:
            infobox += f"* InChIKey: {compound_data.inchikey}\n"

        # Physical Properties
        if compound_data.molecular_formula:
            infobox += f"| chemical_formula = {compound_data.molecular_formula}\n"

        if compound_data.molecular_weight:
            infobox += f"| molar_mass = {compound_data.molecular_weight} g/mol\n"

        if compound_data.appearance:
            infobox += f"| appearance = {compound_data.appearance}\n"

        if compound_data.density:
            infobox += f"| density = {compound_data.density}\n"

        if compound_data.melting_point:
            infobox += f"| melting_point = {compound_data.melting_point}\n"

        if compound_data.boiling_point:
            infobox += f"| boiling_point = {compound_data.boiling_point}\n"

        if compound_data.solubility:
            infobox += f"| solubility = {compound_data.solubility}\n"

        infobox += "}}\n"

        return infobox

    def generate_metadata(self, compound_data: CompoundData) -> str:
        """
        Generate Wikimedia metadata template for image uploads.

        Parameters
        ----------
        compound_data : CompoundData
            Comprehensive compound metadata

        Returns
        -------
        str
            Wikimedia metadata template
        """
        primary_name = self._get_primary_name(compound_data)

        metadata = "{{Information\n"
        metadata += f"|description={{{{en|1=Chemical structure of {primary_name}}}}}\n"
        metadata += f"|date={datetime.now().strftime('%Y-%m-%d')}\n"
        metadata += "|source={{{{Own work}}}}\n"
        metadata += "|author=[[User:YourUsername|Your Username]]\n"
        metadata += "}}\n\n"

        metadata += "== License ==\n"
        metadata += "{{{{PD-chem}}}}\n"
        metadata += "{{{{Self|cc-by-sa-4.0}}}}\n\n"

        metadata += "== Categories ==\n"
        metadata += "[[Category:Chemical structures]]\n"
        metadata += f"[[Category:{primary_name}]]\n"

        if compound_data.drug_class:
            for drug_class in compound_data.drug_class:
                metadata += f"[[Category:{drug_class}]]\n"

        # Add data source attribution
        metadata += "\n== Data Sources ==\n"
        if compound_data.sources:
            for source in compound_data.sources:
                metadata += f"* {source.value.capitalize()}\n"

        return metadata

    def _get_primary_name(self, compound_data: CompoundData) -> str:
        """
        Get the best primary name for the compound.

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


# Convenience functions for backward compatibility
def fetch_pubchem_data(identifier: str) -> Optional[CompoundData]:
    """
    Fetch compound data from PubChem (convenience function).

    Parameters
    ----------
    identifier : str
        Compound identifier

    Returns
    -------
    Optional[CompoundData]
        Compound metadata or None
    """
    aggregator = get_default_aggregator()
    return aggregator.fetch_compound(identifier)


def generate_drugbox_code(
        compound_data: CompoundData,
        image_filename: str = ""
) -> str:
    """
    Generate Drugbox template (convenience function).

    Parameters
    ----------
    compound_data : CompoundData
        Compound metadata
    image_filename : str
        Structure image filename

    Returns
    -------
    str
        Drugbox template code
    """
    generator = TemplateGenerator()
    return generator.generate_drugbox(compound_data, image_filename)


def generate_chembox_code(
        compound_data: CompoundData,
        image_filename: str = ""
) -> str:
    """
    Generate Chembox template (convenience function).

    Parameters
    ----------
    compound_data : CompoundData
        Compound metadata
    image_filename : str
        Structure image filename

    Returns
    -------
    str
        Chembox template code
    """
    generator = TemplateGenerator()
    return generator.generate_chembox(compound_data, image_filename)
