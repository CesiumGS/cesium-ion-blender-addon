import bpy
from bpy.types import Operator
from bpy.props import *

from ..server import OAuthServer
from ..globals import (APP_OPERATOR_PREFIX, ION_ADDRESS, REDIRECT_ADDRESS,
                       REDIRECT_PORT, CLIENT_ID)


class OAuthOperator(Operator):
    bl_label = "Open Cesium Authorization"
    bl_idname = f"{APP_OPERATOR_PREFIX}.oauth"
    bl_options = {'INTERNAL'}

    oauth_address: StringProperty(default=ION_ADDRESS)
    client_id: StringProperty(default=CLIENT_ID)
    redirect_uri: StringProperty()
    code_verifier: StringProperty()

    _server = OAuthServer(REDIRECT_ADDRESS, REDIRECT_PORT)

    @staticmethod
    def stop():
        OAuthOperator._server.stop()

    def execute(self, context):
        import webbrowser
        from urllib.parse import urlencode

        params = urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "assets:write",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        })

        client_id = self.client_id
        redirect_uri = self.redirect_uri
        code_verifier = self.code_verifier

        def oauth_listener(code):
            bpy.ops.csm.get_token(client_id=client_id,
                                  code=code,
                                  code_verifier=code_verifier,
                                  redirect_uri=redirect_uri)

        OAuthOperator._server.set_listener(oauth_listener)
        OAuthOperator._server.start()
        webbrowser.open_new(f"{self.oauth_address}/ion/oauth?{params}")

        return {"FINISHED"}

    @property
    def code_challenge(self):
        import base64, hashlib
        hashed = hashlib.sha256(self.code_verifier.encode("UTF-8")).digest()
        encoded = base64.b64encode(hashed)
        return encoded.decode("utf-8")\
            .replace("=", "")\
            .replace("+", "-")\
            .replace("/", "_")

    def invoke(self, context, event):
        import random, string
        self.redirect_uri = f"http://{REDIRECT_ADDRESS}:{REDIRECT_PORT}/"
        self.code_verifier = str("".join(
            random.choices(string.ascii_letters + string.digits, k=32)))
        return self.execute(context)
