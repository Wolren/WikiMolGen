"""Tests for wikimolgen/cli/cli.py — parser creation and run functions."""

from unittest.mock import MagicMock, patch

import pytest

from wikimolgen.cli.cli import create_parser, run_2d, run_3d


class TestCreateParser:
    def test_returns_argument_parser(self):
        parser = create_parser()
        assert parser.prog == "wikimolgen"

    def test_has_subcommands(self):
        parser = create_parser()
        subactions = parser._subparsers._group_actions
        assert len(subactions) == 1
        choices = subactions[0].choices
        assert "2d" in choices
        assert "3d" in choices
        assert "protein" in choices

    def test_2d_subcommand_args(self):
        parser = create_parser()
        args = parser.parse_args(["2d", "--compound", "aspirin"])
        assert args.mode == "2d"
        assert args.compound == "aspirin"
        assert args.output == "molecule_2d.svg"
        assert args.template is None

    def test_2d_all_args(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "2d",
                "--compound",
                "2244",
                "--output",
                "out.svg",
                "--template",
                "wikipedia_2d",
                "--color-template",
                "cpk_standard",
                "--angle",
                "90",
                "--auto-orient",
                "--scale",
                "40",
                "--use-bw",
                "--transparent-bg",
            ]
        )
        assert args.compound == "2244"
        assert args.output == "out.svg"
        assert args.template == "wikipedia_2d"
        assert args.color_template == "cpk_standard"
        assert args.angle == 90.0
        assert args.auto_orient is True
        assert args.scale == 40.0
        assert args.use_bw is True
        assert args.transparent_bg is True

    def test_3d_subcommand_args(self):
        parser = create_parser()
        args = parser.parse_args(["3d", "--compound", "aspirin"])
        assert args.mode == "3d"
        assert args.compound == "aspirin"
        assert args.render is False
        assert args.bg_color == "white"

    def test_3d_all_args(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "3d",
                "--compound",
                "5284583",
                "--output-base",
                "out",
                "--template",
                "high_quality_3d",
                "--color-template",
                "jmol",
                "--render",
                "--ray-trace",
                "--ray-shadows",
                "--x-rotation",
                "10",
                "--y-rotation",
                "20",
                "--bg-color",
                "black",
            ]
        )
        assert args.compound == "5284583"
        assert args.output_base == "out"
        assert args.render is True
        assert args.ray_trace is True
        assert args.ray_shadows is True
        assert args.x_rotation == 10.0
        assert args.y_rotation == 20.0
        assert args.bg_color == "black"

    def test_protein_subcommand_args(self):
        parser = create_parser()
        args = parser.parse_args(["protein", "8F7W"])
        assert args.mode == "protein"
        assert args.pdb_id == "8F7W"
        assert args.color_scheme == "secondary_structure"

    def test_protein_with_all_args(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "protein",
                "8F7W",
                "--output",
                "protein.png",
                "--color-scheme",
                "rainbow",
                "--no-ligand",
                "--show-water",
                "--ray-trace",
            ]
        )
        assert args.pdb_id == "8F7W"
        assert args.output == "protein.png"
        assert args.color_scheme == "rainbow"
        assert args.show_ligand is False
        assert args.show_water is True
        assert args.ray_trace is True


class TestRun2D:
    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator2D")
    def test_basic_run(self, MockGen2D, MockConfigLoader):
        mock_config = MagicMock()
        MockConfigLoader.get_2d_config.return_value = mock_config
        mock_gen = MagicMock()
        MockGen2D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(["2d", "--compound", "aspirin"])
        run_2d(args)

        MockConfigLoader.get_2d_config.assert_called_once()
        MockGen2D.assert_called_once_with(identifier="aspirin", config=mock_config)
        mock_gen.draw.assert_called_once_with(output="molecule_2d.svg")

    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator2D")
    def test_with_template(self, MockGen2D, MockConfigLoader):
        mock_gen = MagicMock()
        MockGen2D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(
            [
                "2d",
                "--compound",
                "aspirin",
                "--template",
                "wikipedia_2d",
            ]
        )
        run_2d(args)

        mock_gen.load_settings_template.assert_called_once_with("wikipedia_2d")

    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator2D")
    def test_with_color_template(self, MockGen2D, MockConfigLoader):
        mock_gen = MagicMock()
        MockGen2D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(
            [
                "2d",
                "--compound",
                "aspirin",
                "--color-template",
                "cpk_standard",
            ]
        )
        run_2d(args)

        mock_gen.load_color_template.assert_called_once_with("cpk_standard")


class TestRun3D:
    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator3D")
    def test_basic_run(self, MockGen3D, MockConfigLoader):
        mock_config = MagicMock()
        MockConfigLoader.get_3d_config.return_value = mock_config
        mock_gen = MagicMock()
        MockGen3D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(["3d", "--compound", "aspirin"])
        run_3d(args)

        MockConfigLoader.get_3d_config.assert_called_once()
        MockGen3D.assert_called_once_with(identifier="aspirin", config=mock_config)
        mock_gen.generate.assert_called_once_with(
            optimize=True,
            force_field="MMFF94",
            render=False,
            output_base=None,
        )

    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator3D")
    def test_with_ray_trace_and_shadows(self, MockGen3D, MockConfigLoader):
        mock_config = MagicMock()
        MockConfigLoader.get_3d_config.return_value = mock_config
        mock_gen = MagicMock()
        MockGen3D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(
            [
                "3d",
                "--compound",
                "aspirin",
                "--render",
                "--ray-trace",
                "--ray-shadows",
            ]
        )
        run_3d(args)

        overrides = MockConfigLoader.get_3d_config.call_args[1]["overrides"]
        assert overrides["ray_trace_mode"] == 1
        assert overrides["ray_shadows"] == 1

    @patch("wikimolgen.cli.cli.ConfigLoader")
    @patch("wikimolgen.cli.cli.MoleculeGenerator3D")
    def test_with_template(self, MockGen3D, MockConfigLoader):
        mock_gen = MagicMock()
        MockGen3D.return_value = mock_gen

        parser = create_parser()
        args = parser.parse_args(
            [
                "3d",
                "--compound",
                "aspirin",
                "--template",
                "high_quality_3d",
            ]
        )
        run_3d(args)

        mock_gen.load_settings_template.assert_called_once_with("high_quality_3d")
