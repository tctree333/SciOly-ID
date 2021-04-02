import datetime
import string

from sciolyid.data import database, logger


async def channel_setup(ctx):
    """Sets up a new discord channel.

    `ctx` - Discord context object
    """
    logger.info("checking channel setup")
    if not database.exists(f"channel:{ctx.channel.id}"):
        database.hset(
            f"channel:{ctx.channel.id}",
            mapping={"item": "", "answered": 1, "prevJ": 20, "prevI": ""},
        )
        # true = 1, false = 0, prevJ is 20 to define as integer
        logger.info("channel data added")
        await ctx.send("Ok, setup! I'm all ready to use!")

    if database.zscore("score:global", str(ctx.channel.id)) is None:
        database.zadd("score:global", {str(ctx.channel.id): 0})
        logger.info("channel score added")

    if ctx.guild is not None:
        database.zadd("channels:global", {f"{ctx.guild.id}:{ctx.channel.id}": 0})


async def user_setup(ctx):
    """Sets up a new discord user for score tracking.

    `ctx` - Discord context object
    """
    logger.info("checking user data")
    if database.zscore("users:global", str(ctx.author.id)) is None:
        database.zadd("users:global", {str(ctx.author.id): 0})
        logger.info("user global added")
        await ctx.send("Welcome <@" + str(ctx.author.id) + ">!")

    date = str(datetime.datetime.now(datetime.timezone.utc).date())
    if database.zscore(f"daily.score:{date}", str(ctx.author.id)) is None:
        database.zadd(f"daily.score:{date}", {str(ctx.author.id): 0})
        logger.info("user daily added")

    # Add streak
    if (database.zscore("streak:global", str(ctx.author.id)) is None) or (
        database.zscore("streak.max:global", str(ctx.author.id)) is None
    ):
        database.zadd("streak:global", {str(ctx.author.id): 0})
        database.zadd("streak.max:global", {str(ctx.author.id): 0})
        logger.info("added streak")

    if ctx.guild is not None:
        global_score = database.zscore("users:global", str(ctx.author.id))
        database.zadd(
            f"users.server:{ctx.guild.id}", {str(ctx.author.id): global_score}
        )
        logger.info("synced scores")


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

    if (
        database.zscore(f"incorrect.user:{ctx.author.id}", string.capwords(item))
        is not None
    ):
        logger.info("incorrect item user ok")
    else:
        database.zadd(f"incorrect.user:{ctx.author.id}", {string.capwords(item): 0})
        logger.info("incorrect item user added")

    if (
        database.zscore(f"correct.user:{ctx.author.id}", string.capwords(item))
        is not None
    ):
        logger.info("correct item user ok")
    else:
        database.zadd(f"correct.user:{ctx.author.id}", {string.capwords(item): 0})
        logger.info("correct item user added")

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
            database.zadd(
                f"incorrect.server:{ctx.guild.id}", {string.capwords(item): 0}
            )
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
            database.zadd(
                f"session.incorrect:{ctx.author.id}", {string.capwords(item): 0}
            )
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
        database.zincrby(
            f"incorrect.server:{ctx.guild.id}", amount, string.capwords(item)
        )
    else:
        logger.info("dm context")
    if database.exists(f"session.data:{ctx.author.id}"):
        logger.info("session in session")
        database.zincrby(
            f"session.incorrect:{ctx.author.id}", amount, string.capwords(item)
        )
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
