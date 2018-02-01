import uuid
import jsonpickle
import json
from copy import copy
import sys, requests, re, shutil, os, urllib
from urllib.parse import urljoin
from urllib.request import urlretrieve
import tarfile


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
    def __init__(self, id_order="na", update_message="na", progress="na", type="na", status="na"):
        self.id_order = id_order
        self.update_message = update_message
        self.progress = progress
        self.type = type
        self.status = status


class JipFunction(object):
    def __init__(self, name="na", version="na", info="na", author="na", description="na", file_types_consumed="na",
                 file_types_produced="na", resolution_consumed="na", spacing_consumed="na", faas_id="na"):
        self.name = name
        self.version = version
        self.info = info
        self.author = author
        self.description = description
        self.file_types_consumed = file_types_consumed
        self.file_types_produced = file_types_produced
        self.resolution_consumed = resolution_consumed
        self.spacing_consumed = spacing_consumed
        self.faas_id = faas_id


def download_file_list(order, target_path):
    try:
        global fileserver_url

        if not os.path.exists(target_path):
            jip_log(order, ("MKDIR %s" % target_path))
            os.makedirs(target_path)

        image_list = order.image_list

        for img_file in image_list:
            jip_log(order, ("IN FOR"))
            filename = os.path.basename(img_file.url_fileserver)
            server_url = urljoin(fileserver_url, img_file.url_fileserver)
            file_target = os.path.join(target_path, filename)
            jip_log(order, ("server_url %s" % server_url))
            jip_log(order, ("file_target %s" % file_target))
            urlretrieve(server_url, file_target)

        jip_log(order, ("END FOR"))

    except Exception as e:
        jip_log(order, ("download_file_list() ERROR: %s" % str(e)))
        print(str(e))
        return str(e)


def upload_results(order, source_path, function_name):
    try:
        jip_log(order, ("in upload_results()"))

        global fileserver_url

        post_url = urljoin(fileserver_url, 'post')

        headers = {'order': str(order.author.id) + "_" + str(order.author.username), 'hash': order.hash,
                   'function_name': function_name}
        tar_file_path = os.path.join(source_path, function_name + ".tar.gz")
        filename = os.path.basename(tar_file_path)
        jip_log(order, tar_file_path)
        jip_log(order, filename)
        jip_log(order, source_path)

        make_tarfile(tar_file_path, source_path)

        with open(tar_file_path, 'rb') as f:
            r = requests.post(post_url, files={filename: f}, headers=headers)
        return "RESULT:" + tar_file_path


    except Exception as e:
        jip_log(order, ("upload_results() ERROR: %s" % str(e)))
        print(str(e))
        return "ERROR: " + str(e)


def send_order(jip_order, async=False):
    try:

        global faas_url, callback_url, fileserver_url
        if async:
            post_url = urljoin(faas_url + "/async-function/", jip_order.target_function)
        else:
            post_url = urljoin(faas_url + "/function/", jip_order.target_function)

        json_string = convert_object2json(jip_order)
        payload_dict = {'command': 'order', 'order': json_string, 'FILESERVER_URL': fileserver_url,
                        'FAAS_URL': faas_url,
                        'CALLBACK_URL': callback_url, 'X-Callback-Url': callback_url}
        payload_json = json.dumps(payload_dict)

        response = requests.post(post_url, data=payload_json, timeout=5)
        if response.text is not None:
            print("Function response: %s" % response.text)

    except Exception as e:
        print(str(e))
        return str(e)


def get_function_info(function_name, async=False):
    try:

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

        function_info.faas_id = function_name
        return function_info

    except Exception as e:
        function_info = JipFunction(name=function_name)
        return function_info


def update_order(jip_update):
    pass


def remove_tmp(path):
    shutil.rmtree(path)


def jip_log(jip_order, msg):
    update = JipUpdate()
    update.id_order = jip_order.id
    update.update_message = msg
    update.progress = "-1"
    update.type = "log"
    update.status = "running"

    send_update(jip_order)


def send_update(update):
    try:
        global callback_url
        update_json = convert_object2json(update)
        response = requests.post(callback_url, data=update_json, timeout=3)


    except Exception as e:
        return e


def get_dict(json_string):
    return json.loads(json_string)


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
