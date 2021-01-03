# blueprints/about.py | Flask routes for assorted data
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

from operator import itemgetter

from flask import Blueprint, jsonify

import sciolyid.config as config
from sciolyid.data import get_category, groups, master_id_list
from sciolyid.web.config import logger
from sciolyid.web.functions.images import generate_id_lookup

bp = Blueprint("about", __name__, url_prefix="/about")


@bp.route("/list", methods=("GET",))
def list_id_items():
    logger.info("endpoint: about.list")
    if config.options["id_groups"]:
        output = groups
    else:
        output = {"items": master_id_list}
    return jsonify(output)


@bp.route("/info", methods=("GET",))
def info():
    logger.info("endpoint: about.info")
    return jsonify(
        {
            "idName": config.options["id_type"],
            "description": config.options["bot_description"],
            "server": config.options["support_server"],
            "verificationServer": (
                None
                if config.options["verification_server"]
                == config.options["support_server"]
                else config.options["verification_server"]
            ),
            "source": config.options["source_link"],
        }
    )


@bp.route("/count", methods=("GET",))
def count():
    logger.info("endpoint: about.count")
    files = generate_id_lookup(ignore_verify=True).keys()
    counts = {}
    id_items = set(master_id_list)
    for name in files:
        split = name.split("/")[1:-1]
        if len(split) == 1:
            counts.setdefault(split[0], 0)
            counts[split[0]] += 1
            id_items.discard(split[0])
        elif len(split) == 2:
            counts.setdefault(split[0], {})
            counts[split[0]].setdefault(split[1], 0)
            counts[split[0]][split[1]] += 1
            id_items.discard(split[1])
        else:
            logger.info("too many subfolders!")
    for item in id_items:
        if config.options["id_groups"]:
            category = get_category(item)
            counts.setdefault(category, {})
            counts[category][item] = 0
        else:
            counts[item] = 0
    out_list = [
        {
            "name": k,
            "group": isinstance(v, dict),
            "value": [
                {"name": sub_k, "value": sub_v}
                for sub_k, sub_v in sorted(v.items(), key=itemgetter(1, 0))
            ]
            if isinstance(v, dict)
            else v,
        }
        for k, v in sorted(
            counts.items(),
            key=lambda x: (str(x[1]), x[0]) if isinstance(x[1], int) else x[0],
        )
    ]
    output = {"total": len(files), "counts": out_list}
    return jsonify(output)
