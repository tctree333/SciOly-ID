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
    output = {"total": len(files), "counts": {}}
    id_items = set(master_id_list)
    for name in files:
        split = name.split("/")[1:-1]
        if len(split) == 1:
            output["counts"].setdefault(split[0], 0)
            output["counts"][split[0]] += 1
            id_items.discard(split[0])
        elif len(split) == 2:
            output["counts"].setdefault(split[0], {})
            output["counts"][split[0]].setdefault(split[1], 0)
            output["counts"][split[0]][split[1]] += 1
            id_items.discard(split[1])
        else:
            logger.info("too many subfolders!")
    for item in id_items:
        if config.options["id_groups"]:
            output["counts"][get_category(item)][item] = 0
        else:
            output["counts"][item] = 0
    output["none"] = list(sorted(id_items))
    return jsonify(output)
