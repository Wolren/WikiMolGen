"""Tests for wikimolgen.validation — pure validator functions."""

from rdkit import Chem

from wikimolgen.validation import (
    check_compound_consistency,
    check_numeric_ranges,
    extract_first_number,
    is_valid_atc_code,
    is_valid_cas,
    is_valid_chebi,
    is_valid_chembl,
    is_valid_chemspider,
    is_valid_inchi,
    is_valid_inchikey,
    is_valid_kegg,
    is_valid_mesh,
    is_valid_setid,
    is_valid_unii,
    validate_identifier_fields,
)


class TestCAS:
    def test_valid_cas(self):
        # Water 7732-18-5: body 773218, reversed weights -> 105 mod 10 = 5
        assert is_valid_cas("7732-18-5")
        # Aspirin 50-78-2: body 5078, reversed weights -> 42 mod 10 = 2
        assert is_valid_cas("50-78-2")

    def test_invalid_checksum(self):
        assert not is_valid_cas("50-78-3")
        assert not is_valid_cas("50-78-4")

    def test_invalid_format(self):
        assert not is_valid_cas("50-78")
        assert not is_valid_cas("50-78-22")
        assert not is_valid_cas("abc")
        assert not is_valid_cas("")

    def test_non_string(self):
        assert not is_valid_cas(50782)


class TestUNII:
    def test_valid(self):
        assert is_valid_unii("R16CO5Y76E")  # aspirin
        assert is_valid_unii("9NEZ333N27")  # caffeine

    def test_invalid(self):
        assert not is_valid_unii("R16CO5Y7")  # too short
        assert not is_valid_unii("R16CO5Y76E1")  # too long
        assert not is_valid_unii("ABCDEFGHIJ")  # no digit
        assert not is_valid_unii("1234567890")  # no letter
        assert not is_valid_unii("")


class TestInChIKey:
    def test_valid(self):
        assert is_valid_inchikey("BSFYZMDRMSNJQR-UHFFFAOYSA-N")
        assert is_valid_inchikey("RYYVLZVUVIJVGH-UHFFFAOYSA-N")  # caffeine

    def test_invalid(self):
        assert not is_valid_inchikey("BSFYZMDRMSNJQR")
        assert is_valid_inchikey("bsfyzmdrmsnjqr-uhfffaoysa-n")  # case-insensitive
        assert not is_valid_inchikey("BSFYZMDRMSNJQR-UHFFFAOYSA")  # truncated block 3
        assert not is_valid_inchikey("")


class TestInChI:
    def test_valid(self):
        assert is_valid_inchi("InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)")
        assert is_valid_inchi("InChI=1/NaCl")

    def test_invalid(self):
        assert not is_valid_inchi("InChI/C9H8O4")
        assert not is_valid_inchi("BSFYZMDRMSNJQR")
        assert not is_valid_inchi("")


class TestIdentifiers:
    def test_chebi(self):
        assert is_valid_chebi("CHEBI:15377")
        assert is_valid_chebi("15377")
        assert not is_valid_chebi("CHEBI:")
        assert not is_valid_chebi("CHEBI:abc")

    def test_chembl(self):
        assert is_valid_chembl("CHEMBL25")
        assert not is_valid_chembl("CHEMBL")
        assert not is_valid_chembl("25")

    def test_kegg(self):
        assert is_valid_kegg("C00001")
        assert is_valid_kegg("D00225")
        assert not is_valid_kegg("C1")

    def test_mesh(self):
        assert is_valid_mesh("D000001")
        assert not is_valid_mesh("D1")
        assert not is_valid_mesh("MESH:0001")

    def test_chemspider(self):
        assert is_valid_chemspider("238")
        assert not is_valid_chemspider("abc")

    def test_atc(self):
        assert is_valid_atc_code("N02", "BA01")
        assert is_valid_atc_code("A01")
        assert not is_valid_atc_code("N2", "BA01")
        assert not is_valid_atc_code("N02", "BA012")
        assert not is_valid_atc_code("")

    def test_setid(self):
        assert is_valid_setid("85c02768-7b96-4c48-8e67-6716fccd46fe")
        assert not is_valid_setid("85c027687b964c488e676716fccd46fe")
        assert not is_valid_setid("not-a-uuid")


class TestValidateIdentifierFields:
    def test_clean_data(self):
        data = {
            "cas_number": "50-78-2",
            "unii": "R16CO5Y76E",
            "inchikey": "BSFYZMDRMSNJQR-UHFFFAOYSA-N",
            "chebi_id": "CHEBI:15377",
            "chembl_id": "CHEMBL25",
            "atc_prefix": "N02",
            "atc_suffix": "BA01",
        }
        assert validate_identifier_fields(data) == []

    def test_violations_reported(self):
        data = {
            "cas_number": "50-78-3",  # bad checksum
            "unii": "SHORT",
            "inchikey": "garbage",
            "chebi_id": "CHEBI:abc",
            "chembl_id": "CHEMBL",
            "kegg_id": "C1",
            "mesh_id": "D1",
            "chemspider_id": "abc",
            "atc_prefix": "N2",
            "dailymed_id": "not-a-uuid",
        }
        violations = validate_identifier_fields(data)
        fields = {v[0] for v in violations}
        assert fields == {
            "cas_number", "unii", "inchikey", "chebi_id", "chembl_id",
            "kegg_id", "mesh_id", "chemspider_id", "atc_code", "dailymed_id",
        }

    def test_missing_fields_are_skipped(self):
        assert validate_identifier_fields({}) == []


class TestNumericRanges:
    def test_extract_first_number(self):
        assert extract_first_number("135 °C") == 135.0
        assert extract_first_number("1.2-1.5 g/cm3") == 1.2
        assert extract_first_number("no data") is None
        assert extract_first_number("") is None
        assert extract_first_number(None) is None

    def test_plausible_values_pass(self):
        data = {
            "melting_point": "135 °C",
            "boiling_point": "140 °C",
            "density": "1.08 g/cm3",
            "pka": "3.5",
            "refractive_index": "1.5",
        }
        assert check_numeric_ranges(data) == []

    def test_implausible_values_flagged(self):
        data = {"melting_point": "99999 °C", "density": "-5 g/cm3"}
        violations = check_numeric_ranges(data)
        assert {v[0] for v in violations} == {"melting_point", "density"}

    def test_missing_values_skipped(self):
        assert check_numeric_ranges({}) == []


class TestCompoundConsistency:
    ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"

    def test_consistent_data_passes(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {
            "molecular_formula": "C9H8O4",
            "molecular_weight": 180.16,
            "inchikey": "BSFYZMDRMSNJQR-UHFFFAOYSA-N",
        }
        assert check_compound_consistency(self.ASPIRIN_SMILES, data, mol) == []

    def test_formula_mismatch_flagged(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {"molecular_formula": "C8H8O4"}
        violations = check_compound_consistency(self.ASPIRIN_SMILES, data, mol)
        assert any(v[0] == "molecular_formula" for v in violations)

    def test_formula_whitespace_case_insensitive(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {"molecular_formula": "c9h8o4 "}
        assert check_compound_consistency(self.ASPIRIN_SMILES, data, mol) == []

    def test_mw_mismatch_flagged(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {"molecular_weight": 999.0}
        violations = check_compound_consistency(self.ASPIRIN_SMILES, data, mol)
        assert any(v[0] == "molecular_weight" for v in violations)

    def test_unparseable_mw_flagged(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {"molecular_weight": "garbage"}
        violations = check_compound_consistency(self.ASPIRIN_SMILES, data, mol)
        assert any(v[0] == "molecular_weight" for v in violations)

    def test_invalid_mol_returns_no_violations(self):
        data = {"molecular_formula": "C9H8O4"}
        assert check_compound_consistency("not-a-smiles", data) == []

    def test_bad_inchikey_flagged(self):
        mol = Chem.MolFromSmiles(self.ASPIRIN_SMILES)
        data = {"inchikey": "BADKEY"}
        violations = check_compound_consistency(self.ASPIRIN_SMILES, data, mol)
        assert any(v[0] == "inchikey" for v in violations)
