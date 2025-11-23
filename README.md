# WikiMolGen

Generate 2D and 3D molecular visualizations from PubChem or SMILES - RDKit and PyMOL-based tool

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/PyPI-v1.0.0-blue.svg)](https://pypi.org/project/wikimolgen/)

Originally developed for generating molecular structure images for Wikipedia, WikiMolGen provides a Python API, CLI, and a website for creating 2D SVG diagrams and 3D rendered structures.

---

## Features

### Core Capabilities
- **2D SVG Generation**: Vector graphics with automatic orientation
- **3D Conformer Generation**: ETKDG-based 3D structure generation with MMFF94/UFF force field optimization
- **PyMOL Rendering**: Ray-traced molecular images with lighting control
- **Flexible Input**: Supports PubChem CID, compound names, or direct SMILES strings
- **Auto-Orientation**: Automatic rotation for optimal viewing angles (2D & 3D)
- **Template System**: Handling of predefined and custom templates for consistent styling

---

## 📦 Installation

### Basic Installation (2D only)
```bash
pip install wikimolgen
```

This installs the core library with 2D SVG generation support.

### Full Installation (2D + 3D with PyMOL)
For 3D rendering capabilities, install with conda (recommended):

```bash
conda create -n wikimolgen python=3.10
conda activate wikimolgen
conda install -c conda-forge rdkit pubchempy pymol-open-source
pip install wikimolgen
```

### Development Installation
```bash
git clone https://github.com/Wolren/wikimolgen.git
cd wikimolgen
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Python API

#### 2D Molecular Structures

```python
from wikimolgen.rendering import MoleculeGenerator2D

# Generate from PubChem CID
gen = MoleculeGenerator2D("24802108")
gen.generate("4-MeO-DiPT.svg")

# Generate from compound name with auto-orientation
gen = MoleculeGenerator2D("aspirin", auto_orient=True, scale=40)
gen.generate("aspirin.svg")

# Generate from SMILES with custom styling
gen = MoleculeGenerator2D(
    "CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C",
    auto_orient=True,
    bond_length=50.0,
    min_font_size=42,
    use_bw_palette=False  # Use color palette
)
gen.generate("molecule.svg")
```

#### 3D Molecular Structures

```python
from wikimolgen.rendering import MoleculeGenerator3D

# Generate and optimize 3D structure (SDF file only)
gen = MoleculeGenerator3D("caffeine")
sdf_path, _ = gen.generate(optimize=True, force_field="MMFF94")

# Generate with PyMOL rendering (requires PyMOL installation)
gen = MoleculeGenerator3D("DMT", random_seed=42)
gen.configure_rendering(
    width=1920,
    height=1080,
    auto_orient=True,  # Automatic optimal orientation
    stick_radius=0.2,
    sphere_scale=0.3
)
sdf_path, png_path = gen.generate(render=True, output_base="dmt_3d")
```

#### Using Templates

```python
from wikimolgen.predefined_templates import list_predefined_templates, apply_template

# List available templates
templates = list_predefined_templates()
print(templates["settings_templates"])  # ['publication_2d', 'wikipedia_2d', ...]
print(templates["color_templates"])     # ['cpk_standard', 'wikipedia_colors', ...]

# Generate with predefined template
gen = MoleculeGenerator2D("glucose")
apply_template(gen, "publication_2d")
gen.generate("glucose.svg")

# Generate 3D with color template
gen = MoleculeGenerator3D("mescaline")
gen.configure_rendering(color_template="cpk_standard")
gen.generate(render=True, output_base="mescaline_3d")
```

### Command Line Interface

#### 2D Generation

```bash
# Basic usage with auto-orientation
wikimolgen 2d --compound aspirin --output aspirin.svg

# Using PubChem CID with custom settings
wikimolgen 2d --compound 24802108 --output 4-MeO-DiPT.svg --scale 40 --bond-length 50

# SMILES input with template
wikimolgen 2d --compound "CC(C)NCC(O)c1ccc(O)c(O)c1" --template publication_2d --output epinephrine.svg

# Manual rotation (disable auto-orient)
wikimolgen 2d --compound "glucose" --no-auto-orient --angle 45 --output glucose_rotated.svg
```

#### 3D Generation

```bash
# Generate SDF with optimization
wikimolgen 3d --compound "DMT" --optimize --force-field MMFF94 --output-base dmt

# Render with PyMOL using auto-orientation
wikimolgen 3d --compound 5284583 --render --width 1920 --height 1080 --output-base lsd

# Custom rendering with manual rotation
wikimolgen 3d --compound "mescaline" --render \
    --no-auto-orient --x-rotation 0 --y-rotation 200 --z-rotation 0 \
    --stick-radius 0.25 --sphere-scale 0.35 \
    --output-base mescaline_custom

# Using templates
wikimolgen 3d --compound "psilocin" --render --template high_quality_3d --output-base psilocin
```

#### Batch Processing

```bash
# Process multiple compounds
for compound in "aspirin" "caffeine" "morphine"; do
    wikimolgen 2d --compound "$compound" --template publication_2d --output "${compound}.svg"
done

# Generate 3D structures for a list
cat compounds.txt | while read cid; do
    wikimolgen 3d --compound "$cid" --render --template high_quality_3d --output-base "molecule_${cid}"
done
```

---

## 📚 Documentation

### API Reference

#### `MoleculeGenerator2D`

Generate 2D molecular structure diagrams in SVG format.

**Constructor Parameters:**
```python
MoleculeGenerator2D(
    identifier: str,           # PubChem CID, name, or SMILES
    auto_orient: bool = True,  # Automatic optimal rotation
    angle_degrees: float | None = None,  # Manual rotation (degrees, if auto_orient=False)
    scale: float = 30.0,       # Pixels per coordinate unit
    margin: float = 0.5,       # Canvas margin
    bond_length: float = 45.0, # Bond length in pixels
    min_font_size: int = 36,   # Minimum atom label font size
    padding: float = 0.03,     # Padding around molecule
    use_bw_palette: bool = True,  # Black & white vs color
    transparent_background: bool = True  # Transparent background
)
```

**Methods:**
- `generate(output: str | Path) -> Path`: Generate and save SVG file
- **Attributes**: `identifier`, `smiles`, `compound_name`, `mol` (RDKit molecule object)

#### `MoleculeGenerator3D`

Generate 3D molecular structures with optional PyMOL rendering.

**Constructor Parameters:**
```python
MoleculeGenerator3D(
    identifier: str,         # PubChem CID, name, or SMILES
    random_seed: int = 1     # Random seed for conformer generation
)
```

**Methods:**
- `generate(optimize: bool = True, force_field: str = "MMFF94", render: bool = False, output_base: str = "output") -> tuple[Path, Path | None]`
  - Returns: `(sdf_path, png_path)` where `png_path` is `None` if `render=False`
- `configure_rendering(**kwargs)`: Update PyMOL rendering configuration
  - Common parameters: `width`, `height`, `auto_orient`, `x_rotation`, `y_rotation`, `z_rotation`, `stick_radius`, `sphere_scale`, `bg_color`

**Attributes:**
- `identifier`, `smiles`, `compound_name`, `mol`, `render_config`

#### Utility Functions

```python
from wikimolgen.core import fetch_compound, validate_smiles

# Fetch compound information from PubChem
smiles, name = fetch_compound("aspirin")

# Validate SMILES string
is_valid = validate_smiles("CCO")  # Returns bool
```

### Configuration Objects

#### `DrawingConfig` (2D)
Dataclass for 2D drawing configuration:
- `auto_orient`: Enable automatic rotation
- `angle`: Rotation angle in radians (used when auto_orient=False)
- `scale`: Pixels per coordinate unit
- `margin`: Canvas margin
- `bond_length`: Fixed bond length in pixels
- `min_font_size`: Minimum atom label font size
- `padding`: Padding around molecule
- `use_bw_palette`: Use black/white palette
- `transparent_background`: Transparent background

#### `RenderConfig` (3D)
Dataclass for 3D PyMOL rendering configuration:
- `auto_orient`: Enable automatic 3D orientation
- `width`, `height`: Image dimensions
- `x_rotation`, `y_rotation`, `z_rotation`: Manual rotation angles (degrees)
- `stick_radius`, `sphere_scale`: Molecular representation sizes
- `stick_ball_ratio`: Ratio between stick and sphere sizes
- `ambient`, `specular`, `shininess`: Lighting parameters
- `direct`, `reflect`: Directional and reflection lighting
- `depth_cue`: Fog effect for depth perception
- `bg_color`: Background color
- `element_colors`: Dict mapping element symbols to colors
- `auto_crop`: Automatically crop whitespace
- `crop_margin`: Margin for auto-cropping

### Template System

#### Predefined Settings Templates

**2D Templates:**
- `publication_2d`
- `wikipedia_2d`
- `high_contrast_2d`

**3D Templates:**
- `high_quality_3d`:
- `wikipedia_3d`:
- `fast_preview_3d`:

#### Predefined Color Templates

- `cpk_standard`
- `wikipedia_colors`
- `grayscale`
- `vibrant`

#### Using Templates

```python
from wikimolgen.predefined_templates import (
    list_predefined_templates,
    apply_template,
    load_settings_template,
    load_color_template
)

# List all available templates
templates = list_predefined_templates()

# Apply settings template to generator
gen = MoleculeGenerator2D("aspirin")
apply_template(gen, "publication_2d")

# Load template for inspection
config = load_settings_template("high_quality_3d")
print(config)  # Dict of configuration parameters

# Apply color template to 3D generator
gen = MoleculeGenerator3D("caffeine")
colors = load_color_template("cpk_standard")
gen.configure_rendering(element_colors=colors)
```

---

## 🎨 Examples

### Batch Processing Script

```python
from wikimolgen.rendering import MoleculeGenerator2D, MoleculeGenerator3D
from pathlib import Path

# Define output directory
output_dir = Path("molecules")
output_dir.mkdir(exist_ok=True)

# List of compounds
compounds = {
    "aspirin": "50-78-2",
    "caffeine": "58-08-2",
    "morphine": "57-27-2",
    "cocaine": "50-36-2"
}

# Generate 2D structures
for name, cid in compounds.items():
    print(f"Generating 2D structure for {name}...")
    gen = MoleculeGenerator2D(cid, auto_orient=True)
    gen.generate(output_dir / f"{name}_2d.svg")

# Generate 3D structures with rendering
for name, cid in compounds.items():
    print(f"Generating 3D structure for {name}...")
    gen = MoleculeGenerator3D(cid)
    gen.configure_rendering(auto_orient=True, width=1920, height=1080)
    gen.generate(render=True, output_base=str(output_dir / f"{name}_3d"))

print("Done! Check the 'molecules' directory.")
```

### Custom Styling Example

```python
from wikimolgen.rendering import MoleculeGenerator3D

# Create generator
gen = MoleculeGenerator3D("DMT")

# Configure custom rendering
gen.configure_rendering(
    # Image settings
    width=2560,
    height=1440,
    auto_crop=True,
    crop_margin=10,

    # Orientation (manual control)
    auto_orient=False,
    x_rotation=0,
    y_rotation=220,
    z_rotation=0,

    # Molecular representation
    stick_radius=0.25,
    sphere_scale=0.35,
    stick_ball_ratio=1.8,

    # Lighting
    ambient=0.3,
    specular=1.2,
    shininess=40,
    direct=0.6,
    reflect=0.5,

    # Colors
    bg_color="black",
    element_colors={
        "C": "white",
        "N": "lightblue",
        "O": "red",
        "H": "gray80"
    }
)

# Generate
gen.generate(render=True, output_base="dmt_custom")
```

### Wikipedia Integration Example

```python
from wikimolgen.rendering import MoleculeGenerator2D
from wikimolgen.predefined_templates import apply_template

def generate_wikipedia_image(compound_name: str, cid: str):
    """Generate Wikipedia-ready molecular structure image."""
    gen = MoleculeGenerator2D(cid)

    # Apply Wikipedia template
    apply_template(gen, "wikipedia_2d")

    # Generate SVG
    output_path = f"{compound_name}.svg"
    gen.generate(output_path)

    print(f"Generated {output_path}")
    print(f"SMILES: {gen.smiles}")
    print(f"Name: {gen.compound_name}")

    return output_path

# Example usage
generate_wikipedia_image("aspirin", "2244")
generate_wikipedia_image("caffeine", "2519")
```

---

## Project Structure

```
wikimolgen/
├── __init__.py                 # Package exports
├── core.py                     # Core utilities (PubChem, validation)
├── cli.py                      # Command-line interface
├── predefined_templates.py     # Template system
└── rendering/                  # Rendering subpackage
    ├── __init__.py
    ├── wikimol2d.py            # 2D SVG generation
    ├── wikimol3d.py            # 3D structure generation with PyMOL
    └── optimization.py         # Auto-orientation algorithms (PCA-based)
```

---

## How It Works

### 2D Generation Pipeline
1. **Input Processing**: Parse PubChem CID, compound name, or SMILES
2. **Molecule Loading**: Fetch from PubChem or parse SMILES with RDKit
3. **2D Coordinates**: Generate 2D coordinates using RDKit
4. **Auto-Orientation** (optional): Find optimal rotation using PCA analysis
5. **SVG Rendering**: Draw molecule using RDKit's SVG drawer
6. **Output**: Savey SVG file

### 3D Generation Pipeline
1. **Input Processing**: Parse identifier and load molecule
2. **Conformer Generation**: Generate 3D conformer using ETKDG algorithm
3. **Optimization**: Optimize geometry with MMFF94 or UFF force field
4. **Auto-Orientation** (optional): Calculate optimal viewing angle using PCA
5. **PyMOL Rendering** (optional): Render with PyMOL ray tracer
6. **Output**: SDF file + optional PNG image

### Auto-Orientation Algorithm
WikiMolGen uses Principal Component Analysis (PCA) to automatically determine optimal viewing angles:

**2D Auto-Orientation:**
- Analyzes 2D molecular coordinates
- Finds principal axis of molecular structure
- Rotates to maximize visual clarity

**3D Auto-Orientation:**
- Performs PCA on 3D conformer coordinates
- Aligns molecule along principal components
- Optimizes viewing angle for maximum feature visibility
- Adjusts zoom to fit molecule in frame

---

## Contributing

Contributions are welcome!

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **RDKit**: Open-source cheminformatics toolkit
- **PyMOL**: Molecular visualization system
- **PubChem**: NIH chemical database
- **Wikipedia**: Original use case and inspiration

---

## Contact & Support

- **GitHub Issues**: [https://github.com/Wolren/wikimolgen/issues](https://github.com/Wolren/wikimolgen/issues)
- **Email**: wolrenn@outlook.com

---

## Related Projects

- **Web Application**: See [web/README.md](web/README.md) for the interactive Streamlit web interface
- **RDKit**: [https://www.rdkit.org/](https://www.rdkit.org/)
- **PyMOL**: [https://pymol.org/](https://pymol.org/)
- **PubChem**: [https://pubchem.ncbi.nlm.nih.gov/](https://pubchem.ncbi.nlm.nih.gov/)
