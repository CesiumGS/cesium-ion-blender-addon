import bpy
from bpy.types import Operator
from bpy.props import *
from os import path, remove as remove_file
from queue import Queue

import requests

from ..globals import (APP_OPERATOR_PREFIX, API_ADDRESS, ION_ADDRESS)


def destructure(d, *keys):
    return [d[k] if k in d else None for k in keys]


class UploadManager(object):
    def __init__(self, token):
        self.token = token

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def hassession(self):
        return self.session is not None

    def create_session(self,
                       name,
                       description,
                       attribution,
                       source_type,
                       webp_textures=False,
                       api_address=API_ADDRESS):
        data = {
            "name": name,
            "description": description,
            "attribution": attribution,
            "type": "3DTILES",
            "options": {
                "sourceType": source_type,
                "textureFormat": "WEBP" if webp_textures else "AUTO"
            }
        }
        req = requests.post(f"{api_address}/v1/assets",
                            json=data,
                            headers=self.headers)
        if req.status_code != 200:
            raise Exception("Unable to create_session")
        self.session = req.json()

    def upload(self, file_path, boto_progress=None):
        import boto3
        if not self.hassession:
            raise Exception("No current session")

        access_key, secret_key, token, endpoint, bucket, prefix = destructure(
            self.session["uploadLocation"], "accessKey", "secretAccessKey",
            "sessionToken", "endpoint", "bucket", "prefix")
        key = path.join(prefix, "blender.glb")
        boto3.client("s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=token)\
            .upload_file(file_path, Bucket=bucket, Key=key, Callback=boto_progress)

        method, url, fields = destructure(self.session["onComplete"], "method",
                                          "url", "fields")
        res = requests.request(method,
                               url=url,
                               headers=self.headers,
                               data=fields)
        if res.status_code // 100 != 2:
            raise Exception("Bad completion status")

    def open_viewer(self, ion_address=ION_ADDRESS):
        import webbrowser

        if not self.hassession:
            raise Exception("No current session")
        asset_id = self.session["assetMetadata"]["id"]
        url = path.join(ion_address, "ion/assets", str(asset_id))
        webbrowser.open_new(url)


class BytesUploadTimer(object):
    def __init__(self, file_path):
        self._bytes_count_queue = Queue()
        self._total_bytes = float(path.getsize(file_path))
        self._uploaded_bytes = 0

    def put_bytes(self, bytes):
        self._bytes_count_queue.put(bytes, block=False)

    def cleanup(self):
        self._total_bytes = 1
        self()

    def __call__(self):
        if self._uploaded_bytes == 0:
            bpy.context.window_manager.progress_begin(0, self._total_bytes)
        while not self._bytes_count_queue.empty():
            self._uploaded_bytes += self._bytes_count_queue.get()
            progress = self._uploaded_bytes / self._total_bytes
            print(f"Upload progress {progress * 100}%")
            bpy.context.window_manager.progress_update(self._uploaded_bytes)
            bpy.context.window_manager.csm_progress.value = progress
            self._bytes_count_queue.task_done()
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        if self._uploaded_bytes >= self._total_bytes:
            bpy.context.window_manager.progress_end()
            return None
        return 0.01  # Wait 0.01 seconds for next update


class ProgressOperator(Operator):
    bl_label = "Upload progress"
    bl_description = "Current upload progress"
    bl_idname = f"{APP_OPERATOR_PREFIX}.progress"


class ExportUploadOperator(Operator):
    bl_label = "gltf to Cesium uploader"
    bl_idname = f"{APP_OPERATOR_PREFIX}.upload"
    bl_description = "Uploads your model to Cesium ion for 3D Tiling"

    token: StringProperty()
    name: StringProperty()
    description: StringProperty()
    attribution: StringProperty()
    source_type: EnumProperty(items=[
        ("3D_MODEL", "", ""),
        ("3D_CAPTURE", "", ""),
    ])
    webp_textures: BoolProperty(default=False)
    api_address: StringProperty(default=API_ADDRESS)
    ion_address: StringProperty(default=ION_ADDRESS)

    @classmethod
    def poll(self, context):
        csm_user, csm_export = context.window_manager.csm_user, context.scene.csm_export
        return len(csm_user.token) > 0 and len(csm_export.name) > 0 and len(
            csm_export.source_type) > 0

    @staticmethod
    def setup_third_party():
        import sys
        parent_dir = path.sep.join(path.abspath(__file__).split(path.sep)[:-2])
        third_party_dir = path.join(parent_dir, "third_party")
        if third_party_dir not in sys.path:
            sys.path.append(third_party_dir)

    def execute(self, context):
        from tempfile import NamedTemporaryFile
        from threading import Thread
        self.setup_third_party()

        self.report({"INFO"}, "Preparing upload..")
        manager = UploadManager(self.token)
        manager.create_session(self.name, self.description, self.attribution,
                               self.source_type, self.webp_textures,
                               self.api_address)

        suffix = ".glb"
        file_path = NamedTemporaryFile(suffix=suffix, delete=False).name
        ion_address = self.ion_address

        def cleanup():
            context.window_manager.csm_progress.value = 0
            if path.isfile(file_path):
                remove_file(file_path)
            timer.cleanup()

        try:
            self.report({"INFO"}, "Exporting Project..")
            bpy.ops.export_scene.gltf(filepath=file_path[:-len(suffix)])
        except Exception as e:
            self.report({"ERROR"}, "Unable to upload!")
            cleanup()
            raise e

        def ion_worker():
            try:
                manager.upload(file_path, boto_progress=timer.put_bytes)
                manager.open_viewer(ion_address)
            finally:
                cleanup()

        self.report({"INFO"}, "Uploading Output..")
        timer = BytesUploadTimer(file_path)
        Thread(target=ion_worker).start()
        bpy.app.timers.register(timer)

        return {"FINISHED"}

    def invoke(self, context, event):
        csm_user, csm_export = context.window_manager.csm_user, context.scene.csm_export
        self.token = csm_user.token
        self.name = csm_export.name
        self.description = csm_export.description
        self.attribution = csm_export.attribution
        self.source_type = csm_export.source_type
        self.webp_textures = csm_export.webp_textures
        return self.execute(context)
