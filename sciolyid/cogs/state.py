# state.py | commands for alternate lists
# Copyright (C) 2019-2021  EraserBird, person_v1.32

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

import string

import discord
from discord.ext import commands
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.data import GenericError, logger, states
from sciolyid.functions import CustomCooldown


class States(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def broken_send(self, ctx, message, between=""):
        pages = []
        temp_out = ""
        for line in message.splitlines(keepends=True):
            temp_out += line
            if len(temp_out) > 1700:
                temp_out = f"{between}{temp_out}{between}"
                pages.append(temp_out.strip())
                temp_out = ""
        temp_out = f"{between}{temp_out}{between}"
        if temp_out.strip():
            pages.append(temp_out.strip())
        for item in pages:
            await ctx.send(item)

    # set state role
    @commands.command(
        help=f"- Sets an alternate {config.options['id_type']} list",
        name="set",
        aliases=["state", "alt"],
    )
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.user))
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def state(self, ctx, *, args):
        logger.info("command: state set")

        raw_roles = ctx.author.roles
        role_ids = [role.id for role in raw_roles]
        role_names = [role.name.lower() for role in ctx.author.roles]
        args = args.upper().split(" ")

        added = []
        removed = []
        invalid = []
        for arg in args:
            if arg not in states:
                logger.info("invalid state")
                invalid.append(arg)

            # gets similarities
            elif not set(role_names).intersection(set(states[arg]["aliases"])):
                # need to add role (does not have role)
                logger.info("add roles")
                raw_roles = ctx.guild.roles
                guild_role_names = [role.name.lower() for role in raw_roles]
                guild_role_ids = [role.id for role in raw_roles]

                if states[arg]["aliases"][0].lower() in guild_role_names:
                    # guild has role
                    index = guild_role_names.index(states[arg]["aliases"][0].lower())
                    role = ctx.guild.get_role(guild_role_ids[index])

                else:
                    # create role
                    logger.info("creating role")
                    role = await ctx.guild.create_role(
                        name=string.capwords(states[arg]["aliases"][0]),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                        reason=f"Create role for alternate {config.options['id_type']} list",
                    )

                await ctx.author.add_roles(
                    role,
                    reason=f"Set role for alternate {config.options['id_type']} list",
                )
                added.append(role.name)

            else:
                # have roles already (there were similarities)
                logger.info("already has role, removing")
                index = role_names.index(states[arg]["aliases"][0].lower())
                role = ctx.guild.get_role(role_ids[index])
                await ctx.author.remove_roles(
                    role,
                    reason=f"Remove role for alternate {config.options['id_type']} list",
                )
                removed.append(role.name)

        await ctx.send(
            (
                f"**Sorry,** `{'`, `'.join(invalid)}` **{'are' if len(invalid) > 1 else 'is'} not a valid list.**\n"
                + f"*Valid Lists:* `{'`, `'.join(states.keys())}`\n"
                if invalid
                else ""
            )
            + (
                f"**Added the** `{'`, `'.join(added)}` **role{'s' if len(added) > 1 else ''}**\n"
                if added
                else ""
            )
            + (
                f"**Removed the** `{'`, `'.join(removed)}` **role{'s' if len(removed) > 1 else ''}**\n"
                if removed
                else ""
            )
        )

    @state.error
    async def set_error(self, ctx, error):
        logger.info("state set error")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"**Please enter an alternate list.**\n*Valid Lists:* `{'`, `'.join(states.keys())}`"
            )
        elif isinstance(error, commands.CommandOnCooldown):  # send cooldown
            await ctx.send(
                f"**Cooldown.** Try again after {str(round(error.retry_after))}s.",
                delete_after=5.0,
            )
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("**This command is unavailable in DMs!**")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "**The bot does not have enough permissions to fully function.**\n"
                + f"**Permissions Missing:** `{', '.join(map(str, error.missing_perms))}`\n"
                + "*Please try again once the correct permissions are set.*"
            )
        elif isinstance(error, GenericError):
            if error.code == 192:
                # channel is ignored
                return
            if error.code == 842:
                await ctx.send("**Sorry, you cannot use this command.**")
            elif error.code == 666:
                logger.info("GenericError 666")
            elif error.code == 201:
                logger.info("HTTP Error")
                capture_exception(error)
                await ctx.send(
                    "**An unexpected HTTP Error has occurred.**\n *Please try again.*"
                )
            else:
                logger.info("uncaught generic error")
                capture_exception(error)
                await ctx.send(
                    "**An uncaught generic error has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again.*\n"
                    + "**Error:** "
                    + str(error)
                )
                await ctx.send("https://discord.gg/fXxYyDJ")
                raise error
        else:
            capture_exception(error)
            await ctx.send(
                "**An uncaught set error has occurred.**\n"
                + "*Please log this message in #support in the support server below, or try again.*\n"
                + "**Error:** "
                + str(error)
            )
            await ctx.send("https://discord.gg/fXxYyDJ")
            raise error


def setup(bot):
    bot.add_cog(States(bot))
