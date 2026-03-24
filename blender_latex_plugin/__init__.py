bl_info = {
    "name": "Blender LaTeX Plugin",
    "author": "Dasharadhan Mahalingam",
    "version": (1, 0),
    "blender": (4, 2, 2),
    "location": "VSE > Sidebar",
    "description": "A Blender plugin for typesetting using LaTeX",
    "category": "Import-Export",
}

# Dynamic reloading
if "bpy" in locals():
    import importlib

    importlib.reload(compiler)
    importlib.reload(vse_operators)
    importlib.reload(vse_ui)
else:
    from . import compiler, vse_operators, vse_ui

import bpy

modules = (
    vse_operators,
    vse_ui,
)


def register():
    for mod in modules:
        mod.register()


def unregister():
    for mod in reversed(modules):
        mod.unregister()
