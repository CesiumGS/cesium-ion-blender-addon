import os
import re
import sys
import json
import shutil
import fnmatch
import zipfile
import subprocess
from pathlib import Path
from shutil import rmtree, move as move_dir
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


def match_files(folder, ignores=[]):
    excludes = r'|'.join([fnmatch.translate(x) for x in ignores]) or r'$.'

    all_files = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [os.path.join(root, d) for d in dirs]
        dirs[:] = [d for d in dirs if not re.match(excludes, d)]

        # exclude/include files
        files = [os.path.join(root, f) for f in files]
        files = [f for f in files if not re.match(excludes, f)]
        all_files.extend(files)
    return all_files


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


APP_NAME = "io-cesium-ion"


def package(module_dir, license_path, ignores=None, app_name=APP_NAME):
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

    package_files = match_files(module_dir, ignores=ignores)
    bar = ProgressBar(len(package_files), prefix="Zipping ")

    zip_file_name = f"{app_name}-{format_version(local_version)}.zip"
    zipf = zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED)
    zip_path = ""
    for file_path in package_files:
        zip_rel_path = os.path.relpath(file_path, module_dir)
        zipf.write(file_path, os.path.join(app_name, zip_rel_path))
        bar.update(1)

    zipf.write(license_path, os.path.join(app_name, "LICENSE"))
    print(f"Zip written to {zip_file_name}")
    zipf.close()


def install_third_party(module_dir, modules=["boto3"]):
    print("Checking for old third_party...")
    vendor_dir = os.path.join(module_dir, "third_party")
    tmp_vendor_dir = os.path.join(module_dir, "tmp_third_party")
    if os.path.isdir(vendor_dir):
        print("Removing old vendor dir...")
        rmtree(vendor_dir)

    print("Installing vendor (Ignore non-exitting errors)...")
    subprocess.check_output([sys.executable, "-m", "pip", "install"] +
                            modules +
                            [f"--install-option=--prefix={tmp_vendor_dir}"])

    print("Cleaning up...")
    packages_dir = next(Path(tmp_vendor_dir).glob("**/site-packages"))
    move_dir(packages_dir, vendor_dir)
    rmtree(tmp_vendor_dir)

    print("Installation Successful")


if __name__ == "__main__":
    command = None
    if len(sys.argv) >= 2:
        command = sys.argv[1].upper()

    script_dir = os.path.dirname(os.path.realpath(__file__))
    module_dir = os.path.join(script_dir, APP_NAME)
    if command == "PACKAGE":
        with open(os.path.join(script_dir, ".packignore")) as packignore:
            ignores = [line.rstrip('\n') for line in packignore.readlines()]
        package(module_dir, os.path.join(script_dir, "LICENSE"), ignores)
    elif command == "VENDOR":
        print("THIS COMMAND IS EXPERIMENTAL")
        install_third_party(module_dir)
    else:
        print("python3 utils.py arg")
        print("\t package - build a zip for distribution")
        print("\t vendor - update or install third_party directory from pip")
