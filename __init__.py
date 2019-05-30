bl_info = {
    "name": "Cesium ion",
    "description":
    "Upload and tile models with Cesium ion. https://cesium.com",
    "author": "Analytical Graphics, Inc.",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Import-Export"
}


# RELOAD PACKAGE on Refresh
def reload_package(module_dict_main):
    import importlib
    from pathlib import Path

    def reload_package_recursive(current_dir, module_dict):
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue

            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)


if "bpy" in locals():
    reload_package(locals())

import bpy
from bpy.props import PointerProperty
from bpy.app.handlers import persistent

from .operators import *
from .panels import *
from .cache import load_properties

__classes__ = [
    UserProperties, UserPreferences, ExportProperties, ExportPanel,
    OAuthOperator, GetTokenOperator, ClearTokenOperator, ExportUploadOperator
]

register_classes, unregister_classes = bpy.utils\
    .register_classes_factory(__classes__)


def register():
    register_classes()
    bpy.types.WindowManager.csm_user = PointerProperty(type=UserProperties)
    bpy.types.Scene.csm_export = PointerProperty(type=ExportProperties)

    # Update login persistence
    @persistent
    def on_load(ignore):
        load_properties(bpy.context.window_manager.csm_user)

    bpy.app.handlers.load_post.append(on_load)


def unregister():
    unregister_classes()
    del bpy.types.WindowManager.csm_user
    del bpy.types.Scene.csm_export
    OAuthOperator.stop()
