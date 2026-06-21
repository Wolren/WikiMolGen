# WikiMolGen

Generate 2D and 3D molecular visualizations from PubChem or SMILES — RDKit and PyMOL-based tool

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Originally developed for generating molecular structure images for Wikipedia, WikiMolGen provides a Python API, CLI, and a web interface for creating 2D SVG diagrams and 3D rendered structures.

```mermaid
flowchart LR
    A["Compound Name"] --> D{Parse}
    B["PubChem CID"] --> D
    C["SMILES"] --> D
    D --> E["RDKit"]
    E --> F["2D SVG"]
    E --> G["SDF Conformer"]
    G --> H["PyMOL"]
    H --> I["3D PNG"]
    J["PDB ID"] --> H
    D --> K["PubChem Metadata"]
    K --> L["Wikipedia Templates"]
    style F stroke:#4caf50
    style I stroke:#4caf50
    style L stroke:#4caf50
```

## Installation

### Basic (2D only)
```
pip install wikimolgen
```

### Full (2D + 3D with PyMOL)
```
conda create -n wikimolgen python=3.10
conda activate wikimolgen
conda install -c conda-forge rdkit pubchempy pymol-open-source
pip install wikimolgen
```

### Development
```
git clone https://github.com/Wolren/wikimolgen.git
cd wikimolgen
pip install -e ".[dev]"
```

## Web Interface

The Streamlit-based web interface provides an interactive dashboard for generating molecular visualizations with full control over rendering, styling, and Wikipedia metadata.

**Features:**
- **3 modes**: 2D (SVG), 3D (ray-traced PNG), and Protein (PDB cartoon)
- **Rich controls**: atom coloring, lighting, transparency, ray tracing, conformer generation
- **Wikipedia tooling**: auto-generated Infobox drug/chembox templates, metadata, and Commons upload links

```
streamlit run web/app.py
```

## CLI

```
wikimolgen 2d --compound aspirin --output aspirin.svg
wikimolgen 3d --compound 5284583 --render --output-base lsd
```

## License
MIT - see [LICENSE](LICENSE)
