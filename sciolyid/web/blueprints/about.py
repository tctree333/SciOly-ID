from flask import Blueprint, jsonify  # abort, url_for

import sciolyid.config as config
from sciolyid.data import groups, master_id_list
from sciolyid.web.config import logger

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
            "source": config.options["source_link"],
        }
    )
