import os

import requests
import flask

import sciolyid.config as config

PROFILE_URL = "https://discord.com/api/users/{id}"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{id}/{avatar}.{ext}"


class DiscordBotAuth(requests.auth.AuthBase):
    def __call__(self, request):
        request.headers["Authorization"] = "Bot " + os.getenv(
            config.options["bot_token_env"]
        )
        return request


def fetch_profile(user_id):
    url = PROFILE_URL.format(id=user_id)
    resp = requests.get(url, auth=DiscordBotAuth())
    if resp.status_code != 200:
        flask.abort(500, "Failed to fetch profile")
    resp = resp.json()

    profile = dict()
    profile["username"] = f"{resp['username']}#{resp['discriminator']}"
    profile["avatar"] = AVATAR_URL.format(
        id=user_id,
        avatar=resp["avatar"],
        ext=("gif" if resp["avatar"].startswith("a_") else "png"),
    )

    return profile
