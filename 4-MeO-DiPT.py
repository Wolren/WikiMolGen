import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D
import numpy as np

compound = pcp.Compound.from_cid(24802108)
smiles = compound.smiles

mol = Chem.MolFromSmiles(smiles)
AllChem.Compute2DCoords(mol)

# Rotate

conf = mol.GetConformer()
coords = np.array([[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y] for i in range(mol.GetNumAtoms())])
center = coords.mean(axis=0)
coords -= center

angle = np.pi
R = np.array([[np.cos(angle), -np.sin(angle)],
              [np.sin(angle),  np.cos(angle)]])
rotated = coords @ R.T

for i, pos in enumerate(rotated):
    conf.SetAtomPosition(i, (pos[0], pos[1], 0.0))

# Optimise size

min_x, min_y = rotated.min(axis=0)
max_x, max_y = rotated.max(axis=0)

margin = 0.5
min_x -= margin
min_y -= margin
max_x += margin
max_y += margin

scale = 30  # pixels per coordinate unit (tune if molecule is too big/small)
width = int((max_x - min_x) * scale)
height = int((max_y - min_y) * scale)

for i, pos in enumerate(rotated):
    new_x = pos[0] - min_x
    new_y = pos[1] - min_y
    conf.SetAtomPosition(i, (new_x, new_y, 0.0))

# Draw

drawer = rdMolDraw2D.MolDraw2DSVG(width, height)   # enlarge overall canvas size
opts = drawer.drawOptions()
opts.useBWAtomPalette()
opts.fixedBondLength = 35.0
opts.padding = 0.01
opts.minFontSize = 36
opts.setBackgroundColour((0, 0, 0, 0))

rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
drawer.FinishDrawing()

svg = drawer.GetDrawingText().replace('fill:white', 'fill:none')
with open("4-MeO-DiPT.svg", "w") as f:
    f.write(svg)


