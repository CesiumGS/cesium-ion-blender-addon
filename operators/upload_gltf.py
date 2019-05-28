import bpy
from bpy.types import Operator
from bpy.props import *
from os import path
import requests

from ..globals import (APP_OPERATOR_PREFIX, API_ADDRESS, ION_ADDRESS)


def destructure(d, *keys):
    return [d[k] if k in d else None for k in keys]


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


class ExportUploadOperator(Operator):
    bl_label = "Cesium Clear Token"
    bl_idname = f"{APP_OPERATOR_PREFIX}.upload_gltf"

    api_address: StringProperty(default=API_ADDRESS)
    ion_address: StringProperty(default=ION_ADDRESS)
    token: StringProperty()
    name: StringProperty()
    description: StringProperty()
    attribution: StringProperty()

    @staticmethod
    def setup_boto():
        try:
            boto3
        except:
            import sys

            parent_dir = path.sep.join(
                path.abspath(__file__).split(path.sep)[:-2])
            vendor_dir = path.join(parent_dir, "vendor")

            sys.path.append(vendor_dir)

    @staticmethod
    def stop():
        ExportUploadOperator._server.stop()

    @classmethod
    def poll(cls, context):
        csm_user, csm_export = context.scene.csm_user, context.scene.csm_export
        return len(csm_user.token) > 0 and len(csm_export.name) > 0

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def hassession(self):
        return self.session is not None

    def create_session(self):
        data = {
            "name": self.name,
            "description": self.description,
            "attribution": self.attribution,
            "type": "3DTILES",
            "options": {
                "sourceType": "3D_MODEL",
                "textureFormat": "AUTO"
            }
        }
        req = requests.post(f"{API_ADDRESS}/v1/assets",
                            json=data,
                            headers=self.headers)
        if req.status_code != 200:
            self.report({"ERROR"}, "Unable to create_session")
            return
        self.session = req.json()

    def upload(self, file_path):
        ExportUploadOperator.setup_boto()
        import boto3

        if not self.hassession:
            self.report({"ERROR"}, "No current session")
            return

        self.report({"INFO"}, "Starting Upload..")
        access_key, secret_key, token, endpoint, bucket, prefix = destructure(
            self.session["uploadLocation"], "accessKey", "secretAccessKey",
            "sessionToken", "endpoint", "bucket", "prefix")
        key = path.join(prefix, "blender.glb")
        boto3.client("s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=token)\
            .upload_file(file_path, Bucket=bucket, Key=key)

        self.report({"INFO"}, "Send Compleition Status..")
        method, url, fields = destructure(self.session["onComplete"], "method",
                                          "url", "fields")
        res = requests.request(method,
                               url=url,
                               headers=self.headers,
                               data=fields)
        if res.status_code // 100 != 2:
            self.report({"ERROR"}, "Bad completion status")

    def open_viewer(self):
        import webbrowser

        if not self.hassession:
            self.report({"ERROR"}, "No current session")
            return
        asset_id = self.session["assetMetadata"]["id"]
        url = path.join(self.ion_address, "ion/assets", str(asset_id))
        webbrowser.open_new(url)

    def execute(self, context):
        from tempfile import NamedTemporaryFile

        self.report({"INFO"}, "Preparing upload..")
        self.create_session()

        with NamedTemporaryFile() as tmp_file:
            file_path = tmp_file.name

            self.report({"INFO"}, "Exporting Project..")
            bpy.ops.export_scene.gltf(filepath=file_path)
            file_path += ".glb"

            self.report({"INFO"}, "Uploading Output..")
            self.upload(file_path)
            self.open_viewer()

            self.report({"INFO"}, "Finished!")

        return {"FINISHED"}

    def invoke(self, context, event):
        csm_user, csm_export = context.scene.csm_user, context.scene.csm_export
        self.token = csm_user.token
        self.name = csm_export.name
        self.description = csm_export.description
        self.attribution = csm_export.attribution
        self.session = None
        return self.execute(context)
