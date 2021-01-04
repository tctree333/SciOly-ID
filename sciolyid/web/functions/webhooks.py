# functions/webhooks.py | helper functions for working with Discord webhooks
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

import datetime
import os

import requests
from discord import Color, Embed, RequestsWebhookAdapter, Webhook

import sciolyid.config as config
from sciolyid.web.functions.user import (
    AVATAR_URL,
    PROFILE_URL,
    DiscordBotAuth,
    fetch_profile,
)

WEBHOOK_URL = os.getenv(config.options["discord_webhook_env"], None)

if WEBHOOK_URL:
    webhook = Webhook.from_url(WEBHOOK_URL, adapter=RequestsWebhookAdapter())

    def bot_info() -> dict:
        url = PROFILE_URL.format(id="@me")
        resp = requests.get(url, auth=DiscordBotAuth(), timeout=10)
        json: dict = resp.json()

        output: dict = {}
        output["avatar"] = (
            AVATAR_URL.format(
                id=json["id"],
                avatar=json["avatar"],
                ext=("gif" if json["avatar"].startswith("a_") else "png"),
            )
            if json["avatar"]
            else None
        )
        output["name"] = json["username"]
        return output

    bot = bot_info()
    BOT_AVATAR = bot["avatar"]
    BOT_NAME = bot["name"]


def send(type_of: str, **opt):
    """Wrapper to send embed webhooks.

    type: str - one of "add", "verify", "valid", "error"

    opt:
    - add:
        - num: int/str - number of images added
        - items: List[str] - id items added
        - user_id: str - user id
    - verify:
        - action: str - one of "valid", "invalid", "duplicate"
        - user_id: str - user id
    - valid:
        - added: int - num added
        - rejected: int - num rejected
        - items: List[str] - id items added
        - urls: Tuple/List[str, str] - git diff links, image first, then verification
    - error:
        - message: str - error message
    """
    if not WEBHOOK_URL:
        return

    if type_of not in ("add", "verify", "valid", "error"):
        raise TypeError("Invalid type_of value!")

    if type_of == "add":
        username = fetch_profile(opt["user_id"])["username"]
        items = opt["items"]
        items[-1] = "and " + items[-1] if len(items) > 1 else items[-1]

        name = "New images added!"
        content = (
            f"<@{opt['user_id']}> ({username}) added {opt['num']} new "
            + f"image{'' if opt['num'] == 1 else 's'} for {(' ' if len(items)== 2 else ', ').join(items)}!"
        )
        color = Color.dark_green()

    elif type_of == "verify":
        username = fetch_profile(opt["user_id"])["username"]
        color_options = {
            "valid": Color.green(),
            "invalid": Color.red(),
            "duplicate": Color.gold(),
        }

        name = "Image verified!"
        content = (
            f"<@{opt['user_id']}> ({username}) marked an image as {opt['action']}."
        )
        color = color_options[opt["action"]]

    elif type_of == "valid":
        items = opt["items"]
        if opt["added"] != 0:
            items[-1] = "and " + items[-1] if len(items) > 1 else items[-1]

        name = "Updated images!"
        content = (
            f"**{opt['added']}** new image{'' if opt['added'] == 1 else 's'} {'was' if opt['added'] == 1 else 'were'} added"
            + (
                "."
                if opt["added"] == 0
                else f" for {(' ' if len(items)== 2 else ', ').join(items)}."
            )
            + f" **{opt['rejected']}** {'was' if opt['rejected'] == 1 else 'were'} rejected.\n"
            + f"[Image Repo Commit]({opt['urls'][0]}) **|** [Verification Repo Commit]({opt['urls'][1]})"
        )
        color = Color.blue()

    elif type_of == "error":
        name = "An error occurred!"
        content = opt["message"]
        color = Color.dark_red()

    embed = Embed(type="rich", color=color, title=name, description=content)
    embed.set_footer(
        text=datetime.datetime.now().strftime("%a, %b %d, %Y at %I:%M:%S %p")
    )

    webhook.send(username=f"{BOT_NAME} Web", avatar_url=BOT_AVATAR, embed=embed)
