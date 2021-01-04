# blueprints/upload.py | Flask routes for uploading images
# Copyright (C) 2019-2021  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import json
import os
import shutil
import time
import urllib.parse
from io import BytesIO
from itertools import chain
from typing import Set, Union

import requests
from flask import Blueprint, abort, jsonify, request, send_file
from PIL import Image

import sciolyid.config as config
import sciolyid.web.functions.webhooks as webhooks
import sciolyid.web.tasks.git_tasks as git_tasks
from sciolyid.data import master_id_list
from sciolyid.web.config import logger
from sciolyid.web.functions.images import (
    find_duplicates,
    generate_id_lookup,
    verify_image,
)
from sciolyid.web.functions.user import fetch_profile, get_user_id
from sciolyid.web.git import verify_repo
from sciolyid.web.tasks import database

bp = Blueprint("upload", __name__, url_prefix="/upload")


def add_images(
    sources: list,
    destinations: Union[str, list],
    user_id: str,
    username: str,
    use_filenames: bool = True,
):
    different_dests = False
    if isinstance(destinations, list):
        if len(destinations) != len(sources):
            logger.info("source/dest invalid")
            raise IndexError("sources and destinations are not the same length")
        different_dests = True

    verify_repo.remote("origin").pull()
    items: Set[str] = set()
    for i, item in enumerate(sources):
        filename = item.split("/")[-1] if use_filenames else ""
        destination_path = (
            config.options["validation_local_dir"] + destinations[i]
            if different_dests
            else destinations
        )
        os.makedirs(destination_path, exist_ok=True)
        shutil.copyfile(item, destination_path + filename)
        items.add(item.split("/")[-2])

    webhooks.send("add", user_id=user_id, num=len(sources), items=list(items))
    git_tasks.push.delay(f"add images: id-{user_id}\n\nUsername: {username}", user_id)


@bp.route("/", methods=("GET", "POST"))
def upload_files():
    logger.info("endpoint: upload")

    if request.method == "GET":
        return """
            <h1>Upload new File</h1>
            <form method=post enctype=multipart/form-data>
            <input type=file name="file" multiple>
            <input type=hidden name="item" value="dinosaur">
            <input type=submit value=Upload>
            </form>
            """

    user_id: str = get_user_id()
    if not request.files:
        abort(415, "Missing Files")
    if len(request.files) > 10:
        abort(413, "You can only upload 10 files at a time!")
    item = request.form["item"]
    if item not in master_id_list:
        abort(400, "item is invalid")
    files = chain.from_iterable(request.files.listvalues())
    output: dict = {"invalid": [], "duplicates": {}, "sha1": {}, "rejected": []}
    id_lookup = generate_id_lookup()
    for upload in files:
        save_path = f"{config.options['tmp_upload_dir']}{user_id}/{item}/"
        os.makedirs(save_path, exist_ok=True)
        tmp_path = f"{save_path}tmp"
        upload.save(tmp_path)
        with open(tmp_path, "rb") as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()
            if sha1 in id_lookup.values():
                output["rejected"].append(upload.filename)
                os.remove(tmp_path)
                continue

            f.seek(0)
            ext = verify_image(f, upload.mimetype)
            if not ext:
                output["invalid"].append(upload.filename)
                os.remove(tmp_path)
                continue

            dupes = find_duplicates(Image.open(f))
            if dupes:
                output["duplicates"][upload.filename] = dupes

        output["sha1"][upload.filename] = sha1
        os.rename(tmp_path, f"{save_path}{sha1}.{ext}")

    return jsonify(output)


@bp.route("/delete/<string:image_id>", methods=("DELETE",))
def delete(image_id):
    logger.info("endpoint: upload.delete")
    user_id: str = get_user_id()
    tmp = f"{config.options['tmp_upload_dir']}{user_id}/"
    if not os.path.exists(tmp):
        abort(404, "no uploaded images")
    images = []
    for directory in os.listdir(tmp):
        if os.path.isdir(tmp + directory):
            images += list(
                map(lambda x, d=directory: (x, d), os.listdir(tmp + directory))
            )
    found = False
    for filename in images:
        if os.path.splitext(filename[0])[0] == image_id:
            found = os.path.join(filename[1], filename[0])
            break
    if not found:
        abort(404, "image id not found!")
    os.remove(tmp + found)
    if not os.listdir(tmp + os.path.split(found)[0]):
        os.rmdir(tmp + os.path.split(found)[0])
    return jsonify({"deleted": True})


@bp.route("/save", methods=("GET", "POST"))
def save():
    logger.info("endpoint: upload.save")
    user_id: str = get_user_id()

    if database.exists(f"sciolyid.upload.save:{user_id}"):
        abort(400, "save already in progress!")
    database.set(f"sciolyid.upload.save:{user_id}", "1")
    database.delete(f"sciolyid.upload.status:{user_id}")
    database.hset(
        f"sciolyid.upload.status:{user_id}",
        mapping={"start": int(time.time()), "status": json.dumps(["IN_PROGRESS"])},
    )

    username: str = fetch_profile(user_id)["username"]

    save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
    if not os.path.exists(save_path):
        database.delete(
            f"sciolyid.upload.save:{user_id}", f"sciolyid.upload.status:{user_id}"
        )
        abort(404, "No images uploaded")

    sources: list = []
    destinations: list = []
    for directory in os.listdir(save_path):
        remote_path: str = config.options["validation_repo_dir"] + directory + "/"
        current_path: str = save_path + directory + "/"
        for filename in os.listdir(current_path):
            sources.append(current_path + filename)
            destinations.append(remote_path)

    add_images(sources, destinations, user_id, username)
    shutil.rmtree(save_path)

    status: dict = database.hgetall(f"sciolyid.upload.status:{user_id}")
    status = {x[0].decode(): json.loads(x[1].decode()) for x in status.items()}
    return jsonify(status)


@bp.route("/status", methods=("GET",))
def upload_status():
    logger.info("endpoint: upload.status")
    user_id: str = get_user_id()
    if not database.exists(f"sciolyid.upload.status:{user_id}"):
        abort(404, "no current save")
    status: dict = database.hgetall(f"sciolyid.upload.status:{user_id}")
    status = {x[0].decode(): json.loads(x[1].decode()) for x in status.items()}
    return jsonify(status)


@bp.route("/uploaded", methods=("GET",))
def uploaded():
    logger.info("endpoint: upload.uploaded")
    user_id: str = get_user_id()
    save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
    if not os.path.exists(save_path) or not len(os.listdir(save_path)) > 0:
        abort(404, "No uploaded files")
    output: dict = dict()
    for directory in os.listdir(save_path):
        output[directory] = []
        for filename in os.listdir(save_path + directory + "/"):
            output[directory].append(filename)
    return jsonify(output)


@bp.route("/image/<path:image_path>", methods=("GET",))
def send_image(image_path: str):
    logger.info("endpoint: upload.send_image")
    user_id: str = get_user_id()
    save_path: str = os.path.abspath(config.options["tmp_upload_dir"] + user_id)
    item, filename = os.path.split(image_path)
    if not os.path.exists(save_path) or item not in os.listdir(save_path):
        abort(404, "item not found")
    if filename not in os.listdir(os.path.join(save_path, item)):
        abort(404, "filename not found")
    return send_file(os.path.join(save_path, item, filename))


@bp.route("/remote", methods=("GET",))
def get_remote_image():
    logger.info("endpoint: upload.get_remote_image")
    get_user_id()
    url: str = request.args.get("url", "", str)
    if not url:
        abort(400, "No url passed.")
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        abort(400, "Invalid Url")
    requests.get(urllib.parse.urlunparse(parsed), timeout=10)
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        abort(404, "No image found at that location.")
    content = BytesIO(resp.content)
    ext = verify_image(content, resp.headers.get("content-type"))
    if ext is False:
        abort(404, "Invalid image")
    content.seek(0)
    return send_file(content, attachment_filename=f"file.{ext}")
