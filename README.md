[![License](https://img.shields.io/github/license/Wolren/WikiMolGen)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen/commits)
[![Issues](https://img.shields.io/github/issues/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen/issues)
[![Repo size](https://img.shields.io/github/repo-size/Wolren/WikiMolGen)](https://github.com/Wolren/WikiMolGen)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](pyproject.toml)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit)(web/app.py)
[![RDKit](https://img.shields.io/badge/RDKit-2023.09-green)(requirements.txt)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Wolren/WikiMolGen/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Wolren/WikiMolGen)
[![Socket](https://img.shields.io/badge/Socket-Supply%20Chain%20Security-333?logo=socketdotdev)](https://socket.dev)

# WikiMolGen

Generate 2D and 3D molecular visualizations from PubChem or SMILES - RDKit and PyMOL-based tool

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Originally developed for generating molecular structure images for Wikipedia, WikiMolGen provides a Python API, CLI, and a website for creating 2D SVG diagrams and 3D rendered structures.

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

## Usage

### Python API
```python
from wikimolgen.rendering import MoleculeGenerator2D, MoleculeGenerator3D

# 2D: MoleculeGenerator2D(identifier, auto_orient=True).generate(output_path)
# 3D: MoleculeGenerator3D(identifier).generate(render=True, output_base="output")
```

### CLI
```
wikimolgen 2d --compound aspirin --output aspirin.svg
wikimolgen 3d --compound 5284583 --render --output-base lsd
```

### Web Interface
```bash
streamlit run web/app.py
```

## License
MIT - see [LICENSE](LICENSE)