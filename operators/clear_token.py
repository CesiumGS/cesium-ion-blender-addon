from bpy.types import Operator

from ..globals import APP_OPERATOR_PREFIX


class ClearTokenOperator(Operator):
    bl_label = "Cesium Clear Token"
    bl_idname = f"{APP_OPERATOR_PREFIX}.clear_token"

    def execute(self, context):
        context.scene.csm_user.token = ""

        return {"FINISHED"}
