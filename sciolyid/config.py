# config.py | config data
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

from typing import Dict, Optional, Any

required: Dict[str, Optional[str]] = {
    "bot_description": None,  # short bot description
    "bot_signature": None,  # signature for embeds
    "prefixes": None,  # bot prefixes, primary prefix is first in list
    "id_type": None,  # stars, fossils, muscles, etc. - plural noun
    "support_server": None,  # link to discord support server
    "source_link": None,  # link to source code (may be hosted on github)
    "name": None,  # all lowercase, no spaces, doesn't really matter what this is
}

default_image_required: Dict[str, Optional[str]] = {
    "github_image_repo_url": None,  # link to github image repo
}

web_required: Dict[str, Optional[str]] = {
    "client_id": None,  # discord client id
    "base_image_url": None,  # root of where images are hosted
    "validation_repo_url": None,  # github repo where images are temporarily held
}

optional: Dict[str, Any] = {
    "members_intent": False,  # whether the privileged members intent is enabled in the developer portal
    "download_func": None,  # asyncronous function that downloads images locally to download_dir
    "refresh_images": True,  # whether to run download_func once every 24 hours with None as an argument
    "evict_images": False,  # whether to delete items from download_dir
    "download_dir": "github_download/",  # local directory containing media (images)
    "data_dir": "data/",  # local directory containing the id data
    "group_dir": "group/",  # directory within data_dir containing group lists
    "state_dir": "state/",  # directory within data_dir containing alternate lists
    "state_roles": False,  # allow state roles
    "default_state_list": "NATS",  # name of the "state" that should be considered default
    "wikipedia_file": "wikipedia.txt",  # filename within data_dir containing wiki urls for every item
    "meme_file": None,
    "logs": True,  # enable logging
    "log_dir": "logs/",  # directory for text logs/backups
    "bot_files_dir": "",  # folder for bot generated files (downloaded images, logs)
    "short_id_type": "",  # short (usually 1 letter) form of id_type, used as alias for the pic command
    "invite": "This bot is currently not available outside the support server.",  # bot server invite link
    "authors": "person_v1.32, hmmm, and EraserBird",  # creator names
    # "id_groups": True,  # true/false - if you want to be able to select certain groups of items to id, set automatically from "category_name"
    "category_name": None,  # space thing, bird order, muscle group - what you are splitting groups by
    "category_aliases": {},  # aliases for categories
    "disable_extensions": [],  # bot extensions to disable (media, check, skip, hint, score, sessions, race, other)
    "custom_extensions": [],  # custom bot extensions to enable
    "sentry": False,  # enable sentry.io error tracking
    "local_redis": True,  # use a local redis server instead of a remote url
    "bot_token_env": "token",  # name of environment variable containing the discord bot token
    "sentry_dsn_env": "SENTRY_DISCORD_DSN",  # name of environment variable containing the sentry dsn
    "redis_env": "REDIS_URL",  # name of environment variable containing the redis database url
    "backups_channel": None,  # discord channel id to upload database backups (None/False to disable)
    "backups_dir": "backups/",  # directory to put database backup files before uploading
    "holidays": True,  # enable special features on select holidays
    "sendas": True,  # enable the "sendas" command
}

web_optional: Dict[str, Any] = {
    "tmp_upload_dir": "uploaded/",  # directory for temporary file storage
    "validation_local_dir": "validation_repo/",  # directory for cloning the validation repo
    "git_token_env": "GIT_TOKEN",  # environment variable with github auth token
    "git_user_env": "GIT_USERNAME",  # environment variable with github auth token
    "git_email_env": "GIT_EMAIL",  # environment variable with github auth token
    "validation_repo_dir": "",  # directory in validation repo to store files
    "hashes_url": [],  # urls to raw hashes.csv file in both image repos
    "ids_url": [],  # urls to raw ids.csv file in both image repos
    "commit_url_format": [],  # a format string for commit urls to both repos - image repo is first, validation repo is second
    "sentry_web_dsn_env": "SENTRY_API_DSN",  # name of environment variable containing the sentry dsn
    "celery_broker_env": "CELERY_BROKER_URL",  # name of environment variable with the database url for celery (broker)
    "secret_key_env": "FLASK_SECRET_KEY",  # name of environment variable for signed cookies secret key
    "frontend_url_env": "FRONTEND_URL",  # name of environment variable for frontend url
    "client_secret_env": "DISCORD_CLIENT_SECRET",  # name of environment variable for discord client secret
    "discord_webhook_env": "DISCORD_WEBHOOK_URL",  # webhook url for discord notification log
    "verification_server": None,  # invite to special discord server for people adding images, default to support server
}

options: Dict[str, Any] = {
    k: v
    for d in (required, default_image_required, web_required, optional, web_optional)
    for k, v in list(d.items())
}


class BotConfigError(Exception):
    def __init__(
        self, message="An error occurred in the config process."
    ):  # pylint: disable=useless-super-delegation
        super().__init__(message)
