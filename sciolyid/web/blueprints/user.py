# blueprints/user.py | Flask routes related to users
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
import re
import time

import authlib
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, jsonify, make_response, redirect, request, session, url_for
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.web.config import FRONTEND_URL, app, logger
from sciolyid.web.functions.user import fetch_profile, get_user_id, fetch_server_id

bp = Blueprint("user", __name__, url_prefix="/user")
oauth = OAuth(app)

relative_url_regex = re.compile(
    r"/[^/](?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))*"
)

DISCORD_CLIENT_SECRET: str = os.getenv(config.options["client_secret_env"], "")
oauth.register(
    name="discord",
    client_id=config.options["client_id"],
    client_secret=DISCORD_CLIENT_SECRET,
    access_token_url="https://discord.com/api/oauth2/token",
    access_token_params=None,
    authorize_url="https://discord.com/api/oauth2/authorize",
    authorize_params=None,
    api_base_url="https://discord.com/api/",
    client_kwargs={"scope": "identify guilds", "prompt": "consent"},
)
discord = oauth.discord


@bp.route("/login", methods=("GET",))
def login():
    logger.info("endpoint: login")
    redirect_uri = url_for("user.authorize", _external=True, _scheme="https")
    resp = make_response(oauth.discord.authorize_redirect(redirect_uri))
    redirect_after: str = request.args.get("redirect", FRONTEND_URL, str)
    if (
        relative_url_regex.fullmatch(redirect_after) is not None
        and len(redirect_after) <= 50
    ):
        resp.headers.add(
            "Set-Cookie",
            "redirect="
            + redirect_after
            + "; Max-Age=180; SameSite=Lax; HttpOnly; Secure",
        )
    else:
        resp.headers.add(
            "Set-Cookie", "redirect=/; Max-Age=180; SameSite=Lax; HttpOnly; Secure"
        )
    return resp


@bp.route("/authorize")
def authorize():
    logger.info("endpoint: authorize")
    redirect_uri = url_for("user.authorize", _external=True, _scheme="https")
    oauth.discord.authorize_access_token(redirect_uri=redirect_uri)
    user_profile: dict = oauth.discord.get("users/@me").json()
    user_guilds: dict = oauth.discord.get("users/@me/guilds").json()

    if str(fetch_server_id()) not in (guild["id"] for guild in user_guilds):
        return redirect(config.options["verification_server"])

    session["uid"] = user_profile["id"]
    session["date"] = str(int(time.time()))

    redirect_cookie: str = request.cookies.get("redirect")
    if relative_url_regex.fullmatch(redirect_cookie) is not None:
        redirection = FRONTEND_URL + redirect_cookie
    else:
        redirection = FRONTEND_URL + "/"
    return redirect(redirection)


@bp.route("/logout", methods=("GET",))
def logout():
    logger.info("endpoint: logout")

    session.pop("uid", None)
    session.pop("date", None)

    redirect_after: str = request.args.get("redirect", FRONTEND_URL, str)
    if relative_url_regex.fullmatch(redirect_after) is not None:
        redirect_url = FRONTEND_URL + redirect_after
    else:
        redirect_url = FRONTEND_URL
    return redirect(redirect_url)


@bp.route("/profile", methods=("GET",))
def get_profile():
    logger.info("endpoint: profile")
    uid = get_user_id()
    profile = fetch_profile(uid)
    return jsonify(profile)


@app.errorhandler(authlib.common.errors.AuthlibBaseError)
def handle_authlib_error(e):
    logger.info(f"error with oauth login: {e}")
    capture_exception(e)
    return jsonify(error="An error occurred with the login"), 500
