import asyncio
import os
import random

import sentry_sdk
from flask import Flask, session
from sentry_sdk.integrations.flask import FlaskIntegration

from sciolyid.data import logger
import sciolyid.config as config

if config.options["sentry"]:
    sentry_sdk.init(
        release=f"{os.getenv('CURRENT_PLATFORM')} Release "
        + (
            f"{os.getenv('GIT_REV', '')[:8]}"
            if os.getenv("CURRENT_PLATFORM") != "Heroku"
            else f"{os.getenv('HEROKU_RELEASE_VERSION')}:{os.getenv('HEROKU_SLUG_DESCRIPTION')}"
        ),
        dsn=os.getenv("SENTRY_API_DSN"),
        integrations=[FlaskIntegration()],
    )

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True
app.secret_key = os.getenv("FLASK_SECRET_KEY")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")

@app.after_request  # enable CORS
def after_request(response):
    header = response.headers
    header["Access-Control-Allow-Origin"] = FRONTEND_URL
    header["Access-Control-Allow-Credentials"] = "true"
    return response