import bpy
from bpy.props import *
from bpy.types import (Panel, PropertyGroup, AddonPreferences)

from ..operators import (OAuthOperator, ClearTokenOperator)
from ..globals import (APP_CATEGORY, APP_PACKAGE)


class UserProperties(PropertyGroup):
    token: StringProperty()


class UserPreferences(AddonPreferences):
    bl_idname = APP_PACKAGE

    def draw(self, context):
        layout = self.layout
        csm_user_len = len(context.window_manager.csm_user.token)
        status_text = "Logged In" if csm_user_len > 0 else "Disconnected"
        layout.row().label(text=f"Status: {status_text}")

        if csm_user_len <= 0:
            layout.operator(OAuthOperator.bl_idname, text="Login")
        else:
            layout.operator(ClearTokenOperator.bl_idname, text="Logout")
