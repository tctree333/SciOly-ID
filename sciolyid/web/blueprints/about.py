from flask import Blueprint, jsonify  # abort, url_for

from sciolyid.data import groups
from sciolyid.web.config import logger

# import sciolyid.config as config

bp = Blueprint("about", __name__, url_prefix="/about")


@bp.route("/list", methods=("GET",))
def list_id_items():
    logger.info("endpoint: about.list")
    return jsonify(groups)
