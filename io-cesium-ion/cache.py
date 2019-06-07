import bpy
from bpy.types import (Operator, PropertyGroup)
from bpy.props import StringProperty
from threading import Thread
from os import path
import json

from .globals import APP_OPERATOR_PREFIX


def to_snake_case(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_path(prop_group):
    config_path = bpy.utils.user_resource("CONFIG", create=True)
    property_group_name = to_snake_case(type(prop_group).__name__)
    file_name = f"{APP_OPERATOR_PREFIX}_{property_group_name}.json"
    file_path = path.join(config_path, file_name)

    return file_path


def save_properties(prop_group):
    save_path = get_path(prop_group)
    props = prop_group.__annotations__.keys()
    data = {prop: prop_group[prop] for prop in props}
    with open(save_path, "w") as write_file:
        json.dump(data, write_file)


def load_properties(prop_group):
    read_path = get_path(prop_group)
    if not path.isfile(read_path):
        return
    with open(read_path) as read_file:
        data = json.load(read_file)
        for key in data.keys():
            prop_group[key] = data[key]
    return prop_group
