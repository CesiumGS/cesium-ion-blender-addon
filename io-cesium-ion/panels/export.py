from bpy.props import *
from bpy.types import (Panel, PropertyGroup)

from ..operators import (ExportUploadOperator, OAuthOperator, ProgressOperator)
from ..globals import APP_CATEGORY

SOURCE_TYPES = [
    ("3D_MODEL", "3D Model", "Models designed through blender", "FILE_3D", 1),
    ("3D_CAPTURE", "3D Capture", "Model created through 3D capture such as " +
     "scanning, LIDAR, photogrammetry, etc...", "CAMERA_DATA", 2)
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
        name="Use WebP images",
        default=False,
        description=
        "Will produce WebP images, which are typically 25-34% smaller than " +
        "equivalent JPEG images which leads to faster streaming and reduced " +
        "data usage. 3D Tiles produced with this option require a client " +
        "that supports the glTF EXT_texture_webp extension, such as " +
        "CesiumJS 1.54 or newer, and a browser that supports WebP, such as " +
        "Chrome or Firefox 65 and newer.")


class ProgressProperty(PropertyGroup):
    value: FloatProperty(default=0)


class ExportPanel(Panel):
    bl_idname = "CESIUM_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = APP_CATEGORY
    bl_category = APP_CATEGORY

    def required_prop(self, property_group, property_id):
        self.layout.prop(property_group, property_id)
        if len(getattr(property_group, property_id)) <= 0:
            row = self.layout.row()
            row.alignment = "CENTER"
            name = property_group.__annotations__[property_id][1]["name"]
            row.label(text=f"{name} is required.", icon="ERROR")

    def progress_bar(self, progress, layout=None):
        if layout is None:
            layout = self.layout
        container = layout.row()

        label_container = container.row()
        label_container.alignment = "LEFT"
        label_container.label(text=f"{int(progress * 100)}%")

        progress_container = container.row().split(factor=progress)
        progress_container.operator(ProgressOperator.bl_idname,
                                    text="",
                                    depress=True)

    def draw(self, context):
        layout = self.layout
        layout.alignment = "LEFT"

        csm_export = context.scene.csm_export
        csm_user_len = len(context.window_manager.csm_user.token)
        progress = context.window_manager.csm_progress.value

        if progress > 0:
            self.progress_bar(progress)
        elif csm_user_len > 0:
            self.required_prop(csm_export, "name")
            layout.prop(csm_export, "description")
            layout.prop(csm_export, "attribution")
            layout.separator()
            self.required_prop(csm_export, "source_type")

            layout.prop(csm_export, "webp_textures")
            layout.operator(ExportUploadOperator.bl_idname,
                            text="Upload to Cesium ion")
        else:
            layout.operator(OAuthOperator.bl_idname, text="Login")
