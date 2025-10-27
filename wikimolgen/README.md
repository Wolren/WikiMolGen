# WikiMolGen

**Unified Molecular Structure Generator** - Generate publication-quality 2D and 3D molecular visualizations from PubChem or SMILES. Originally built for wikipedia

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **2D SVG Generation**: Publication-ready vector graphics with customizable styling
- **3D Conformer Generation**: High quality ETKDG-based 3D structure generation with force field optimization
- **PyMOL Rendering** - High-quality ray-traced molecular images
- **Flexible Input** - Supports PubChem CID, compound names, or direct SMILES
- **Class-Based API** - Type-annotated Python API with dataclasses
- **CLI Interface** - Command-line tool for batch processing
## Installation

### Basic Installation
```bash
pip install rdkit pubchempy numpy
```

### PyMOL Support (for 3D rendering)
```bash
conda install -c conda-forge rdkit pubchempy pymol-open-source
```
### Development Installation
```bash
git clone https://github.com/Wolren/wikimolgen.git
cd wikimolgen
pip install -e .
```

## Quick Start

### Python API

#### 2D Structures
```python
from wikimolgen import MoleculeGenerator2D

# From PubChem CID
gen = MoleculeGenerator2D("24802108")
gen.generate("4-MeO-DiPT.svg")

# From compound name
gen = MoleculeGenerator2D("psilocin", angle=0, scale=40)
gen.generate("psilocin.svg")

# From SMILES
gen = MoleculeGenerator2D("CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C")
gen.generate("custom.svg")
```

#### 3D Structures
```python
from wikimolgen import MoleculeGenerator3D

# Generate and optimize 3D structure
gen = MoleculeGenerator3D("24802108")
sdf_path, _ = gen.generate(optimize=True, force_field="MMFF94")

# With PyMOL rendering
gen = MoleculeGenerator3D("DMT", random_seed=42)
gen.configure_rendering(width=1920, height=1080, y_rotation=180)
sdf_path, png_path = gen.generate(render=True, output_base="dmt_3d")
```

### Command Line

#### 2D Generation
```bash
# Basic usage
wikimolgen 2d --compound 24802108 --output 4-MeO-DiPT.svg

# Custom styling
wikimolgen 2d --compound "psilocin" --angle 0 --scale 40 --font-size 42

# SMILES input
wikimolgen 2d --compound "CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C" --output test.svg
```

#### 3D Generation
```bash
# Generate SDF only
wikimolgen 3d --compound "DMT" --optimize --force-field MMFF94

# With PyMOL rendering
wikimolgen 3d --compound 5284583 --render --width 1920 --height 1080

# Custom output and rotation
wikimolgen 3d --compound "mescaline" --render --output-base mescaline --y-rotation 180
```

## Package Structure

```
wikimolgen/
├── __init__.py          # Package initialization and exports
├── core.py              # Shared utilities (PubChem fetching, validation)
├── wikimol2d.py         # 2D structure generation (MoleculeGenerator2D)
├── wikimol3d.py         # 3D structure generation (MoleculeGenerator3D)
└── cli.py               # Command-line interface
```

## API Reference

### `MoleculeGenerator2D`

Generate 2D molecular structure diagrams.

**Parameters:**
- `identifier`(str): PubChem CID, compound name, or SMILES
- `angle`(float): Rotation angle in radians (default: π)
- `scale`(float): Pixels per coordinate unit (default: 30.0)
- `margin`(float): Canvas margin (default: 0.5)
- `bond_length`(float): Fixed bond length in pixels (default: 35.0)
- `min_font_size`(int): Minimum atom label font size (default: 36)
- `use_bw_palette`(bool): Use black/white palette (default: True)
- `transparent_background`(bool): Transparent background (default: True)

**Methods:**
- `generate(output: str) -> Path`: Generate and save SVG

### `MoleculeGenerator3D`

Generate 3D molecular structures with conformer optimization.

**Parameters:**
- `identifier` (str): PubChem CID, compound name, or SMILES
- `random_seed` (int): Random seed for conformer generation (default: 1)

**Methods:**
- `generate(optimize: bool, force_field: str, render: bool, output_base: str) -> tuple[Path, Path | None]`
- `configure_rendering(**kwargs)`: Update PyMOL rendering settings

#### `fetch_compound(identifier: str) -> tuple[str, str]`

Fetch compound SMILES and name from PubChem.

**Returns:** `(smiles, compound_name)`

## Configuration

### 2D Drawing Config
Customize via `DrawingConfig` dataclass or constructor parameters:
- Rotation angle and scaling
- Bond length and font size
- Color palette (B&W or full color)
- Background transparency

### 3D Rendering Config
Customize via `RenderConfig` dataclass or `configure_rendering()`:
- Image dimensions (width, height)
- Stick/sphere properties (radius, scale, quality)
- Lighting (ambient, specular, shininess)
- Camera rotation (x, y, z)
- Element colors

## Dependencies

**Required:**
- Python 3.10+
- rdkit
- pubchempy
- numpy
- pymol2

## Examples

### Batch Processing
```python
from wikimolgen import MoleculeGenerator2D, MoleculeGenerator3D

compounds = ["psilocin", "DMT", "mescaline", "LSD"]

# Generate 2D structures
for name in compounds:
    gen = MoleculeGenerator2D(name)
    gen.generate(f"{name}_2d.svg")

# Generate 3D structures with rendering
for name in compounds:
    gen = MoleculeGenerator3D(name)
    gen.generate(render=True, output_base=f"{name}_3d")
```

### Custom Styling
```python
from wikimolgen import MoleculeGenerator3D

gen = MoleculeGenerator3D("24802108")
gen.configure_rendering(
    width=2560,
    height=1440,
    stick_radius=0.25,
    sphere_scale=0.35,
    y_rotation=220,
    bg_color="black",
    carbon_color="white",
)
gen.generate(render=True, output_base="custom_render")
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Citation

If you use wikimolgen in your research, please cite:

```bibtex
@software{wikimolgen2025,
  author = {Wolren},
  title = {wikimolgen: Unified Molecular Structure Generator},
  year = {2025},
  version = {1.0.0},
  url = {https://github.com/Wolren/wikimolgen}
}
```

