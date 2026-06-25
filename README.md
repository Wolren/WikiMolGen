[![License](https://img.shields.io/github/license/Wolren/WikiMolGen)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen/commits)
[![Issues](https://img.shields.io/github/issues/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen/issues)
[![Repo size](https://img.shields.io/github/repo-size/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](pyproject.toml)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit)](web/app.py)
[![RDKit](https://img.shields.io/badge/RDKit-2023.09-green)](requirements.txt)

# WikiMolGen

Generate 2D and 3D molecular visualizations from PubChem or SMILES — RDKit and PyMOL-based tool

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
GNU General Public License v3.0 or later - see [LICENSE](LICENSE)