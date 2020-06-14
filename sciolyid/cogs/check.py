# check.py | commands to check answers
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

from discord.ext import commands

from sciolyid.data import database, get_aliases, get_wiki_url, logger
from sciolyid.functions import (CustomCooldown, incorrect_increment,
                                item_setup, score_increment, session_increment,
                                spellcheck_list, streak_increment)


class Check(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Check command - argument is the guess
    @commands.command(help="- Checks your answer.", usage="guess", aliases=["guess", "c"])
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.user))
    async def check(self, ctx, *, arg):
        logger.info("command: check")

        current_item = database.hget(f"channel:{ctx.channel.id}", "item").decode("utf-8")
        if current_item == "":  # no image
            await ctx.send("You must ask for a image first!")
        else:  # if there is a image, it checks answer
            arg = arg.lower()
            current_item = current_item.lower()
            logger.info("current_item: " + current_item)
            logger.info("arg: " + arg)

            item_setup(ctx, current_item)
            correct_list = map(lambda x: x.lower(), get_aliases(current_item))

            if database.exists(f"race.data:{ctx.channel.id}"):
                logger.info("race in session")
                if database.hget(f"race.data:{ctx.channel.id}", "strict"):
                    logger.info("strict spelling")
                    correct = arg in correct_list
                else:
                    logger.info("spelling leniency")
                    correct = spellcheck_list(arg, correct_list)
            else:
                logger.info("no race")
                if database.hget(f"session.data:{ctx.author.id}", "strict"):
                    logger.info("strict spelling")
                    correct = arg in correct_list
                else:
                    logger.info("spelling leniency")
                    correct = spellcheck_list(arg, correct_list)

            if correct:
                logger.info("correct")

                database.hset(f"channel:{ctx.channel.id}", "item", "")
                database.hset(f"channel:{ctx.channel.id}", "answered", "1")

                session_increment(ctx, "correct", 1)
                streak_increment(ctx, 1)

                await ctx.send(
                    "Correct! Good job!"
                    if not database.exists(f"race.data:{ctx.channel.id}")
                    else f"**{ctx.author.mention}**, you are correct!"
                )
                url = get_wiki_url(ctx, current_item)
                await ctx.send(
                    url if not database.exists(f"race.data:{ctx.channel.id}") else f"<{url}>"
                )  # sends wiki page
                score_increment(ctx, 1)
                if database.exists(f"race.data:{ctx.channel.id}"):

                    limit = int(database.hget(f"race.data:{ctx.channel.id}", "limit"))
                    first = database.zrevrange(f"race.scores:{ctx.channel.id}", 0, 0, True)[0]
                    if int(first[1]) >= limit:
                        logger.info("race ending")
                        race = self.bot.get_cog("Race")
                        await race.stop_race_(ctx)
                    else:
                        logger.info("auto sending next image")
                        group, bw = database.hmget(
                            f"race.data:{ctx.channel.id}", ["group", "bw"]
                        )
                        media = self.bot.get_cog("Media")
                        await media.send_pic_(ctx, group.decode("utf-8"), bw.decode("utf-8"))

            else:
                logger.info("incorrect")

                streak_increment(ctx, None)
                session_increment(ctx, "incorrect", 1)
                incorrect_increment(ctx, str(current_item), 1)

                if database.exists(f"race.data:{ctx.channel.id}"):
                    await ctx.send("Sorry, that wasn't the right answer.")
                else:
                    database.hset(f"channel:{ctx.channel.id}", "item", "")
                    database.hset(f"channel:{ctx.channel.id}", "answered", "1")
                    await ctx.send("Sorry, the image was actually " + current_item + ".")
                    url = get_wiki_url(ctx, current_item)
                    await ctx.send(url)


def setup(bot):
    bot.add_cog(Check(bot))
