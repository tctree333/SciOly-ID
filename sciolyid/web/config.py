# config.py | Flask application configuration
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

import sentry_sdk
from flask import Flask, request
from sentry_sdk.integrations.flask import FlaskIntegration

from sciolyid.data import logger  # pylint: disable=unused-import
import sciolyid.config as config

if config.options["sentry"]:
    sentry_sdk.init(
        release=f"{os.getenv('CURRENT_PLATFORM')} Release "
        + (
            f"{os.getenv('GIT_REV', '')[:8]}"
            if os.getenv("CURRENT_PLATFORM") != "Heroku"
            else f"{os.getenv('HEROKU_RELEASE_VERSION')}:{os.getenv('HEROKU_SLUG_DESCRIPTION')}"
        ),
        dsn=os.getenv(config.options["sentry_web_dsn_env"]),
        integrations=[FlaskIntegration()],
    )

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_NAME"] = config.options["name"]
app.secret_key = os.getenv(config.options["secret_key_env"])
FRONTEND_URL: str = os.getenv(config.options["frontend_url_env"], "")


@app.after_request  # enable CORS
def after_request(response):
    header = response.headers
    header["Access-Control-Allow-Origin"] = FRONTEND_URL
    header["Access-Control-Allow-Credentials"] = "true"
    header["Access-Control-Allow-Headers"] = request.access_control_request_headers
    header["Access-Control-Allow-Methods"] = "HEAD, GET, OPTIONS, POST, DELETE"
    return response
