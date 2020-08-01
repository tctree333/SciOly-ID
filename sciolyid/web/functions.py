import imghdr
import os
import time
from typing import Dict, Union

import flask
import requests
from PIL import Image

import sciolyid.config as config

PROFILE_URL = "https://discord.com/api/users/{id}"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{id}/{avatar}.{ext}"


class DiscordBotAuth(requests.auth.AuthBase):
    def __call__(self, request):
        request.headers["Authorization"] = (
            "Bot " + os.environ[config.options["bot_token_env"]]
        )
        return request


def fetch_profile(user_id: Union[int, str]) -> Dict[str, str]:
    url = PROFILE_URL.format(id=user_id)
    resp = requests.get(url, auth=DiscordBotAuth())
    if resp.status_code != 200:
        flask.abort(500, "Failed to fetch profile")
    json: dict = resp.json()

    profile: Dict[str, str] = dict()
    profile["username"] = f"{json['username']}#{json['discriminator']}"
    profile["avatar"] = AVATAR_URL.format(
        id=user_id,
        avatar=json["avatar"],
        ext=("gif" if json["avatar"].startswith("a_") else "png"),
    )

    return profile
