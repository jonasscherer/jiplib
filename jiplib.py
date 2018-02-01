import uuid
import jsonpickle
import json
from copy import copy
import sys, requests, re, shutil, os, urllib
from urllib.parse import urljoin
from urllib.request import urlretrieve


def init(faas_url_tmp, fileserver_url_tmp, callback_url_tmp):
    global faas_url, fileserver_url, callback_url

    faas_url = faas_url_tmp
    fileserver_url = fileserver_url_tmp
    callback_url = callback_url_tmp


def create_uid():
    return uuid.uuid4()


def convert_object2json(order_obj):
    return jsonpickle.encode(order_obj)


def convert_json2object(json_str):
    return jsonpickle.decode(json_str)


def get_uid():
    uid = uuid.uuid4().hex
    return uid


def translate_JipImageModel_to_JipImage(jip_image_model):
    jip_image = JipImage()

    jip_image.id_image = jip_image_model.id
    jip_image.uploader = jip_image_model.author.username
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
    jip_order.id = jip_order_model.id

    author = JipUser(username=jip_order_model.author.username, id=jip_order_model.author.id, role="na")
    jip_order.author = author
    jip_order.target_function = jip_order_model.target_function
    jip_order.status = jip_order_model.status
    # jip_order.timestamp_creation = JipOrderModel.timestamp_creation

    new_img_list = []

    for img in img_list:
        new_img_list.append(translate_JipImageModel_to_JipImage(img))

    jip_order.image_list = new_img_list

    return jip_order


class JipUser(object):
    def __init__(self, username="na", id="na", role="na"):
        self.username = username
        self.id = id
        self.role = role


class JipImage(object):
    def __init__(self, id_image="na", uploader="na", file_type="na", path_filesystem="na", url_fileserver="na",
                 resolution="na",
                 spacing="na"):
        self.id_image = id_image
        self.uploader = uploader
        self.file_type = file_type
        self.path_filesystem = path_filesystem
        self.url_fileserver = url_fileserver
        self.resolution = resolution
        self.spacing = spacing


class JipOrder(object):
    def __init__(self, title="na", text="na", hash="na", id="na", author="na", order_path="na",
                 timestamp_creation="na", target_function="na", image_list="na", status="na"):
        self.hash = hash
        self.title = title
        self.text = text
        self.id = id
        self.author = author
        self.order_path = order_path
        self.timestamp_creation = timestamp_creation
        self.target_function = target_function
        self.image_list = image_list
        self.status = status


class JipUpdate(object):
    def __init__(self, id_order="na", update_message="na", progress="na"):
        self.id_order = id_order
        self.update_message = update_message
        self.progress = progress


class JipFunction(object):
    def __init__(self, name="na", version="na", info="na", author="na", description="na", file_types_consumed="na",
                 file_types_produced="na",
                 resolution_consumed="na",
                 spacing_consumed="na"):
        self.name = name
        self.version = version
        self.info = info
        self.author = author
        self.description = description
        self.file_types_consumed = file_types_consumed
        self.file_types_produced = file_types_produced
        self.resolution_consumed = resolution_consumed
        self.spacing_consumed = spacing_consumed


def download_file_list(image_list, target_path):
    global fileserver_url

    if not os.path.exists(target_path):
        os.makedirs(target_path)

    for img_file in image_list:
        filename = os.path.join(img_file.url_fileserver)
        file_target = os.path.join(target_path, filename)

        urlretrieve(img_file.url_fileserver, file_target)


def upload_results(order, source_path):
    global fileserver_url

    post_url = urljoin(fileserver_url, 'post')

    headers = {'user': order.author.id + "_" + order.author.username, 'function_name': function_name}

    for path in os.listdir(source_path):
        full_path = os.path.join(source_path, path)
        if os.path.isfile(full_path):
            file_name = os.path.basename(full_path)
            with open(full_path, 'rb') as f:
                r = requests.post(post_url, files={file_name: f}, headers=headers)


def send_order(jip_order, async=False):
    global faas_url, callback_url, fileserver_url

    if async:
        post_url = urljoin(faas_url + "/async-function/", jip_order.target_function)
    else:
        post_url = urljoin(faas_url + "/function/", jip_order.target_function)

    json_string = convert_object2json(jip_order)
    payload_dict = {'command': 'order', 'order': json_string, 'FILESERVER_URL': fileserver_url, 'FAAS_URL': faas_url,
                    'CALLBACK_URL': callback_url}
    payload_json = json.dumps(payload_dict)
    response = requests.post(post_url, data=payload_json, timeout=5)
    if response.text is not None:
        print("Function response: %s" % response.text)


def get_function_info(function_name, async=False):
    global faas_url
    post_url = urljoin(faas_url + "/function/", function_name)

    payload_dict = {'command': 'info'}
    payload_json = json.dumps(payload_dict)
    response = requests.post(post_url, data=payload_json, timeout=1)
    response_text = response.text

    if "py/object" in response_text:
        response_text = response_text[response_text.find("{"): response_text.find("}") + 1]
        function_info = convert_json2object(response_text)
    else:
        function_info = JipFunction(name=function_name)

    return function_info


def update_order(jip_update):
    pass


def remove_tmp(path):
    shutil.rmtree(path)


def jip_log(jip_order, msg):
    global callback_url

    json_string = convert_object2json(jip_order)

    payload_dict = {'type': 'log', 'order': json_string, 'message': msg}
    payload_json = json.dumps(payload_dict)
    response = requests.post(callback_url, data=payload_json, timeout=2)


def get_dict(json_string):
    return json.loads(json_string)
