# hint.py | commands for giving hints
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

from typing import Literal

from discord import app_commands
from discord.ext import commands

from sciolyid.data import database, logger
from sciolyid.functions import CustomCooldown


class Hint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # give hint
    @commands.hybrid_command(
        help="- Gives first letter of current image",
        usage="[count|c last|l all|a]",
        aliases=["h"],
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    @app_commands.describe(option="type of hint to give")
    @app_commands.rename(option="type")
    async def hint(
        self,
        ctx: commands.Context,
        option: Literal["count", "last", "all", "c", "l", "a", "first"] = "first",
    ):
        logger.info("command: hint")

        current_item = database.hget(f"channel:{ctx.channel.id}", "item").decode(
            "utf-8"
        )
        if current_item != "":  # check if there is item
            if len(option) == 0 or option == "first":
                await ctx.send(f"The first letter is {current_item[0]}.")
            elif option == "count" or option == "c":
                await ctx.send(f"The answer has {str(len(current_item))} letters.")
            elif option == "last" or option == "l":
                await ctx.send(f"The last letter is {current_item[-1]}.")
            elif option == "all" or option == "a":
                the_hint = "`" + current_item[0]
                for letter in current_item[1:-1]:
                    if letter != " ":
                        the_hint += " _ "
                    else:
                        the_hint += "   "
                await ctx.send(the_hint + current_item[-1] + "`")
            else:
                await ctx.send(f"The first letter is {current_item[0]}.")
        else:
            await ctx.send("You need to ask for a image first!")


async def setup(bot):
    await bot.add_cog(Hint(bot))
