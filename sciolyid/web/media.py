import imghdr
import os
import time
from itertools import chain

from flask import (Blueprint, abort, jsonify, make_response, redirect, request,
                   session, url_for)
from PIL import Image
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.web.config import FRONTEND_URL, app, logger
from sciolyid.web.functions import verify_image

bp = Blueprint("media", __name__, url_prefix="/media")


@bp.route("/upload", methods=["GET", "POST"])
def login():
    logger.info("endpoint: upload")
    if request.method == "POST":
        if not request.files:
            abort(415, "Missing Files")
        files = chain.from_iterable(request.files.listvalues())
        invalid = []
        for upload in files:
            if not verify_image(upload):
                invalid.append(upload.name)
            # else:

    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=file name="file">
      <input type=submit value=Upload>
    </form>
    """
