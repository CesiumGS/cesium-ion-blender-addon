bl_info = {
    "name": "Cesium Ion",
    "description":
    "Upload and tile models with Cesium ion. https://cesium.com",
    "author": "",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Import-Export"
}

import bpy
from bpy.props import (PointerProperty, BoolProperty)
from bpy.types import Operator
from bpy.app.handlers import persistent
from threading import Event

from .operators import *
from .panels import *
from .globals import APP_OPERATOR_PREFIX
from .cache import load_properties


# Update login persistence
@persistent
def on_load(ignore):
    load_properties(bpy.context.window_manager.csm_user)


class MenuOperator(ExportManageMixin, Operator):
    bl_label = "Upload to Cesium Ion"
    bl_idname = f"{APP_OPERATOR_PREFIX}.launch_upload"

    def is_token(self, context):
        return len(context.window_manager.csm_user.token) > 0

    def execute(self, context):
        if not self.is_token(context):

            def draw_error(self, context):
                self.layout.label(text="User authorization failed!")
                self.layout.label(
                    text="Please re-run export and complete authorization.")

            bpy.context.window_manager.popup_menu(draw_error,
                                                  title="Authorization Error",
                                                  icon="ERROR")

            return {"CANCELLED"}

        return bpy.ops.csm.upload('INVOKE_DEFAULT')

    def invoke(self, context, event):

        if not self.is_token(context):
            bpy.ops.csm.oauth('INVOKE_DEFAULT')

        return context.window_manager.invoke_props_dialog(self)


def create_menu(self, context):
    self.layout.operator(MenuOperator.bl_idname, text="Upload to Cesium ion")


__classes__ = [
    UserProperties, UserPanel, ExportProperties, ExportPanel, OAuthOperator,
    GetTokenOperator, ClearTokenOperator, ExportUploadOperator,
    UserPreferences, MenuOperator
]

register_classes, unregister_classes = bpy.utils\
    .register_classes_factory(__classes__)


def register():
    register_classes()
    bpy.types.WindowManager.csm_user = PointerProperty(type=UserProperties)
    bpy.types.Scene.csm_export = PointerProperty(type=ExportProperties)
    bpy.app.handlers.load_post.append(on_load)
    bpy.types.TOPBAR_MT_file_export.append(create_menu)


def unregister():
    unregister_classes()
    del bpy.types.WindowManager.csm_user
    del bpy.types.Scene.csm_export
    OAuthOperator.stop()
