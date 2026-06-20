"""Tests for wikimolgen/sources/pubchem_experimental.py — mocked PubChem PUG View JSON."""

from unittest.mock import patch

import pytest

from wikimolgen.sources.pubchem_experimental import fetch_experimental_data


# ── helpers to build PUG View JSON structures ──────────────────────────


def _leaf_section(heading, str_value=None, number_value=None, unit=None):
    """Build a PUG View leaf ``Section`` with ``Information``."""
    section = {"TOCHeading": heading}
    info = {}
    if str_value is not None:
        info["Value"] = {"StringWithMarkup": [{"String": str_value}]}
    elif number_value is not None:
        v = {"Number": [number_value]}
        if unit:
            v["Unit"] = unit
        info["Value"] = v
    if info:
        section["Information"] = [info]
    return section


def _container_section(heading, subsections):
    """Build a PUG View container ``Section`` with nested ``Section`` s."""
    return {"TOCHeading": heading, "Section": subsections}


def _mock_record(
    melting=None,
    boiling=None,
    density=None,
    appearance=None,
    flash_point=None,
    solubility=None,
    vapor_pressure=None,
    decomposition=None,
    pka=None,
    odor=None,
    autoignition=None,
    refractory=None,
    viscosity=None,
    optical_rotation=None,
    henry=None,
    logp_exp=None,
    un_number=None,
    ec_number=None,
    rtecs=None,
    include_ghs=False,
    include_toxicity=False,
):
    """Build a sample PUG View ``Record`` with given experimental / safety data."""
    phys_subs = []

    exp_props = []
    for name, val in [
        ("Melting Point", melting),
        ("Boiling Point", boiling),
        ("Density", density),
        ("Physical Description", appearance),
        ("Flash Point", flash_point),
        ("Solubility", solubility),
        ("Vapor Pressure", vapor_pressure),
        ("Decomposition", decomposition),
        ("Dissociation Constants", pka),
        ("Odor", odor),
        ("Autoignition Temperature", autoignition),
        ("Refractive Index", refractory),
        ("Viscosity", viscosity),
        ("Optical Rotation", optical_rotation),
        ("Henry's Law Constant", henry),
        ("LogP", logp_exp),
    ]:
        if val is not None:
            exp_props.append(_leaf_section(name, str_value=val))

    if exp_props:
        phys_subs.append(_container_section("Experimental Properties", exp_props))

    if phys_subs:
        phys_section = _container_section("Chemical and Physical Properties", phys_subs)
    else:
        phys_section = _container_section("Chemical and Physical Properties", [])

    sections = [phys_section]

    # Safety and Hazards
    if include_ghs:
        ghs_items = []
        ghs_information = []

        pictograms = include_ghs.get("pictograms", [])
        if pictograms:
            markup = []
            for pic in pictograms:
                markup.append(
                    {
                        "Type": "Icon",
                        "URL": f"https://pubchem.ncbi.nlm.nih.gov/images/ghs/{pic}.svg",
                    }
                )
            ghs_information.append(
                {
                    "Name": "Pictogram(s)",
                    "Value": {"StringWithMarkup": [{"String": "", "Markup": markup}]},
                }
            )

        if include_ghs.get("signal"):
            ghs_information.append(
                {
                    "Name": "Signal",
                    "Value": {"StringWithMarkup": [{"String": include_ghs["signal"]}]},
                }
            )

        if include_ghs.get("h_statements"):
            ghs_information.append(
                {
                    "Name": "GHS Hazard Statements",
                    "Value": {"StringWithMarkup": [{"String": include_ghs["h_statements"]}]},
                }
            )

        if include_ghs.get("p_statements"):
            ghs_information.append(
                {
                    "Name": "Precautionary Statement Codes",
                    "Value": {"StringWithMarkup": [{"String": include_ghs["p_statements"]}]},
                }
            )

        if ghs_information:
            hazard_id_section = _container_section(
                "Hazards Identification",
                [
                    {
                        "TOCHeading": "GHS Classification",
                        "Information": ghs_information,
                    }
                ],
            )
            safety = _container_section("Safety and Hazards", [hazard_id_section])
            sections.append(safety)

    # Toxicity
    if include_toxicity:
        tox_data = []
        for line in include_toxicity:
            tox_data.append(
                {
                    "TOCHeading": "Toxicity Data",
                    "Information": [{"Value": {"StringWithMarkup": [{"String": line}]}}],
                }
            )
        toxicity_section = _container_section(
            "Toxicity",
            [
                _container_section(
                    "Toxicological Information",
                    tox_data,
                )
            ],
        )
        sections.append(toxicity_section)

    # Names and Identifiers → Other Identifiers
    ident_subs = []
    for heading, val in [
        ("UN Number", un_number),
        ("European Community (EC) Number", ec_number),
        ("RTECS Number", rtecs),
    ]:
        if val:
            ident_subs.append(_leaf_section(heading, str_value=val))

    if ident_subs:
        names_section = _container_section(
            "Names and Identifiers",
            [_container_section("Other Identifiers", ident_subs)],
        )
        sections.append(names_section)

    return {"Record": {"RecordNumber": 2244, "RecordTitle": "Aspirin", "Section": sections}}


# ── tests ──────────────────────────────────────────────────────────────


class TestFetchExperimentalData:
    def test_successful_fetch(self):
        mock_data = _mock_record(
            melting="135 °C",
            boiling="140 °C",
            density="1.5 g/cm³",
            appearance="white powder",
            solubility="10 mg/mL",
        )
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["melting_point"] == "135 °C"
            assert result["boiling_point"] == "140 °C"
            assert result["density"] == "1.5 g/cm³"
            assert result["appearance"] == "white powder"
            assert result["solubility"] == "10 mg/mL"

    def test_partial_data(self):
        mock_data = _mock_record(melting="100 °C")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["melting_point"] == "100 °C"
            assert "boiling_point" not in result

    def test_empty_record(self):
        mock_data = {"Record": {"Section": []}}
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result == {}

    def test_no_sections(self):
        mock_data = {"Record": {}}
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result == {}

    def test_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("PubChem API failed")
            with pytest.raises(Exception, match="PubChem API failed"):
                fetch_experimental_data(2244)

    def test_string_cid(self):
        mock_data = _mock_record(melting="50 °C")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data("2244")
            assert result["melting_point"] == "50 °C"

    def test_pka(self):
        mock_data = _mock_record(pka="3.5")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["pka"] == "3.5"

    def test_odor(self):
        mock_data = _mock_record(odor="Odorless")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["odor"] == "Odorless"

    def test_vapor_pressure(self):
        mock_data = _mock_record(vapor_pressure="0.1 mmHg")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["vapor_pressure"] == "0.1 mmHg"

    def test_ghs_data(self):
        ghs = {
            "pictograms": ["GHS07", "GHS06"],
            "signal": "Warning",
            "h_statements": "H302: Harmful if swallowed; H319: Causes eye irritation",
            "p_statements": "P261, P264, P270",
        }
        mock_data = _mock_record(include_ghs=ghs)
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert "ghs_pictograms" in result
            assert "{{GHS07}}" in result["ghs_pictograms"]
            assert "{{GHS06}}" in result["ghs_pictograms"]
            assert result["ghs_signal_word"] == "Warning"
            assert "H302" in result["h_statements"]
            assert "P261" in result["p_statements"]

    def test_toxicity(self):
        tox = ["LD50 Oral - Rat - 950 mg/kg", "LD50 Dermal - Rabbit - 2000 mg/kg"]
        mock_data = _mock_record(include_toxicity=tox)
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert "ld50" in result
            assert "LD50 Oral" in result["ld50"]
            assert "toxicity_data" in result

    def test_identifiers(self):
        mock_data = _mock_record(un_number="2811", ec_number="200-064-1", rtecs="VO0700000")
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["un_number"] == "2811"
            assert result["ec_number"] == "200-064-1"
            assert result["rtecs"] == "VO0700000"

    def test_all_physical_props(self):
        mock_data = _mock_record(
            melting="135 °C",
            boiling="140 °C",
            flash_point="150 °F",
            solubility="10 mg/mL",
            vapor_pressure="0.01 mmHg",
            density="1.5 g/cm³",
            decomposition="140 °C",
            appearance="White solid",
            odor="Odorless",
            pka="3.5",
            autoignition="400 °C",
            refractory="1.5",
            viscosity="1.0 cP",
            optical_rotation="-5.0°",
            henry="1.2E-7 atm·m³/mol",
            logp_exp="1.19",
        )
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_data
            result = fetch_experimental_data(2244)
            assert result["melting_point"] == "135 °C"
            assert result["boiling_point"] == "140 °C"
            assert result["flash_point"] == "150 °F"
            assert result["solubility"] == "10 mg/mL"
            assert result["vapor_pressure"] == "0.01 mmHg"
            assert result["density"] == "1.5 g/cm³"
            assert result["decomposition"] == "140 °C"
            assert result["appearance"] == "White solid"
            assert result["odor"] == "Odorless"
            assert result["pka"] == "3.5"
            assert result["autoignition_point"] == "400 °C"
            assert result["refractive_index"] == "1.5"
            assert result["viscosity"] == "1.0 cP"
            assert result["optical_rotation"] == "-5.0°"
            assert result["henry_constant"] == "1.2E-7 atm·m³/mol"
            assert result["logp_experimental"] == "1.19"
