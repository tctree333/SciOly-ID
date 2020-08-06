import imghdr
import os
import random

from flask import Blueprint, abort, jsonify, request, send_file, url_for

import sciolyid.config as config
from sciolyid.web.config import logger
from sciolyid.web.functions.images import (VALID_IMG_TYPES, find_duplicates,
                                           generate_id_lookup)
from sciolyid.web.functions.user import get_user_id
from sciolyid.web.tasks import database

bp = Blueprint("verify", __name__, url_prefix="/verify")


@bp.route("/", methods=("GET",))
def verify_files():
    logger.info("endpoint: verify")
    user_id: str = get_user_id()

    lookup = filename_lookup(
        os.path.abspath(
            config.options["validation_local_dir"]
            + config.options["validation_repo_dir"][:-1]
        )
    )
    image_id = random.choice(tuple(lookup))
    while database.sismember(f"sciolyid.verify.user:{user_id}", image_id):
        image_id = random.choice(tuple(lookup))

    output = {}
    output["url"] = url_for(".send_image", image_id=image_id)
    output["duplicates"] = find_duplicates(lookup[image_id], ignore_verify=True)
    output["item"] = lookup[image_id].split("/")[-2]
    output["id"] = image_id
    return jsonify(output)


@bp.route("/image/<string:image_id>", methods=("GET",))
def send_image(image_id: str):
    logger.info("endpoint: verify.send_image")
    get_user_id()

    lookup = filename_lookup(
        os.path.abspath(
            config.options["validation_local_dir"]
            + config.options["validation_repo_dir"][:-1]
        )
    )
    image_path = lookup.get(image_id, None)
    if not image_path:
        abort(404, "Filename not found!")
    return send_file(image_path)


def filename_lookup(start_path: str) -> dict:
    id_lookup = generate_id_lookup()
    if not id_lookup:
        abort(500, "filename lookup failed!")
    result = {}
    stack = []
    stack.append(start_path)
    while stack:
        current = stack.pop()
        for child_filename in os.listdir(current):
            child_path = current + "/" + child_filename
            if os.path.isdir(child_path):
                stack.append(child_path)
                continue
            if imghdr.what(child_path) in VALID_IMG_TYPES:
                image_id = id_lookup["./" + os.path.relpath(child_path, start_path)]
                result[image_id] = child_path
    return result


@bp.route("/confirm", methods=("POST",))
def confirm():
    logger.info("endpoint: verify.confirm")
    user_id: str = get_user_id()

    confirmation = request.form["confirmation"]
    if confirmation not in ("valid", "invalid", "duplicate"):
        abort(400, "invalid confirmation field")

    lookup = filename_lookup(
        os.path.abspath(
            config.options["validation_local_dir"]
            + config.options["validation_repo_dir"][:-1]
        )
    )
    image_id = request.form["id"]
    if image_id not in lookup.keys():
        abort(400, "invalid id")

    if database.sismember(f"sciolyid.verify.user:{user_id}", image_id):
        abort(400, "You've already confirmed this image!")

    database.zincrby(f"sciolyid.verify.images:{confirmation}", 1, image_id)
    database.sadd(f"sciolyid.verify.user:{user_id}", image_id)
    return jsonify({"success": True})


# @bp.route("/save", methods=("GET", "POST"))
# def save():
#     logger.info("endpoint: upload.save")
#     user_id: str = get_user_id()

#     if database.exists(f"sciolyid.upload.save:{user_id}"):
#         abort(500, "save already in progress!")
#     database.set(f"sciolyid.upload.save:{user_id}", "1")
#     database.delete(f"sciolyid.upload.status:{user_id}")
#     database.hset(
#         f"sciolyid.upload.status:{user_id}",
#         mapping={"start": int(time.time()), "status": json.dumps(["IN_PROGRESS"])},
#     )

#     username: str = fetch_profile(user_id)["username"]

#     save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
#     if not os.path.exists(save_path):
#         database.delete(
#             f"sciolyid.upload.save:{user_id}", f"sciolyid.upload.status:{user_id}"
#         )
#         abort(500, "No images uploaded")

#     sources: list = []
#     destinations: list = []
#     for directory in os.listdir(save_path):
#         remote_path: str = config.options["validation_repo_dir"] + directory + "/"
#         current_path: str = save_path + directory + "/"
#         for filename in os.listdir(current_path):
#             sources.append(current_path + filename)
#             destinations.append(remote_path)

#     add_images(sources, destinations, user_id, username)
#     shutil.rmtree(save_path)

#     status: dict = database.hgetall(f"sciolyid.upload.status:{user_id}")
#     status = {x[0].decode(): json.loads(x[1].decode()) for x in status.items()}
#     return jsonify(status)


# @bp.route("/status", methods=("GET",))
# def upload_status():
#     logger.info("endpoint: upload.save")
#     user_id: str = get_user_id()
#     if not database.exists(f"sciolyid.upload.status:{user_id}"):
#         abort(500, "no current save")
#     status: dict = database.hgetall(f"sciolyid.upload.status:{user_id}")
#     status = {x[0].decode(): json.loads(x[1].decode()) for x in status.items()}
#     return jsonify(status)


# @bp.route("/uploaded", methods=("GET",))
# def uploaded():
#     logger.info("endpoint: upload.uploaded")
#     user_id: str = get_user_id()
#     save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
#     if not os.path.exists(save_path) or not len(os.listdir(save_path)) > 0:
#         abort(500, "No uploaded files")
#     output: dict = dict()
#     for directory in os.listdir(save_path):
#         output[directory] = []
#         for filename in os.listdir(save_path + directory + "/"):
#             output[directory].append(filename)
#     return jsonify(output)
