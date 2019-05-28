import bpy
from bpy.props import *
from bpy.types import (Panel, PropertyGroup)

from ..operators import (OAuthOperator, ClearTokenOperator)
from ..globals import APP_CATEGORY


class UserProperties(PropertyGroup):
    token: StringProperty()


class UserPanel(Panel):
    bl_idname = "CESIUM_PT_user"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Account"
    bl_category = APP_CATEGORY

    def draw(self, context):

        layout = self.layout
        csm_user = context.window_manager.csm_user
        csm_user_len = len(csm_user.token)
        status_text = "Linked" if csm_user_len > 0 else "Disconnected"
        layout.row().label(text=f"Status: {status_text}")

        if csm_user_len <= 0:
            layout.operator(OAuthOperator.bl_idname, text="Authorize")
        else:
            layout.operator(ClearTokenOperator.bl_idname, text="Logout")
