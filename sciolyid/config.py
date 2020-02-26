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
    "download_dir": "github_download",
    "data_dir": "data/",
    "list_dir": "lists",
    "wikipedia_file": "wikipedia.txt",
    "alias_file": "aliases.txt",
    "logs": True,
    "log_dir": "logs",
    "file_folder": "",
    "invite": "This bot is currently not avaliable outside the support server.",  # bot server invite link
    "authors": "person_v1.32, hmmm, and EraserBird",  # creator names
    "id_groups": True,  # true/false - if you want to be able to select certain groups of items to id
    "category_aliases": {},  # aliases for categories
    "disable_extensions": [],
    "custom_extensions": [],
    "sentry": False,
    "local_redis": True,
    "bot_token_env": "token",
    "sentry_dsn_env": "SENTRY_DISCORD_DSN",
    "redis_env": "REDIS_URL",
}

options = {d: e for d, e in list(required.items()) + list(id_required.items()) + list(optional.items())}

class BotConfigError(Exception):
    def __init__(self, message="An error occurred in the config process."):  # pylint: disable=useless-super-delegation
        super().__init__(message)
