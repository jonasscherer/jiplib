import uuid
import jsonpickle
from copy import copy
import sys, requests, re, shutil, os, urllib
from urlparse import urljoin


def create_uid():
    return uuid.uuid4()


def convert_object2json(order_obj):
    return jsonpickle.encode(order_obj)


def convert_json2object(json_str):
    return jsonpickle.decode(json_str)


def get_uid():
    uid = uuid.uuid4().hex
    print("Generating new order UID! %s" % uid)
    return uid


def translate_JipImageModel_to_JipImage(jip_image_model):
    jip_image = JipImage()

    jip_image.id_image = jip_image_model.id
    jip_image.uploader = jip_image_model.author
    jip_image.file_type = jip_image_model.file_type
    jip_image.path_filesystem = jip_image_model.path_filesystem
    jip_image.url_fileserver = jip_image_model.url_fileserver
    jip_image.resolution = jip_image_model.resolution
    jip_image.spacing = jip_image_model.spacing

    return jip_image


def translate_JipOrderModel_to_JipOrder(jip_order_model, img_list):
    jip_order = JipOrder()
    jip_order.hash = jip_order_model.hash
    jip_order.title = jip_order_model.title
    jip_order.text = jip_order_model.text
    jip_order.id_order = jip_order_model.id
    jip_order.customer = jip_order_model.author.username
    jip_order.target_function = jip_order_model.target_function
    # jip_order.timestamp_creation = JipOrderModel.timestamp_creation

    new_img_list = []

    for img in img_list:
        new_img_list.append(translate_JipImageModel_to_JipImage(img))

    jip_order.image_list = new_img_list

    return jip_order


class JipUser(object):
    def __init__(self, name, role):
        self.name = name
        self.role = role


class JipImage(object):
    def __init__(self, id_image="", uploader="", file_type="", path_filesystem="", url_fileserver="", resolution="",
                 spacing=""):
        self.id_image = id_image
        self.uploader = uploader
        self.file_type = file_type
        self.path_filesystem = path_filesystem
        self.url_fileserver = url_fileserver
        self.resolution = resolution
        self.spacing = spacing


class JipOrder(object):
    def __init__(self, title="", text="", hash="", id_order="", customer="", order_path="", timestamp_creation="",
                 target_function="", image_list=""):
        self.hash = hash
        self.title = title
        self.text = text
        self.id_order = id_order
        self.customer = customer
        self.order_path = order_path
        self.timestamp_creation = timestamp_creation
        self.target_function = target_function
        self.image_list = image_list


class JipUpdate(object):
    def __init__(self, id_order="", update_message="", progress=""):
        self.id_order = id_order
        self.update_message = update_message
        self.progress = progress


class JipFunction(object):
    def __init__(self, name="", version="", info="", author="", description="", file_types_consumed="",
                 file_types_produced="",
                 resolution_consumed="",
                 spacing_consumed=""):
        self.name = name
        self.version = version
        self.info = info
        self.author = author
        self.description = description
        self.file_types_consumed = file_types_consumed
        self.file_types_produced = file_types_produced
        self.resolution_consumed = resolution_consumed
        self.spacing_consumed = spacing_consumed


def download_file_list(to_do, uid):
    basic_url = os.environ['BASICURL']
    print("BASICURL: %s" % basic_url)

    source_path = os.environ['SOURCEPATH']

    if not os.path.exists(source_path):
        os.makedirs(source_path)

    for img_file in to_do:
        print("Download File: %s" % img_file.title)
        server_url = urllib.urljoin(basic_url, img_file.path)
        file_target = os.path.join(source_path, img_file.title)
        print("server_url: %s" % server_url)
        print("file_target: %s" % file_target)
        urllib.urlretrieve(server_url, file_target)
        print("File downloaded: %s" % img_file)

    print("All files downloaded!")


def upload_results(uuid, function_name):
    basic_url = os.environ['BASICURL']
    target_path = os.environ['TARGETPATH']

    post_url = urllib.urljoin(basic_url, 'post')
    print("Post-url: %s" % post_url)

    headers = {'uuid': uuid, 'function_name': function_name}

    for path in os.listdir(target_path):
        full_path = os.path.join(target_path, path)
        if os.path.isfile(full_path):
            file_name = os.path.basename(full_path)
            print("upload file: %s" % full_path)
            with open(full_path, 'rb') as f:
                r = requests.post(post_url, files={file_name: f}, headers=headers)
                print(r.text)
            print("File %s uploaded!" % file_name)


def remove_tmp(uid):
    shutil.rmtree("/tmp/%s/" % uid)
