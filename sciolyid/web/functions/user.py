import os
import time
from typing import Dict, Union

import requests
from flask import abort, session

import sciolyid.config as config

PROFILE_URL = "https://discord.com/api/users/{id}"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{id}/{avatar}.{ext}"
DEFAULT_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/{discrim}.png"
INVITE_TO_ID_URL = "https://discord.com/api/invites/{code}"

SESSION_EXPIRE: int = 432000  # time (seconds) before expiring the session


class DiscordBotAuth(requests.auth.AuthBase):
    def __call__(self, request):
        request.headers["Authorization"] = (
            "Bot " + os.environ[config.options["bot_token_env"]]
        )
        return request


def fetch_profile(user_id: Union[int, str]) -> Dict[str, str]:
    url = PROFILE_URL.format(id=user_id)
    resp = requests.get(url, auth=DiscordBotAuth(), timeout=10)
    if resp.status_code != 200:
        abort(404, "Failed to fetch profile")
    json: dict = resp.json()

    profile: Dict[str, str] = dict()
    profile["username"] = f"{json['username']}#{json['discriminator']}"
    if json["avatar"]:
        profile["avatar"] = AVATAR_URL.format(
            id=user_id,
            avatar=json["avatar"],
            ext=("gif" if json["avatar"].startswith("a_") else "png"),
        )
    else:
        profile["avatar"] = DEFAULT_AVATAR_URL.format(
            discrim=int(json["discriminator"]) % 5
        )

    return profile


def fetch_server_id():
    if config.options.get("verification_server_id", None):
        return config.options.get("verification_server_id")
    url = INVITE_TO_ID_URL.format(
        code=config.options["verification_server"].split("/")[-1]
    )
    resp = requests.get(url, auth=DiscordBotAuth(), timeout=10)
    if resp.status_code != 200:
        abort(404, "Failed to fetch id")
    json: dict = resp.json()
    config.options["verification_server_id"] = json["guild"]["id"]
    return json["guild"]["id"]


def get_user_id() -> str:
    date: int = int(session.get("date", 0))
    if (time.time() - date) > SESSION_EXPIRE:
        abort(403, "Your session expired")
    uid: str = session["uid"]
    return uid
