import pymol2
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolfiles

smiles = "CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C"
mol = Chem.MolFromSmiles(smiles)
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, randomSeed=1)
AllChem.MMFFOptimizeMolecule(mol)
rdmolfiles.MolToMolFile(mol, "4-MeO-DiPT-3d-sticks.sdf")

with pymol2.PyMOL() as pymol:
    cmd = pymol.cmd
    cmd.load("4-MeO-DiPT-3d-sticks.sdf")
    cmd.hide("everything")
    cmd.show("sticks", "all")
    cmd.show("spheres", "all")
    cmd.bg_color("white")

    # Elements
    cmd.color("gray25", "elem C")
    cmd.color("blue", "elem N")
    cmd.color("red", "elem O")
    cmd.color("gray85", "elem H")

    # Sticks
    cmd.set("stick_radius", 0.2)
    cmd.set("stick_color", "gray40")

    # Sphere
    cmd.set("sphere_scale", 0.3)
    cmd.set("sphere_quality", 4)

    # Stick Ball
    cmd.set("stick_ball", "on")
    cmd.set("stick_ball_ratio", 1.8)
    cmd.set("stick_quality", 30)

    # General
    cmd.set("ambient", 0.25)
    cmd.set("specular", 1.0)
    cmd.set("shininess", 30)
    cmd.set("ray_shadows", 0)
    cmd.set("antialias", 2)
    cmd.set("ray_opaque_background", 0)

    cmd.set("depth_cue", 0)

    cmd.zoom("all", buffer=2.0)
    cmd.orient("all")
    cmd.turn("x", 0)
    cmd.turn("y", 200)

    pymol.cmd.png("4-MeO-DiPT-3d-sticks.png", width=1320, height=990)



