bl_info = {
    "name": "Cesium Ion",
    "description": "Cesium Ion Exporting Tool",
    "author": "",
    "version": (0, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object"
}

import bpy
from bpy.props import *
from bpy.types import (
    Panel,
    PropertyGroup,
    Operator
)

import requests
from urllib.parse import urlencode

"""
SERVER.PY
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from threading import Thread
from os import path

class OAuthClientServer(object):
    def __init__(self, address, port, listener=(lambda code: code)):
        self._address = address
        self._port = port
        self._listener = listener
        self._server = None
        self._server_thread = None

    @property
    def is_alive(self):
        return self._server_thread is not None\
            and self._server_thread.is_alive()

    def set_listener(self, listener):
        self._listener = listener

    def start(self):
        if self.is_alive:
            return

        listener = self._listener
        client = self

        class TokenHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()

                script_dir = path.dirname(path.realpath(__file__))
                file_path = path.join(script_dir, "index.html")
                with open(file_path, "rb") as file:
                    data = file.read()
                    self.wfile.write(data)

                params = parse_qs(self.path[2:])

                if "code" in params:
                    Thread(target=client.stop).start()
                    listener(params["code"][0])

        self._server = HTTPServer((self._address, self._port), TokenHandler)

        self._server_thread = Thread(
            target=self._server.serve_forever,
            args=(0.01,)
        )
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()

    def stop(self, wait=True):
        if not self.is_alive:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server_thread.join()
        self._server_thread = None
        self._server = None
"""
SERVER.PY
"""

APP_CATEGORY="Cesium Ion"
CLIENT_ID="4"
ION_ADDRESS="http://composer.test:8081"
API_ADDRESS="http://api.composer.test:8081"
REDIRECT_ADDRESS="localhost"
REDIRECT_PORT=10101

class OAuthOperator(Operator):
    bl_label = "Open Cesium Authorization"
    bl_idname = "csm.oauth"

    client_id: StringProperty()
    redirect_uri: StringProperty()
    code_verifier: StringProperty()

    def execute(self, context):
        import webbrowser

        params = urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "assets:write assets:read",
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256"
        })

        client_id = self.client_id
        redirect_uri = self.redirect_uri
        code_verifier = self.code_verifier
        def oauth_listener(code):
            bpy.ops.csm.get_token(
                client_id=client_id,
                code=code,
                code_verifier=code_verifier,
                redirect_uri=redirect_uri
            )

        server.set_listener(oauth_listener)
        server.start()
        webbrowser.open_new(f"{ION_ADDRESS}/ion/oauth?{params}")

        return { "FINISHED" }

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
        self.client_id = CLIENT_ID
        self.redirect_uri = f"http://{REDIRECT_ADDRESS}:{REDIRECT_PORT}/"
        self.code_verifier = str("".join(random.choices(string.ascii_letters
            + string.digits, k=32)))
        return self.execute(context)

class GetTokenOperator(Operator):
    bl_label = "Cesium Token Fetch"
    bl_idname = "csm.get_token"

    client_id: StringProperty()
    redirect_uri: StringProperty()
    code_verifier: StringProperty()
    code: StringProperty()

    def execute(self, context):

        url = f"{API_ADDRESS}/oauth/token/"
        data = {
            "grant_type": "authorization_code",
            "code": self.code,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier
        }
        req = requests.post(url, json=data)
        output = req.json()

        if req.status_code != 200:
            self.report({ "ERROR" }, "Authorization failed")
            return { "CANCELLED" }
        if "access_token" not in output:
            self.report({ "ERROR" }, "Invalid access token")
            return { "CANCELLED" }

        context.scene.csm_user.token = output["access_token"]

        return { "FINISHED" }


class ClearTokenOperator(Operator):
    bl_label = "Cesium Clear Token"
    bl_idname = "csm.clear_token"

    def execute(self, context):
        context.scene.csm_user.token = ""

        return { "FINISHED" }

def destructure(d, *keys):
    return [ d[k] if k in d else None for k in keys ]

class S3ProgressPercentage(object):
    def __init__(self, filename, context):
        self._size = float(path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._context = context

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100


class IonUploader(object):
    @staticmethod
    def _setup_vendor():
        try:
            boto3
        except:
            import os, sys

            # Add vendor directory to module search path
            parent_dir = os.path.abspath(os.path.dirname(__file__))
            vendor_dir = os.path.join(parent_dir, "vendor")

            sys.path.append(vendor_dir)

    def __init__(self, token, name, description="", attribution=""):
        self._token = token
        self._name = name
        self._description = description
        self._attribution = attribution
        self._session = None

    @property
    def headers(self):
        return { "Authorization": f"Bearer {self._token}" }

    @property
    def has_session(self):
        return self._session is not None

    def init(self):
        data = {
            "name": self._name,
            "description": self._description,
            "attribution": self._attribution,
            "type": "3DTILES",
            "options": { "sourceType": "3D_MODEL", "textureFormat": "AUTO" }
        }

        req = requests.post(f"{API_ADDRESS}/v1/assets",
            json=data, headers=self.headers)
        if req.status_code != 200:
            return "Unable to create upload session"
        self._session = req.json()

        return "SUCCESS"

    def upload(self, file_path):
        if not self.has_session:
            return "No current session"

        IonUploader._setup_vendor()
        import boto3

        access_key, secret_key, token, endpoint, bucket, prefix = destructure(
            self._session["uploadLocation"],
            "accessKey", "secretAccessKey", "sessionToken",
            "endpoint", "bucket", "prefix"
        )
        key = path.join(prefix, "blender.glb")
        boto3.client("s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=token)\
            .upload_file(file_path, Bucket=bucket, Key=key)

        method, url, fields = destructure(self._session["onComplete"],
            "method", "url", "fields")
        res = requests.request(method, url=url,
            headers=self.headers, data=fields)
        if res.status_code // 100 != 2:
            return "Bad completion status"

        return "SUCCESS"

    def open_viewer(self):
        import webbrowser
        if not self.has_session:
            return "No current session"
        asset_id = self._session["assetMetadata"]["id"]
        url = path.join(ION_ADDRESS, "ion/assets", str(asset_id))
        webbrowser.open_new(url)
        return "SUCCESS"


class ExportUploadOperator(Operator):
    bl_label = "Cesium Clear Token"
    bl_idname = "csm.upload_gltf"

    @classmethod
    def poll(cls, context):
        csm_user, csm_export = context.scene.csm_user, context.scene.csm_export
        return len(csm_user.token) > 0 and len(csm_export.name) > 0

    def report_on_fail(self, out):
        if out == "SUCCESS":
            return
        if isinstance({ out }, str):
            self.report("ERROR", out)
        raise BaseException(out)

    def execute(self, context):
        from tempfile import NamedTemporaryFile

        csm_user, csm_export = context.scene.csm_user, context.scene.csm_export

        self.report({ "INFO" }, "Preparing upload...")
        uploader = IonUploader(csm_user.token, csm_export.name,
            csm_export.description, csm_export.attribution)
        self.report_on_fail(uploader.init())

        with NamedTemporaryFile() as tmp_file:
            file_name = tmp_file.name

            self.report({ "INFO" }, "Exporting Project...")
            bpy.ops.export_scene.gltf(filepath=file_name)
            file_name += ".glb"

            self.report({ "INFO" }, "Uploading Output...")
            self.report_on_fail(uploader.upload(file_name))
            self.report_on_fail(uploader.open_viewer())

            self.report({ "INFO" }, "Finished!")

        return { "FINISHED" }


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
        csm_user_len = len(context.scene.csm_user.token)
        status_text = "Linked" if csm_user_len > 0 else "Disconnected"
        layout.row().label(text=f"Status: {status_text}")

        if csm_user_len <= 0:
            layout.operator(OAuthOperator.bl_idname, text="Authorize")
        else:
            layout.operator(ClearTokenOperator.bl_idname, text="Logout")


class ExportProperties(PropertyGroup):
    name: StringProperty(name="Name", description="Title for the upload")
    description: StringProperty(name="Desc", description="Give an " +
        "overview of the contents of the data")
    attribution: StringProperty(name="Attrib", description="Provide data " +
        "attribution")

class ExportPanel(Panel):
    bl_idname = "CESIUM_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Export"
    bl_category = APP_CATEGORY

    def draw(self, context):

        layout = self.layout
        scene = context.scene

        layout.prop(scene.csm_export, "name")
        layout.prop(scene.csm_export, "description")
        layout.prop(scene.csm_export, "attribution")

        layout.operator(ExportUploadOperator.bl_idname, text="Upload to Ion")


# Sanity check for server death
try:server.stop()
except:pass

classes = [
    OAuthOperator, UserProperties, UserPanel, ExportProperties,
    ExportPanel, GetTokenOperator, ClearTokenOperator, ExportUploadOperator
]
register_classes, unregister_classes = bpy.utils.register_classes_factory(classes)
server = OAuthClientServer(REDIRECT_ADDRESS, REDIRECT_PORT)

def register():
    import os
    register_classes()
    bpy.types.Scene.csm_user = PointerProperty(type=UserProperties)
    bpy.types.Scene.csm_export = PointerProperty(type=ExportProperties)

def unregister():
    unregister_classes()
    server.stop()

if __name__ == "__main__":
    register()
