bl_info = {
    "name": "Cesium Ion",
    "description": "Cesium Ion Exporting Tool",
    "author": "",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Import-Export"
}

import bpy
from bpy.props import PointerProperty

from .operators import *
from .panels import *
from .cache import PropertyLoadWorker

__classes__ = [
    OAuthOperator, UserProperties, UserPanel, ExportProperties, ExportPanel,
    GetTokenOperator, ClearTokenOperator, ExportUploadOperator
]

register_classes, unregister_classes = bpy.utils\
    .register_classes_factory(__classes__)


def register():
    register_classes()
    bpy.types.Scene.csm_user = PointerProperty(type=UserProperties)
    bpy.types.Scene.csm_export = PointerProperty(type=ExportProperties)
    PropertyLoadWorker().start()


def unregister():
    ExportUploadOperator.stop()
    unregister_classes()
    del bpy.types.Scene.csm_user
    del bpy.types.Scene.csm_export


if __name__ == "__main__":
    register()
