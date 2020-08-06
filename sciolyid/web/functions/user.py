import os
import time
from typing import Dict, Union

import requests
from flask import abort, session

import sciolyid.config as config

PROFILE_URL = "https://discord.com/api/users/{id}"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{id}/{avatar}.{ext}"

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
        abort(500, "Failed to fetch profile")
    json: dict = resp.json()

    profile: Dict[str, str] = dict()
    profile["username"] = f"{json['username']}#{json['discriminator']}"
    profile["avatar"] = AVATAR_URL.format(
        id=user_id,
        avatar=json["avatar"],
        ext=("gif" if json["avatar"].startswith("a_") else "png"),
    )

    return profile


def get_user_id() -> str:
    date: int = int(session.get("date", 0))
    if (time.time() - date) > SESSION_EXPIRE:
        abort(403, "Your session expired")
    uid: str = session["uid"]
    return uid
