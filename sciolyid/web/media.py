import os
import time
import hashlib
from itertools import chain

from flask import (Blueprint, abort, jsonify, make_response, redirect, request,
                   session, url_for)
from PIL import Image
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.github import find_duplicates
from sciolyid.web.config import FRONTEND_URL, app, logger
from sciolyid.web.functions import verify_image
from sciolyid.web.user import get_user_id

bp = Blueprint("media", __name__, url_prefix="/media")


@bp.route("/upload", methods=["GET", "POST"])
def login():
    logger.info("endpoint: upload")
    user_id = get_user_id()
    if request.method == "POST":
        if not request.files:
            abort(415, "Missing Files")
        files = chain.from_iterable(request.files.listvalues())
        output = {"invalid": [], "duplicates": {}}
        for upload in files:
            with upload.stream as f:
                ext = verify_image(f, upload.mimetype)
                if not ext:
                    output["invalid"].append(upload.filename)
                    continue
                dupes = find_duplicates(Image.open(f))
                if dupes:
                    output["duplicates"][upload.filename] = dupes
                f.seek(0)
                sha1 = hashlib.sha1(f.read()).hexdigest()
                save_filename = f"{config.options['tmp_upload_dir']}{user_id}/{request.form['item']}/"
                os.makedirs(save_filename, exist_ok=True)
                upload.save(f"{save_filename}{sha1}.{ext}")

        return jsonify(output)

    return """
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name="file" multiple>
      <input type=hidden name="item" value="dinosaur">
      <input type=submit value=Upload>
    </form>
    """
