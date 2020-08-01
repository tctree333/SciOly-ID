import copy
import hashlib
import os
import shutil
import time
from itertools import chain

from flask import (Blueprint, abort, jsonify, make_response, redirect, request,
                   session, url_for)
from PIL import Image
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.web.config import FRONTEND_URL, app, logger
from sciolyid.web.functions import fetch_profile
from sciolyid.web.upload_functions import (add_images, find_duplicates,
                                           verify_image)
from sciolyid.web.user import get_user_id

bp = Blueprint("upload", __name__, url_prefix="/upload")


@bp.route("/", methods=["GET", "POST"])
def upload():
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
    if len(request.files) > 100:
        abort(413, "You can only upload 100 files at a time!")
    files = chain.from_iterable(request.files.listvalues())
    output: dict = {"invalid": [], "duplicates": {}, "sha1": {}}
    for upload in files:
        with copy.deepcopy(upload.stream) as f:
            ext = verify_image(f, upload.mimetype)
            if not ext:
                output["invalid"].append(upload.filename)
                continue
            dupes = find_duplicates(Image.open(f))
            if dupes:
                output["duplicates"][upload.filename] = dupes
            f.seek(0)
            sha1 = hashlib.sha1(f.read()).hexdigest()
        output["sha1"][upload.filename] = sha1
        save_path = (
            f"{config.options['tmp_upload_dir']}{user_id}/{request.form['item']}/"
        )
        os.makedirs(save_path, exist_ok=True)
        upload.save(f"{save_path}{sha1}.{ext}")

    return jsonify(output)


@bp.route("/save", methods=["GET", "POST"])
def save():
    logger.info("endpoint: upload.save")
    user_id: str = get_user_id()
    username: str = fetch_profile(user_id)["username"]
    save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
    sources: list = []
    destinations: list = []
    for directory in os.listdir(save_path):
        remote_path: str = config.options["validation_repo_dir"] + directory + "/"
        current_path: str = save_path + directory + "/"
        for filename in os.listdir(current_path):
            sources.append(current_path + filename)
            destinations.append(remote_path)
    url = add_images(sources, destinations, user_id, username)
    if url is None:
        abort(500, "Pushing the changes failed.")
    shutil.rmtree(save_path)
    return jsonify({"url": url})


@bp.route("/uploaded", methods=["GET"])
def uploaded():
    logger.info("endpoint: upload.uploaded")
    user_id: str = get_user_id()
    save_path: str = config.options["tmp_upload_dir"] + user_id + "/"
    if not os.path.exists(save_path) or not len(os.listdir(save_path)) > 0:
        abort(500, "No uploaded files")
    output: dict = dict()
    for directory in os.listdir(save_path):
        output[directory] = []
        for filename in os.listdir(save_path + directory + "/"):
            output[directory].append(filename)
    return jsonify(output)
