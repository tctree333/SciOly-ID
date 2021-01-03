# blueprints/verify.py | Flask routes relating to image verification
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

import os

from flask import Blueprint, abort, jsonify, request, send_file, url_for

import sciolyid.config as config
import sciolyid.web.functions.webhooks as webhooks
from sciolyid.web.config import logger
from sciolyid.web.functions.images import filename_lookup, find_duplicates
from sciolyid.web.functions.user import get_user_id
from sciolyid.web.git import verify_repo
from sciolyid.web.tasks import database

bp = Blueprint("verify", __name__, url_prefix="/verify")


@bp.route("/", methods=("GET",))
def verify_files():
    logger.info("endpoint: verify")
    user_id: str = get_user_id()
    verify_repo.remote("origin").pull()

    lookup = filename_lookup(
        os.path.abspath(
            config.options["validation_local_dir"]
            + config.options["validation_repo_dir"]
        )
    )
    ids: tuple = tuple(lookup.keys())

    if len(ids) == 0:
        return jsonify({"end": True})

    offset: int = request.args.get("offset", 0, int)

    seen: set = set(
        map(lambda x: x.decode(), database.smembers(f"sciolyid.verify.user:{user_id}"))
    )
    image_id: str = ""
    for i in range(len(ids)):
        offset = (i + offset) % len(ids)
        id_ = ids[offset]
        if id_ not in seen:
            image_id = id_
            break
        if i == len(ids) - 1:
            return jsonify({"end": True})

    output = {}
    output["offset"] = offset
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
            + config.options["validation_repo_dir"]
        )
    )
    image_path = lookup.get(image_id, None)
    if not image_path:
        abort(404, "Filename not found!")
    return send_file(image_path)


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
            + config.options["validation_repo_dir"]
        )
    )
    image_id = request.form["id"]
    if image_id not in lookup.keys():
        abort(400, "invalid id")

    if database.sismember(f"sciolyid.verify.user:{user_id}", image_id):
        abort(400, "You've already confirmed this image!")

    database.zincrby(f"sciolyid.verify.images:{confirmation}", 1, image_id)
    database.sadd(f"sciolyid.verify.user:{user_id}", image_id)
    webhooks.send("verify", user_id=user_id, action=confirmation)
    return jsonify({"success": True})


@bp.route("/stats", methods=("GET",))
def stats():
    logger.info("endpoint: verify.stats")
    get_user_id()

    image_id = request.args.get("id", "", str)
    lookup = filename_lookup(
        os.path.abspath(
            config.options["validation_local_dir"]
            + config.options["validation_repo_dir"]
        )
    )
    if image_id not in lookup.keys():
        abort(400, "invalid id")

    output = dict()
    for confirmation in ("valid", "duplicate", "invalid"):
        output[confirmation] = int(
            database.zscore(f"sciolyid.verify.images:{confirmation}", image_id) or 0
        )

    return jsonify(output)
