import os
import re
import sys
import json
import zipfile
import subprocess
import urllib.error, urllib.request


class ProgressBar(object):
    def __init__(self, total, prefix="", size=60, file=sys.stdout):
        self.total = total
        self.prefix = prefix
        self.size = 60
        self.file = file
        self.total_count = 0

    def update(self, count):
        self.total_count += count
        x = int(self.size * self.total_count / self.total)
        self.file.write("%s[%s%s] %i/%i\r" %
                        (self.prefix, "#" * x, "." *
                         (self.size - x), self.total_count, self.total))
        self.file.flush()

        if self.total_count == self.total:
            print()


def get_tracked_files(folder=None):
    files = subprocess.check_output("git ls-files", shell=True)\
        .decode()\
        .splitlines()

    if folder is not None:
        folder = os.path.abspath(folder)
        old_files = files
        files = []
        for file in old_files:
            abs_path = os.path.abspath(file)
            if abs_path.startswith(folder):
                files.append(file)

    return files


def error(msg):
    print(msg)
    sys.exit(1)


def format_version(tuple_version):
    return "v" + ".".join(map(str, tuple_version))


def get_latest_version(org, repo, version_param_length=2):
    url = f"https://api.github.com/repos/{org}/{repo}/releases/latest"
    try:
        body = urllib.request.urlopen(url).read()
    except urllib.error.HTTPError as e:
        body = e.read()
    data = json.loads(body.decode("UTF-8"))

    if "tag_name" not in data:
        version = ()
    else:
        version = re.sub(r"[^0-9\.]", "", data["tag_name"]).split(".")
    version += (0, ) * (version_param_length - len(version))

    return version


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    module_dir = os.path.join(script_dir, "io-cesium-ion")
    script_path = os.path.join(module_dir, "__init__.py")
    print("Identifying version...")
    with open(script_path, "r") as init_script:
        bl_info_raw = re.findall(r"bl_info\s*=\s*(\{[^}]+\})",
                                 init_script.read())
        if len(bl_info_raw) != 1:
            error("Unable to find bl_info expected 1 found " +
                  f"{len(bl_info_raw)}")
        bl_info = eval(bl_info_raw[0])

    local_version = bl_info["version"]
    released_version = get_latest_version(
        "AnalyticalGraphicsInc",
        "ion-blender-exporter",
        version_param_length=len(local_version))

    if local_version <= released_version:
        error(f"\"Local Version\" ({format_version(local_version)}) in " +
              "\"bl_info\" must be newer than the last \"Release Version\" " +
              f"({format_version(released_version)})")

    tracked_files = get_tracked_files(module_dir)
    bar = ProgressBar(len(tracked_files), prefix="Zipping ")

    zip_file_name = f'io-cesium-ion-{format_version(local_version)}.zip'
    zipf = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
    for file_path in tracked_files:
        zip_rel_path = os.path.relpath(file_path, module_dir)
        zipf.write(file_path, zip_rel_path)
        bar.update(1)

    zipf.writestr(os.path.join(script_dir, "LICENSE"), "LICENSE")
    print(f"Zip written to {zip_file_name}")
    zipf.close()
