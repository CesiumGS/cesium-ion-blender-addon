bl_info = {
    "name": "Cesium ion",
    "description":
    "Upload and tile models with Cesium ion. https://cesium.com",
    "author": "Analytical Graphics, Inc.",
    "wiki_url":
    "https://github.com/AnalyticalGraphicsInc/ion-blender-exporter",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Cesium ion",
    "category": "Import-Export"
}

import bpy
from bpy.props import PointerProperty
from bpy.app.handlers import persistent

from .operators import *
from .panels import *
from .cache import load_properties

__classes__ = [
    UserProperties, UserPreferences, ExportProperties, ExportPanel,
    OAuthOperator, GetTokenOperator, ClearTokenOperator, ExportUploadOperator,
    ProgressOperator, ProgressProperty
]

register_classes, unregister_classes = bpy.utils\
    .register_classes_factory(__classes__)


def register():
    register_classes()
    bpy.types.WindowManager.csm_user = PointerProperty(type=UserProperties)
    bpy.types.Scene.csm_export = PointerProperty(type=ExportProperties)
    bpy.types.WindowManager.csm_progress = PointerProperty(
        type=ProgressProperty)

    # Update login persistence
    @persistent
    def on_load(ignore):
        load_properties(bpy.context.window_manager.csm_user)

    bpy.app.handlers.load_post.append(on_load)


def unregister():
    unregister_classes()
    del bpy.types.WindowManager.csm_user
    del bpy.types.Scene.csm_export
    del bpy.types.WindowManager.csm_progress
    OAuthOperator.stop()
