"""
Wikipedia Drugbox Generator
===========================
Fetches compound data from PubChem and generates Wikipedia Drugbox template code.
"""

from typing import Optional, Dict, Any

import pubchempy as pcp


def fetch_pubchem_data(identifier: str) -> Optional[Dict[str, Any]]:
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
        # Try to get compound by CID first
        if identifier.isdigit():
            compounds = pcp.get_compounds(identifier, 'cid')
        else:
            # Try by name, then SMILES
            compounds = pcp.get_compounds(identifier, 'name')
            if not compounds:
                compounds = pcp.get_compounds(identifier, 'smiles')

        if not compounds:
            return None

        compound = compounds[0]

        data = {
            'iupac_name': compound.iupac_name,
            'molecular_formula': compound.molecular_formula,
            'molecular_weight': compound.molecular_weight,
            'smiles': compound.smiles or compound.canonical_smiles,
            'inchi': compound.inchi,
            'inchikey': compound.inchikey,
            'cid': compound.cid,
            'synonyms': compound.synonyms[:5] if compound.synonyms else []
        }

        return data

    except Exception as e:
        print(f"Error fetching PubChem data: {e}")
        return None


def generate_drugbox_code(compound_data: Dict[str, Any], image_filename: str = "") -> str:
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

    # Get primary name (first synonym or IUPAC)
    primary_name = compound_data['synonyms'][0] if compound_data['synonyms'] else compound_data['iupac_name']

    drugbox_template = f"""{{{{Infobox drug
| image = {image_filename if image_filename else 'Example.png'}
| image_class = skin-invert-image
| width = 200px
| alt =
| image2 =
| image_class2 =
| width2 =

<!--Clinical data-->
| pronounce = 
| tradename = 
| Drugs.com = 
| MedlinePlus = 
| pregnancy_AU = 
| pregnancy_AU_comment = 
| pregnancy_category = 
| routes_of_administration = 
| class = 
| ATCvet = 
| ATC_prefix = 
| ATC_suffix = 

<!--Legal status-->
| legal_AU = 
| legal_AU_comment = 
| legal_BR = 
| legal_BR_comment = 
| legal_CA = 
| legal_CA_comment = 
| legal_DE = 
| legal_DE_comment = 
| legal_NZ = 
| legal_NZ_comment = 
| legal_UK = 
| legal_UK_comment = 
| legal_US = 
| legal_US_comment = 
| legal_UN = 
| legal_UN_comment = 
| legal_status = 

<!--Pharmacokinetic data-->
| bioavailability = 
| protein_bound = 
| metabolism = 
| metabolites = 
| onset = 
| elimination_half-life = 
| duration_of_action = 
| excretion = 

<!--Identifiers-->
| CAS_number_Ref = 
| CAS_number = 
| PubChem = {compound_data.get('cid', '')}
| ChemSpiderID_Ref = 
| ChemSpiderID = 
| ChEMBL_Ref = 
| ChEMBL = 
| UNII_Ref = 
| UNII = 
| synonyms = {'; '.join(compound_data.get('synonyms', [])[:3])}

<!--Chemical and physical data-->
| IUPAC_name = {compound_data.get('iupac_name', '')}
| chemical_formula = {compound_data.get('molecular_formula', '')}
| molecular_weight = {compound_data.get('molecular_weight', '')} g/mol
| SMILES = {compound_data.get('smiles', '')}
| StdInChI_Ref =
| StdInChI = {compound_data.get('inchi', '')}
| StdInChIKey_Ref =
| StdInChIKey = {compound_data.get('inchikey', '')}
}}}}"""

    return drugbox_template


def generate_chembox_code(compound_data: Dict[str, Any], image_filename: str = "") -> str:
    """
    Generate Wikipedia Chembox template code (alternative to Drugbox).

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

    chembox_template = f"""{{{{Chembox
<!-- Images -->
| ImageFile = {image_filename if image_filename else 'Example.png'}
| ImageSize = 225px
| ImageAlt = 
| ImageClass = skin-invert-image

<!-- Names -->
| IUPACName = {compound_data.get('iupac_name', '')}
| OtherNames = {'; '.join(compound_data.get('synonyms', [])[:3])}

<!-- Sections -->
|Section1={{{{Chembox Identifiers
| CASNo = 
| ChEBI = 
| ChemSpiderID = 
| StdInChI = {compound_data.get('inchi', '')}
| StdInChIKey = {compound_data.get('inchikey', '')}
| KEGG = 
| UNII = 
| PubChem = {compound_data.get('cid', '')}
| SMILES = {compound_data.get('smiles', '')}
}}}}
|Section2={{{{Chembox Properties
| Formula = {compound_data.get('molecular_formula', '')}
| MolarMass = {compound_data.get('molecular_weight', '')} g/mol
| Appearance = 
| Density = 
| MeltingPt = 
| BoilingPt = 
| Solubility = 
}}}}
|Section3={{{{Chembox Hazards
| MainHazards = 
| FlashPt = 
| AutoignitionPt = 
}}}}
}}}}"""

    return chembox_template
