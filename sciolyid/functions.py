# functions.py | function definitions
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

import datetime
import difflib
import math
import os
import pickle
import string
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image

import sciolyid.config as config
from sciolyid.data import GenericError, database, groups, id_list, logger


async def channel_setup(ctx):
    """Sets up a new discord channel.
    
    `ctx` - Discord context object
    """
    logger.info("checking channel setup")
    if database.exists(f"channel:{ctx.channel.id}"):
        logger.info("channel data ok")
    else:
        database.hmset(
            f"channel:{ctx.channel.id}", {"item": "", "answered": 1, "prevJ": 20, "prevI": ""},
        )
        # true = 1, false = 0, prevJ is 20 to define as integer
        logger.info("channel data added")
        await ctx.send("Ok, setup! I'm all ready to use!")

    if database.zscore("score:global", str(ctx.channel.id)) is not None:
        logger.info("channel score ok")
    else:
        database.zadd("score:global", {str(ctx.channel.id): 0})
        logger.info("channel score added")

    if ctx.guild is not None:
        if database.zadd("channels:global", {f"{ctx.guild.id}:{ctx.channel.id}": 0}) is not 0:
            logger.info("server lookup ok")
        else:
            logger.info("server lookup added")


async def user_setup(ctx):
    """Sets up a new discord user for score tracking.
    
    `ctx` - Discord context object
    """
    logger.info("checking user data")
    if database.zscore("users:global", str(ctx.author.id)) is not None:
        logger.info("user global ok")
    else:
        database.zadd("users:global", {str(ctx.author.id): 0})
        logger.info("user global added")
        await ctx.send("Welcome <@" + str(ctx.author.id) + ">!")

    date = str(datetime.datetime.now(datetime.timezone.utc).date())
    if database.zscore(f"daily.score:{date}", str(ctx.author.id)) is not None:
        logger.info("user daily ok")
    else:
        database.zadd(f"daily.score:{date}", {str(ctx.author.id): 0})
        logger.info("user daily added")

    # Add streak
    if (database.zscore("streak:global", str(ctx.author.id)) is not None) and (
        database.zscore("streak.max:global", str(ctx.author.id)) is not None
    ):
        logger.info("user streak in already")
    else:
        database.zadd("streak:global", {str(ctx.author.id): 0})
        database.zadd("streak.max:global", {str(ctx.author.id): 0})
        logger.info("added streak")

    if ctx.guild is not None:
        logger.info("no dm")
        if database.zscore(f"users.server:{ctx.guild.id}", str(ctx.author.id)) is not None:
            server_score = database.zscore(f"users.server:{ctx.guild.id}", str(ctx.author.id))
            global_score = database.zscore("users:global", str(ctx.author.id))
            if server_score is global_score:
                logger.info("user server ok")
            else:
                database.zadd(
                    f"users.server:{ctx.guild.id}", {str(ctx.author.id): global_score}
                )
        else:
            score = int(database.zscore("users:global", str(ctx.author.id)))
            database.zadd(f"users.server:{ctx.guild.id}", {str(ctx.author.id): score})
            logger.info("user server added")
    else:
        logger.info("dm context")


def item_setup(ctx, item: str):
    """Sets up a new item for incorrect tracking.
    
    `ctx` - Discord context object
    `item` - item to setup
    """
    logger.info("checking item data")
    if database.zscore("incorrect:global", string.capwords(item)) is not None:
        logger.info("item global ok")
    else:
        database.zadd("incorrect:global", {string.capwords(item): 0})
        logger.info("item global added")

    if database.zscore(f"incorrect.user:{ctx.author.id}", string.capwords(item)) is not None:
        logger.info("item user ok")
    else:
        database.zadd(f"incorrect.user:{ctx.author.id}", {string.capwords(item): 0})
        logger.info("item user added")

    date = str(datetime.datetime.now(datetime.timezone.utc).date())
    if database.zscore(f"daily.incorrect:{date}", string.capwords(item)) is not None:
        logger.info("item daily ok")
    else:
        database.zadd(f"daily.incorrect:{date}", {string.capwords(item): 0})
        logger.info("item daily added")

    if database.zscore("frequency.item:global", string.capwords(item)) is not None:
        logger.info("item freq global ok")
    else:
        database.zadd("frequency.item:global", {string.capwords(item): 0})
        logger.info("item freq global added")

    if ctx.guild is not None:
        logger.info("no dm")
        if (
            database.zscore(f"incorrect.server:{ctx.guild.id}", string.capwords(item))
            is not None
        ):
            logger.info("item server ok")
        else:
            database.zadd(f"incorrect.server:{ctx.guild.id}", {string.capwords(item): 0})
            logger.info("item server added")
    else:
        logger.info("dm context")

    if database.exists(f"session.data:{ctx.author.id}"):
        logger.info("session in session")
        if (
            database.zscore(f"session.incorrect:{ctx.author.id}", string.capwords(item))
            is not None
        ):
            logger.info("item session ok")
        else:
            database.zadd(f"session.incorrect:{ctx.author.id}", {string.capwords(item): 0})
            logger.info("item session added")
    else:
        logger.info("no session")


def session_increment(ctx, item: str, amount: int = 1):
    """Increments the value of a database hash field by `amount`.

    `ctx` - Discord context object\n
    `item` - hash field to increment (see data.py for details,
    possible values include correct, incorrect, total)\n
    `amount` (int) - amount to increment by, usually 1
    """
    if database.exists(f"session.data:{ctx.author.id}"):
        logger.info("session active")
        logger.info(f"incrementing {item} by {amount}")
        value = int(database.hget(f"session.data:{ctx.author.id}", item))
        value += int(amount)
        database.hset(f"session.data:{ctx.author.id}", item, str(value))
    else:
        logger.info("session not active")


def incorrect_increment(ctx, item: str, amount: int = 1):
    """Increments the value of an incorrect item by `amount`.

    `ctx` - Discord context object\n
    `item` - item that was incorrect\n
    `amount` (int) - amount to increment by, usually 1
    """
    logger.info(f"incrementing incorrect {item} by {amount}")
    date = str(datetime.datetime.now(datetime.timezone.utc).date())
    database.zincrby("incorrect:global", amount, string.capwords(item))
    database.zincrby(f"incorrect.user:{ctx.author.id}", amount, string.capwords(item))
    database.zincrby(f"daily.incorrect:{date}", amount, string.capwords(item))
    if ctx.guild is not None:
        logger.info("no dm")
        database.zincrby(f"incorrect.server:{ctx.guild.id}", amount, string.capwords(item))
    else:
        logger.info("dm context")
    if database.exists(f"session.data:{ctx.author.id}"):
        logger.info("session in session")
        database.zincrby(f"session.incorrect:{ctx.author.id}", amount, string.capwords(item))
    else:
        logger.info("no session")


def score_increment(ctx, amount: int = 1):
    """Increments the score of a user by `amount`.

    `ctx` - Discord context object\n
    `amount` (int) - amount to increment by, usually 1
    """
    logger.info(f"incrementing score by {amount}")
    date = str(datetime.datetime.now(datetime.timezone.utc).date())
    database.zincrby("score:global", amount, str(ctx.channel.id))
    database.zincrby("users:global", amount, str(ctx.author.id))
    database.zincrby(f"daily.score:{date}", amount, str(ctx.author.id))
    if ctx.guild is not None:
        logger.info("no dm")
        database.zincrby(f"users.server:{ctx.guild.id}", amount, str(ctx.author.id))
    else:
        logger.info("dm context")
    if database.exists(f"race.data:{ctx.channel.id}"):
        logger.info("race in session")
        database.zincrby(f"race.scores:{ctx.channel.id}", amount, str(ctx.author.id))


def streak_increment(ctx, amount: int):
    """Increments the streak of a user by `amount`.

    `ctx` - Discord context object\n
    `amount` (int) - amount to increment by, usually 1.
    If amount is None, the streak is ended.
    """

    if amount is not None:
        # increment streak and update max
        database.zincrby("streak:global", amount, ctx.author.id)
        if database.zscore("streak:global", ctx.author.id) > database.zscore(
            "streak.max:global", ctx.author.id
        ):
            database.zadd(
                "streak.max:global",
                {ctx.author.id: database.zscore("streak:global", ctx.author.id)},
            )
    else:
        database.zadd("streak:global", {ctx.author.id: 0})


def black_and_white(input_image_path) -> BytesIO:
    """Returns a black and white version of an image.

    Output type is a file object (BytesIO).

    `input_image_path` - path to image (string) or file object
    """
    logger.info("black and white")
    with Image.open(input_image_path) as color_image:
        bw = color_image.convert("L")
        final_buffer = BytesIO()
        bw.save(final_buffer, "png")
    final_buffer.seek(0)
    return final_buffer


async def send_leaderboard(ctx, title, page, database_key=None, data=None):
    logger.info("building/sending leaderboard")

    if database_key is None and data is None:
        raise GenericError("database_key and data are both NoneType", 990)
    elif database_key is not None and data is not None:
        raise GenericError("database_key and data are both set", 990)

    if page < 1:
        page = 1

    entry_count = (
        int(database.zcard(database_key)) if database_key is not None else data.count()
    )
    page = (page * 10) - 10

    if entry_count == 0:
        logger.info(f"no items in {database_key}")
        await ctx.send("There are no items in the database.")
        return

    if page > entry_count:
        page = entry_count - (entry_count % 10)

    items_per_page = 10
    leaderboard_list = (
        map(
            lambda x: (x[0].decode("utf-8"), x[1]),
            database.zrevrangebyscore(
                database_key, "+inf", "-inf", page, items_per_page, True
            ),
        )
        if database_key is not None
        else data.iloc[page : page + items_per_page - 1].items()
    )
    embed = discord.Embed(type="rich", colour=discord.Color.blurple())
    embed.set_author(name=config.options["bot_signature"])
    leaderboard = ""

    for i, stats in enumerate(leaderboard_list):
        leaderboard += f"{i+1+page}. **{stats[0]}** - {int(stats[1])}\n"
    embed.add_field(name=title, value=leaderboard, inline=False)

    await ctx.send(embed=embed)


def build_id_list(group_str: str = ""):
    logger.info("building id list")
    categories = group_str.split(" ")
    logger.info(f"categories: {categories}")

    id_choices = []
    category_output = ""

    if not config.options["id_groups"]:
        logger.info("no groups allowed")
        return (id_list, "None")

    group_args = []
    for group in set(
        list(groups.keys())
        + [
            item
            for group in groups.keys()
            for item in config.options["category_aliases"][group]
        ]
    ).intersection({category.lower() for category in categories}):
        if group not in groups.keys():
            group = next(
                key
                for key, value in config.options["category_aliases"].items()
                if group in value
            )
        group_args.append(group)
    logger.info(f"group_args: {group_args}")

    category_output = " ".join(group_args).strip()
    for group in group_args:
        logger.info(f"group: {group}")
        id_choices += groups[group]

    if not id_choices:
        logger.info("no choices")
        id_choices += id_list
        category_output = "None"

    logger.info(f"id_choices length: {len(id_choices)}")
    logger.info(f"category_output: {category_output}")

    return (id_choices, category_output)


def backup_all():
    """Backs up the database to a file.
    
    This function serializes all data in the REDIS database
    into a file in the `backups` directory.

    This function is run with a task every 6 hours and sends the files
    to a specified discord channel.
    """
    logger.info("Starting Backup")
    logger.info("Creating Dump")
    keys = (key.decode("utf-8") for key in database.keys())
    dump = ((database.dump(key), key) for key in keys)
    logger.info("Finished Dump")
    logger.info("Writing To File")
    try:
        os.mkdir(config.options["backups_dir"])
        logger.info("Created backups directory")
    except FileExistsError:
        logger.info("Backups directory exists")
    with open(config.options["backups_dir"] + "dump.dump", "wb") as f:
        with open(config.options["backups_dir"] + "keys.txt", "w") as k:
            for item, key in dump:
                pickle.dump(item, f)
                k.write(f"{key}\n")
    logger.info("Backup Finished")


async def fools(ctx):
    logger.info(f"holiday check: invoked command: {str(ctx.command)}")
    if str(ctx.command) in ("leaderboard", "missed", "score", "streak", "userscore"):
        embed = discord.Embed(
            type="rich", colour=discord.Color.blurple(), title=f"{str(ctx.command).title()}"
        )
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name=f"{str(ctx.command).title()}",
            value="User scores and data have been cleared. We apologize for the inconvenience.",
            inline=False,
        )
        await ctx.send(embed=embed)
        raise GenericError(code=666)
    return True


def spellcheck_list(word_to_check, correct_list, abs_cutoff=None):
    for correct_word in correct_list:
        if abs_cutoff is None:
            relative_cutoff = math.floor(len(correct_word) / 3)
        if spellcheck(word_to_check, correct_word, relative_cutoff) is True:
            return True
    return False


def spellcheck(worda, wordb, cutoff=3):
    """Checks if two words are close to each other.
    
    `worda` (str) - first word to compare
    `wordb` (str) - second word to compare
    `cutoff` (int) - allowed difference amount
    """
    worda = worda.lower().replace("-", " ").replace("'", "")
    wordb = wordb.lower().replace("-", " ").replace("'", "")
    shorterword = min(worda, wordb, key=len)
    if worda != wordb:
        if len(list(difflib.Differ().compare(worda, wordb))) - len(shorterword) >= cutoff:
            return False
    return True


class CustomCooldown:
    """Halve cooldown times in DM channels."""

    # Code adapted from discord.py example
    def __init__(
        self,
        per: float,
        disable: bool = False,
        bucket: commands.BucketType = commands.BucketType.channel,
    ):
        """Initialize a custom cooldown.

            `per` (float) - Cooldown default duration, halves in DM channels
            `bucket` (commands.BucketType) - cooldown scope, defaults to channel
            """
        rate = 1
        dm_per = per / 2
        race_per = 0.5
        self.disable = disable
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, bucket)
        self.dm_mapping = commands.CooldownMapping.from_cooldown(rate, dm_per, bucket)
        self.race_mapping = commands.CooldownMapping.from_cooldown(rate, race_per, bucket)

    def __call__(self, ctx: commands.Context):
        if not self.disable and ctx.guild is None:
            # halve cooldown in DMs
            bucket = self.dm_mapping.get_bucket(ctx.message)

        elif ctx.command.name.startswith("check") and ctx.channel.name.startswith("racing"):
            # tiny check cooldown in racing channels
            bucket = self.race_mapping.get_bucket(ctx.message)

        else:
            bucket = self.default_mapping.get_bucket(ctx.message)

        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True
