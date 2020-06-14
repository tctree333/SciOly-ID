# config.py | config data
# Copyright (C) 2019-2020  EraserBird, person_v1.32, hmmm

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

required = {
    "bot_description": None,  # short bot description
    "bot_signature": None,  # signature for embeds
    "prefixes": None,  # bot prefixes, primary prefix is first in list
    "id_type": None,  # stars, fossils, muscles, etc. - plural noun
    "github_image_repo_url": None,  # link to github image repo
    "support_server": None,  # link to discord support server
    "source_link": None,  # link to source code (may be hosted on github)
}

id_required = {
    "category_name": None,  # space thing, bird order, muscle group - what you are splitting groups by
}

optional = {
    "name": "id-bot",  # all lowercase, no spaces, doesn't really matter what this is
    "download_func": None,  # asyncronous function that downloads images locally to download_dir
    "download_dir": "github_download/",  # local directory containing media (images)
    "data_dir": "data/",  # local directory containing the id data
    "list_dir": "lists/",  # directory within data_dir containing id lists
    "restricted_list_dir": None,  # directory within data_dir containg id lists that are avaliable by selection only
    "wikipedia_file": "wikipedia.txt",  # filename within data_dir containing wiki urls for every item
    "alias_file": "aliases.txt",  # filename within data_dir contiaining aliases for any item
    "meme_file": None,
    "logs": True,  # enable logging
    "log_dir": "logs/",  # directory for text logs/backups
    "bot_files_dir": "",  # folder for bot generated files (downloaded images, logs)
    "short_id_type": "",  # short (usually 1 letter) form of id_type, used as alias for the pic command
    "invite": "This bot is currently not avaliable outside the support server.",  # bot server invite link
    "authors": "person_v1.32, hmmm, and EraserBird",  # creator names
    "id_groups": True,  # true/false - if you want to be able to select certain groups of items to id
    "category_aliases": {},  # aliases for categories
    "disable_extensions": [],  # bot extensions to disable (media, check, skip, hint, score, sessions, race, other)
    "custom_extensions": [],  # custom bot extensions to enable
    "sentry": False,  # enable sentry.io error tracking
    "local_redis": True,  # use a local redis server instead of a remote url
    "bot_token_env": "token",  # name of environment variable containing the discord bot token
    "sentry_dsn_env": "SENTRY_DISCORD_DSN",  # name of environment variable containing the sentry dsn
    "redis_env": "REDIS_URL",  # name of environment variable containing the redis database url
    "backups_channel": None,  # discord channel id to upload database backups (None/False to disable)
    "backups_dir": "backups",  # directory to put database backup files before uploading
    "holidays": True,  # enable special features on select holidays
    "sendas": True,  # enable the "sendas" command
}

options = {
    d: e
    for d, e in list(required.items()) + list(id_required.items()) + list(optional.items())
}


class BotConfigError(Exception):
    def __init__(
        self, message="An error occurred in the config process."
    ):  # pylint: disable=useless-super-delegation
        super().__init__(message)
