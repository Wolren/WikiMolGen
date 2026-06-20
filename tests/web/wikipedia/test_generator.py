"""Tests for web/wikipedia/generator.py — mocked PubChemPy + enrich."""

from unittest.mock import MagicMock, patch

from web.wikipedia.generator import (
    _format_h_statements,
    _format_p_statements,
    _ghs_line,
    fetch_pubchem_data,
    generate_chembox_code,
    generate_drugbox_code,
)


class TestFormatHStatements:
    def test_basic(self):
        assert _format_h_statements("H302: Harmful if swallowed") == "{{H-phrases|302}}"

    def test_multiple(self):
        raw = "H302 (95.6%): Harmful if swallowed; H319 (75.6%): Causes eye irritation"
        result = _format_h_statements(raw)
        assert "H-phrases" in result
        assert "302" in result
        assert "319" in result

    def test_none(self):
        assert _format_h_statements(None) is None

    def test_no_h_codes(self):
        assert _format_h_statements("No hazard statements") is None


class TestFormatPStatements:
    def test_basic(self):
        assert _format_p_statements("P261") == "{{P-phrases|261}}"

    def test_multiple(self):
        raw = "P261, P264, P270, P301+P312"
        result = _format_p_statements(raw)
        assert "P-phrases" in result
        assert "261" in result
        assert "264" in result
        assert "301+P312" in result

    def test_none(self):
        assert _format_p_statements(None) is None


class TestGhsLine:
    def test_all_fields(self):
        dt = {
            "ghs_pictograms": "{{GHS07}}{{GHS06}}",
            "ghs_signal_word": "Warning",
            "h_statements": "H302: Harmful if swallowed",
            "p_statements": "P261, P264",
        }
        result = _ghs_line(dt)
        assert "GHSPictograms" in result
        assert "{{GHS07}}" in result
        assert "GHSSignalWord" in result
        assert "Warning" in result
        assert "HPhrases" in result
        assert "PPhrases" in result

    def test_empty(self):
        assert _ghs_line({}) == ""


class TestFetchPubchemData:
    def test_cid_lookup_success(self):
        mock_compound = MagicMock()
        mock_compound.iupac_name = "Aspirin"
        mock_compound.molecular_formula = "C9H8O4"
        mock_compound.molecular_weight = 180.16
        mock_compound.smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mock_compound.canonical_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mock_compound.inchi = "InChI=1S/C9H8O4/c1-..."
        mock_compound.inchikey = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        mock_compound.cid = 2244
        mock_compound.synonyms = ["Aspirin", "Acetylsalicylic acid", "2-Acetoxybenzoic acid"]

        with patch("pubchempy.get_compounds", return_value=[mock_compound]):
            with patch(
                "web.wikipedia.generator.enrich_compound_data",
                return_value={
                    "iupac_name": "Aspirin",
                    "cid": 2244,
                    "chembl_id": "CHEMBL123",
                    "drugbank_id": "DB00945",
                    "wikidata_qid": "Q18216",
                    "cas_number": "50-78-2",
                    "chebi_id": "15365",
                    "kegg_id": "D00109",
                    "unii": "R16CO5Y76E",
                    "chemspider_id": "2157",
                },
            ) as mock_enrich:
                result = fetch_pubchem_data("2244")
                assert result is not None
                assert result["iupac_name"] == "Aspirin"
                assert result["cid"] == 2244
                assert result["chembl_id"] == "CHEMBL123"
                assert result["drugbank_id"] == "DB00945"
                assert result["wikidata_qid"] == "Q18216"
                assert result["cas_number"] == "50-78-2"
                assert result["chebi_id"] == "15365"
                assert result["kegg_id"] == "D00109"
                assert result["unii"] == "R16CO5Y76E"
                assert result["chemspider_id"] == "2157"
                mock_enrich.assert_called_once()

    def test_name_lookup_success(self):
        mock_compound = MagicMock()
        mock_compound.iupac_name = "Caffeine"
        mock_compound.molecular_formula = "C8H10N4O2"
        mock_compound.molecular_weight = 194.19
        mock_compound.smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
        mock_compound.canonical_smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
        mock_compound.inchi = "InChI=1S/C8H10N4O2/c1-..."
        mock_compound.inchikey = "RYYVLZVUVIJVGH-UHFFFAOYSA-N"
        mock_compound.cid = 2519
        mock_compound.synonyms = ["Caffeine", "Theine"]

        with patch("pubchempy.get_compounds", return_value=[mock_compound]):
            with patch("web.wikipedia.generator.enrich_compound_data", side_effect=lambda x: x):
                result = fetch_pubchem_data("caffeine")
                assert result is not None
                assert result["iupac_name"] == "Caffeine"
                assert result["cid"] == 2519

    def test_smiles_lookup_fallback(self):
        mock_compound = MagicMock()
        mock_compound.iupac_name = "Ethanol"
        mock_compound.molecular_formula = "C2H6O"
        mock_compound.molecular_weight = 46.07
        mock_compound.smiles = "CCO"
        mock_compound.canonical_smiles = "CCO"
        mock_compound.inchi = "InChI=1S/C2H6O/c1-..."
        mock_compound.inchikey = "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"
        mock_compound.cid = 702
        mock_compound.synonyms = ["Ethanol", "Ethyl alcohol"]

        with patch(
            "pubchempy.get_compounds",
            side_effect=[
                [],
                [mock_compound],
            ],
        ):
            with patch("web.wikipedia.generator.enrich_compound_data", side_effect=lambda x: x):
                result = fetch_pubchem_data("CCO")
                assert result is not None
                assert result["iupac_name"] == "Ethanol"

    def test_no_results(self):
        with patch("pubchempy.get_compounds", return_value=[]):
            result = fetch_pubchem_data("nonexistent_compound_xyzzy_12345")
            assert result is None

    def test_exception_caught(self):
        with patch("pubchempy.get_compounds", side_effect=Exception("API Error")):
            result = fetch_pubchem_data("2244")
            assert result is None

    def test_synonyms_capped_at_10(self):
        mock_compound = MagicMock()
        mock_compound.iupac_name = "Test"
        mock_compound.molecular_formula = "C"
        mock_compound.molecular_weight = 12.01
        mock_compound.smiles = "C"
        mock_compound.canonical_smiles = "C"
        mock_compound.inchi = "InChI=1S/C"
        mock_compound.inchikey = "OKTJSMMVPCPJKN-UHFFFAOYSA-N"
        mock_compound.cid = 1
        mock_compound.synonyms = [f"synonym_{i}" for i in range(20)]

        with patch("pubchempy.get_compounds", return_value=[mock_compound]):
            with patch("web.wikipedia.generator.enrich_compound_data", side_effect=lambda x: x):
                result = fetch_pubchem_data("1")
                assert len(result["synonyms"]) == 10

    def test_no_synonyms(self):
        mock_compound = MagicMock()
        mock_compound.iupac_name = "Test"
        mock_compound.molecular_formula = "C"
        mock_compound.molecular_weight = 12.01
        mock_compound.smiles = "C"
        mock_compound.canonical_smiles = "C"
        mock_compound.inchi = "InChI=1S/C"
        mock_compound.inchikey = "OKTJSMMVPCPJKN-UHFFFAOYSA-N"
        mock_compound.cid = 1
        mock_compound.synonyms = None

        with patch("pubchempy.get_compounds", return_value=[mock_compound]):
            with patch("web.wikipedia.generator.enrich_compound_data", side_effect=lambda x: x):
                result = fetch_pubchem_data("1")
                assert result["synonyms"] == []


class TestGenerateDrugboxCode:
    FULL_DATA = {
        "cas_number": "50-78-2",
        "cid": 2244,
        "drugbank_id": "DB00945",
        "chemspider_id": "2157",
        "chembl_id": "CHEMBL123",
        "unii": "R16CO5Y76E",
        "kegg_id": "D00109",
        "synonyms": ["Aspirin", "Acetylsalicylic acid", "2-Acetoxybenzoic acid"],
        "iupac_name": "Aspirin",
        "molecular_formula": "C9H8O4",
        "molecular_weight": 180.16,
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "inchi": "InChI=1S/C9H8O4/c1-...",
        "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "wikidata_qid": "Q18216",
    }

    def test_generates_valid_template(self):
        result = generate_drugbox_code(self.FULL_DATA, "Aspirin_structure.png")
        assert "Infobox drug" in result
        assert "Aspirin_structure.png" in result
        assert "50-78-2" in result
        assert "DB00945" in result
        assert "CHEMBL123" in result
        assert "R16CO5Y76E" in result
        assert "D00109" in result
        assert "2244" in result
        assert "Aspirin" in result
        assert "180.16 g/mol" in result

    def test_all_enriched_fields_appear(self):
        """Verify every field from enrichment sources populates drugbox correctly."""
        result = generate_drugbox_code(self.FULL_DATA)
        assert "| CAS_number = 50-78-2" in result
        assert "| PubChem = 2244" in result
        assert "| DrugBank = DB00945" in result
        assert "| ChemSpiderID = 2157" in result
        assert "| ChEMBL = CHEMBL123" in result
        assert "| UNII = R16CO5Y76E" in result
        assert "| KEGG = D00109" in result
        assert "| IUPAC_name = Aspirin" in result
        assert "| chemical_formula = C9H8O4" in result
        assert "180.16 g/mol" in result
        assert "CC(=O)OC1=CC=CC=C1C(=O)O" in result
        assert "InChI=1S/C9H8O4/c1-..." in result
        assert "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" in result
        assert "Aspirin; Acetylsalicylic acid; 2-Acetoxybenzoic acid" in result

    def test_empty_when_no_data(self):
        result = generate_drugbox_code(None)
        assert "Unable to generate Drugbox" in result

    def test_empty_dict(self):
        result = generate_drugbox_code({})
        assert "Unable to generate Drugbox" in result

    def test_empty_dict_still_generates_template(self):
        # When all keys are empty strings but compound_data is not falsy
        result = generate_drugbox_code({"cid": 1})
        assert "Infobox drug" in result

    def test_image_defaults_to_example(self):
        result = generate_drugbox_code(self.FULL_DATA)
        assert "Example.png" in result

    def test_synonyms_capped_at_3(self):
        data = dict(self.FULL_DATA)
        data["synonyms"] = [f"s{i}" for i in range(10)]
        result = generate_drugbox_code(data)
        assert "s0; s1; s2" in result
        assert "s3" not in result

    def test_element_counts_dynamic(self):
        data = dict(self.FULL_DATA)
        data.update({"na_count": 1, "mg_count": 2, "fe_count": 3, "c_count": 9, "o_count": 2})
        result = generate_drugbox_code(data)
        assert "| C = 9" in result
        assert "| O = 2" in result
        assert "| Na = 1" in result
        assert "| Mg = 2" in result
        assert "| Fe = 3" in result


class TestGenerateChemboxCode:
    FULL_DATA = {
        "cas_number": "50-78-2",
        "cid": 2244,
        "drugbank_id": "DB00945",
        "chemspider_id": "2157",
        "chebi_id": "CHEBI:15365",
        "chembl_id": "CHEMBL123",
        "unii": "R16CO5Y76E",
        "kegg_id": "D00109",
        "synonyms": ["Aspirin"],
        "iupac_name": "Aspirin",
        "molecular_formula": "C9H8O4",
        "molecular_weight": 180.16,
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "inchi": "InChI=1S/C9H8O4/c1-...",
        "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        "melting_point": "136 °C",
        "boiling_point": "140 °C",
        "xlogp": 1.0,
        "wikidata_qid": "Q18216",
        "ec_number": "200-064-1",
        "un_number": "2811",
        "rtecs": "VO0700000",
        "unii": "R16CO5Y76E",
        "iuphar_ligand": "1234",
        "niaid_chemdb": "5678",
        "mesh_id": "D001241",
        "drugs_com": "aspirin",
        "medlineplus": "a682878",
        "pdb_ligand": "ASN",
        "c_count": 9,
        "h_count": 8,
        "o_count": 4,
    }

    def test_generates_valid_template(self):
        result = generate_chembox_code(self.FULL_DATA, "Aspirin_structure.png")
        assert "Chembox" in result
        assert "Aspirin_structure.png" in result
        assert "50-78-2" in result
        assert "CHEBI:15365" in result
        assert "DB00945" in result
        assert "136 °C" in result
        assert "1.0" in result

    def test_all_enriched_fields_appear(self):
        """Verify every field from enrichment sources populates chembox correctly."""
        result = generate_chembox_code(self.FULL_DATA)
        assert "| CASNo = 50-78-2" in result
        assert "| ChEBI = CHEBI:15365" in result
        assert "| ChemSpiderID = 2157" in result
        assert "| DrugBank = DB00945" in result
        assert "| KEGG = D00109" in result
        assert "| UNII = R16CO5Y76E" in result
        assert "| PubChem = 2244" in result
        assert "| SMILES = CC(=O)OC1=CC=CC=C1C(=O)O" in result
        assert "| StdInChI = InChI=1S/C9H8O4/c1-..." in result
        assert "| StdInChIKey = BSYNRYMUTXBXSQ-UHFFFAOYSA-N" in result
        assert "| Formula = C9H8O4" in result
        assert "180.16 g/mol" in result
        assert "| IUPACName = Aspirin" in result
        assert "| LogP = 1.0" in result

    def test_element_counts_in_chembox(self):
        result = generate_chembox_code(self.FULL_DATA)
        assert "| C = 9" in result
        assert "| H = 8" in result
        assert "| O = 4" in result

    def test_new_identifiers_appear(self):
        result = generate_chembox_code(self.FULL_DATA)
        assert "| EC_number = 200-064-1" in result
        assert "| UNNumber = 2811" in result
        assert "| RTECS = VO0700000" in result
        assert "| IUPHAR_ligand = 1234" in result
        assert "| NIAID_ChemDB = 5678" in result
        assert "| MeSHName = D001241" in result
        assert "| Drugs_com = aspirin" in result
        assert "| MedlinePlus = a682878" in result
        assert "| PDB_ligand = ASN" in result

    def test_ghs_fields_in_chembox(self):
        dt = dict(self.FULL_DATA)
        dt["ghs_pictograms"] = "{{GHS07}}"
        dt["ghs_signal_word"] = "Warning"
        dt["h_statements"] = "H302: Harmful if swallowed"
        dt["p_statements"] = "P261, P264"
        result = generate_chembox_code(dt)
        assert "Section6" in result
        assert "GHSPictograms" in result
        assert "{{GHS07}}" in result
        assert "GHSSignalWord" in result
        assert "HPhrases" in result
        assert "PPhrases" in result

    def test_boiling_point_in_chembox(self):
        result = generate_chembox_code(self.FULL_DATA)
        assert "| BoilingPt = 140 °C" in result

    def test_empty_when_no_data(self):
        result = generate_chembox_code(None)
        assert "Unable to generate Chembox" in result

    def test_empty_dict(self):
        result = generate_chembox_code({})
        assert "Chembox" in result

    def test_image_defaults_to_example(self):
        result = generate_chembox_code(self.FULL_DATA)
        assert "Example.png" in result
