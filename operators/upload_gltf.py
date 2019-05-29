import bpy
from bpy.types import Operator
from bpy.props import *
from os import path
import requests

from ..globals import (APP_OPERATOR_PREFIX, API_ADDRESS, ION_ADDRESS)


def destructure(d, *keys):
    return [d[k] if k in d else None for k in keys]


class S3ProgressPercentage(object):
    def __init__(self, filename, operator, context):
        from threading import Lock
        self._size = float(path.getsize(filename))
        self._seen_so_far = 0
        self._lock = Lock()
        self._context = context
        self._operator = operator

    def __call__(self, bytes_amount):
        with self._lock:
            wm = self._context.window_manager
            if self._seen_so_far == 0:
                wm.progress_begin(0, self._size)

            self._seen_so_far += bytes_amount
            wm.progress_update(self._seen_so_far)
            percentage = self._seen_so_far / self._size * 100
            self._operator.report({"INFO"}, f"Progress Upload {percentage}")

            if self._seen_so_far >= self._size:
                wm.progress_end()


class ExportUploadOperator(Operator):
    bl_label = "gltf to Cesium uploader"
    bl_idname = f"{APP_OPERATOR_PREFIX}.upload_gltf"
    bl_description = "Uploads \".glb\" exports to Cesium ion"

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

    @classmethod
    def poll(self, context):
        csm_user, csm_export = context.window_manager.csm_user, context.scene.csm_export
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

    def upload(self, file_path, context):
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
        progress = S3ProgressPercentage(file_path, self, context)
        boto3.client("s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=token)\
            .upload_file(file_path, Bucket=bucket, Key=key, Callback=progress)

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

        suffix = ".glb"
        with NamedTemporaryFile(suffix=suffix) as tmp_file:
            file_path = tmp_file.name

            self.report({"INFO"}, "Exporting Project..")
            bpy.ops.export_scene.gltf(filepath=file_path[:-len(suffix)])
            print(file_path)

            self.report({"INFO"}, "Uploading Output..")
            self.upload(file_path, context)
            self.open_viewer()

            self.report({"INFO"}, "Finished!")

        return {"FINISHED"}

    def invoke(self, context, event):
        csm_user, csm_export = context.window_manager.csm_user, context.scene.csm_export
        self.token = csm_user.token
        self.name = csm_export.name
        self.description = csm_export.description
        self.attribution = csm_export.attribution
        self.session = None
        return self.execute(context)
