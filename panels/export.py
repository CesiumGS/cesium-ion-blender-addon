from bpy.props import *
from bpy.types import (Panel, PropertyGroup)

from ..operators import (ExportUploadOperator, OAuthOperator)
from ..globals import APP_CATEGORY

SOURCE_TYPES = [
    ("3D_MODEL", "3D Model", "Models designed through blender", "FILE_3D", 1),
    ("3D_CAPTURE", "3D Capture",
     "Model created through photogrammetry processes", "CAMERA_DATA", 2)
]


class ExportProperties(PropertyGroup):
    name: StringProperty(name="Name", description="Title for the upload")
    description: StringProperty(
        name="Description",
        description="Give an overview of the contents of the data")
    attribution: StringProperty(
        name="Attribution",
        description="Acknowledge the particular author, artist, or coporation")
    source_type: EnumProperty(name="Model Type",
                              description="Type of data being uploaded",
                              items=lambda self, context: SOURCE_TYPES)
    webp_textures: BoolProperty(
        name="Convert to WebP",
        default=False,
        description=
        "Will produce WebP images, which are typically 25-34% smaller than " +
        "equivalent JPEG images which leads to faster streaming and reduced " +
        "data usage. 3D Tiles produced with this option require a client " +
        "that supports the glTF EXT_texture_webp extension, such as " +
        "CesiumJS 1.54 or newer, and a browser that supports WebP, such as " +
        "Chrome or Firefox 65 and newer.")


class ExportPanel(Panel):
    bl_idname = "CESIUM_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = APP_CATEGORY
    bl_category = APP_CATEGORY

    def draw(self, context):
        layout = self.layout

        csm_export = context.scene.csm_export
        csm_user_len = len(context.window_manager.csm_user.token)

        if csm_user_len > 0:
            layout = self.layout
            scene = context.scene

            layout.prop(scene.csm_export, "name")
            if len(csm_export.name) <= 0:
                layout.label(text="Name is required.")

            layout.prop(scene.csm_export, "description")
            layout.prop(scene.csm_export, "attribution")
            layout.separator()
            layout.prop(scene.csm_export, "source_type")
            if csm_export.source_type is "":
                layout.label(text="Model Type is required.")

            layout.prop(scene.csm_export, "webp_textures")
            layout.operator(ExportUploadOperator.bl_idname,
                            text="Upload to ion")
        else:
            layout.operator(OAuthOperator.bl_idname, text="Login")
