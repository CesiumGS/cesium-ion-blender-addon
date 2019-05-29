from bpy.props import *
from bpy.types import (Panel, PropertyGroup)

from ..operators import ExportUploadOperator
from ..globals import APP_CATEGORY


class ExportProperties(PropertyGroup):
    name: StringProperty(name="Name",
                         default="Untitled",
                         description="Title for the upload")
    description: StringProperty(name="Desc",
                                description="Give an " +
                                "overview of the contents of the data")
    attribution: StringProperty(name="Attrib",
                                description="Provide data " + "attribution")


class ExportManageMixin(object):
    def draw(self, context):

        layout = self.layout
        scene = context.scene

        layout.prop(scene.csm_export, "name")
        layout.prop(scene.csm_export, "description")
        layout.prop(scene.csm_export, "attribution")


class ExportPanel(ExportManageMixin, Panel):
    bl_idname = "CESIUM_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Export"
    bl_category = APP_CATEGORY

    def draw(self, context):
        super().draw(context)
        self.layout.operator(ExportUploadOperator.bl_idname,
                             text="Upload to ion")
