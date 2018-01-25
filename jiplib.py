import uuid
import jsonpickle
from copy import copy


def create_uid():
    return uuid.uuid4()


def convert_object2json(order_obj):
    return jsonpickle.encode(order_obj)


def convert_json2object(json_str):
    return jsonpickle.decode(json_str)


class JipUser(object):
    def __init__(self, name, role):
        self.name = name
        self.role = role


class JipImage(object):
    def __init__(self, id_image, uploader, file_type, path_filesystem, url_fileserver, resolution, spacing):
        self.id_image = id_image
        self.uploader = uploader
        self.file_type = file_type
        self.path_filesystem = path_filesystem
        self.url_fileserver = url_fileserver
        self.resolution = resolution
        self.spacing = spacing


class JipOrder(object):
    def __init__(self, id_order, customer, timestamp_creation, target_function, image_list):
        self.id_order = id_order
        self.customer = customer
        self.timestamp_creation = timestamp_creation
        self.target_function = target_function
        self.image_list = image_list


class JipUpdate(object):
    def __init__(self, id_order, update_message, progress):
        self.id_order = id_order
        self.update_message = update_message
        self.progress = progress


class JipFunction(object):
    def __init__(self, name="", version="", info="", description="", file_types_consumed="", file_types_produced="",
                 resolution_consumed="",
                 spacing_consumed=""):
        self.name = name
        self.version = version
        self.info = info
        self.description = description
        self.file_types_consumed = file_types_consumed
        self.file_types_produced = file_types_produced
        self.resolution_consumed = resolution_consumed
        self.spacing_consumed = spacing_consumed
