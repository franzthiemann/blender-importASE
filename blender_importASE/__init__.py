#!/usr/bin/env python

__author__ = "Hendrik Weiske"
__credits__ = ["Franz Thiemann"]
__version__ = "1.4"
__maintainer__ = "Hendrik Weiske"
__email__ = "hendrik.weiske@uni-leipzig.de"

bl_info = {
    "name": "ASE Importer",
    "description": "Import molecules using ASE",
    "author": "Hendrik Weiske",
    "version": (1, 4),
    "blender": (4, 1, 1),
    "location": "File > Import",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from ase import io
import ase
from ase.data import covalent_radii, colors
from ase.build import make_supercell
import numpy as np
from ase import Atoms
from os.path import join
import os
from .import_cubefiles import cube2vol
from .utils import setup_materials, group_atoms
from .drawobjects import draw_atoms, draw_bonds, draw_unit_cell
from .ui import import_ase_molecule


class ImportASEMolecule(bpy.types.Operator, ImportHelper):
    bl_idname = "import_mesh.ase"
    bl_label = "Import ASE Molecule"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".*"

    supercell1: bpy.props.IntVectorProperty(
        name="Supercell-vector",
        size=3,
        default=[1, 1, 1],
        min=0,
        subtype="XYZ"
    )
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="scaling the atoms",
        default=1.0,
        min=0.0,
        soft_max=10,
    )
    colorbonds: bpy.props.BoolProperty(
        name='colorbonds',
        description="Color the bonds according to the surrounding atoms",
        default=False,
    )
    fix_bonds: bpy.props.BoolProperty(
        name='Use Longbonds',
        description="Mitigates lines in the middle of bonds where individual bonds meet",
        default=True,
    )
    color: bpy.props.FloatProperty(
        name="color",
        description="color for gray bonds in BW-scale",
        default=0.6,
        min=0.0,
        max=1.0,
    )
    unit_cell: bpy.props.BoolProperty(
        name='unit_cell',
        description="Draw unit cell",
        default=False,
    )
    separate_collections: bpy.props.BoolProperty(
        name='separate_collections',
        description="separate collections by unit cell, atoms and bonds",
        default=False,
    )
    representation: bpy.props.EnumProperty(
        name="representation",
        description="select the representation for your structure",
        items=[
            ("Balls'n'Sticks", "Balls'n'Sticks", "Balls and sticks representaiton"),
            ("Licorice", "Licorice", "Licorice representation"),
            ('VDW', 'VDW', 'VDW Radii, no bonds'),
        ],
        default="Balls'n'Sticks"
    )
    read_density: bpy.props.BoolProperty(
        name='load e-density',
        description="load electron-density as volume and use a node-tree for the creation of isosurfaces (only .cube-files)",
        default=True,
    )
    zero_cell: bpy.props.BoolProperty(
        name='Assume zero centered cell',
        description="Calculations in AMS result in zero-centered cells. This will confuse the longbond algorithm and cause" \
                    "the atoms to lie outside the unit cell (if drawn). This option compensates for that.",
        default=False,
    )
    animate: bpy.props.BoolProperty(
        name='animate',
        description="animate trajectory (all traj-files readable by ASE)",
        default=True,
    )
    imageslice: bpy.props.IntProperty(
        name='nth-image',
        description='when loading long trajectories it is recommended not to use all images, since that will scale poorly depending on the number of bonds in the molecule and drastically influence performance',
        default=1
    )
    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
        description='List of files to be imported'
    )
    directory: bpy.props.StringProperty(
        name='folder',
        description='directory of file',
        subtype='DIR_PATH'
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Create Supercell")
        box.separator()
        # commented out because it throws errors, don't know what it does anyhow... -PM
        #box.operator("import_scene.my_format", text="Import")

        for i, text in enumerate(["X", "Y", "Z"]):
            row = box.row(align=True)
            row.prop(self, "supercell1", text=text, index=i, emboss=False, slider=True)
        layout.prop(self, "scale")
        layout.prop(self, 'colorbonds')
        layout.prop(self, 'fix_bonds')
        layout.prop(self, 'representation')
        layout.prop(self, 'color')
        layout.prop(self, 'unit_cell')
        layout.prop(self, 'separate_collections')
        layout.prop(self, 'read_density')
        layout.prop(self, 'zero_cell')
        layout.prop(self, 'animate')
        layout.prop(self,'imageslice')

    def execute(self, context):
        for file in self.files:
            filepath = join(self.directory, file.name)
            matrix = np.diag(self.supercell1)
            default = [1, 0, 0, 0, 1, 0, 0, 0, 1]
            SUPERCELL = False
            for n, i in enumerate(self.supercell1):
                if i != default[n]:
                    SUPERCELL = True
                break
            import_ase_molecule(filepath, file.name, matrix,
                                color=self.color, colorbonds=self.colorbonds, fix_bonds=self.fix_bonds, scale=self.scale,
                                unit_cell=self.unit_cell, representation=self.representation,
                                separate_collections=self.separate_collections,
                                read_density=self.read_density, SUPERCELL=SUPERCELL, 
                                shift_cell=self.zero_cell,imageslice=self.imageslice,
                                animate=self.animate
                                )
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func_import(self, context):
    self.layout.operator(ImportASEMolecule.bl_idname, text="ASE Molecule (.*)")


def register():
    bpy.utils.register_class(ImportASEMolecule)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportASEMolecule)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
