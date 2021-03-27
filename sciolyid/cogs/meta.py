# meta.py | commands about the bot
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

import typing

import discord
from discord.ext import commands
from discord.utils import escape_markdown as esc

import sciolyid.config as config
from sciolyid.data import database, logger
from sciolyid.functions import CustomCooldown, send_leaderboard


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # bot info command - gives info on bot
    @commands.command(
        help="- Gives info on bot, support server invite, stats",
        aliases=["bot_info", "support"],
    )
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.channel))
    async def botinfo(self, ctx):
        logger.info("command: botinfo")

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name="Bot Info",
            value=f"This bot was created by {config.options['authors']}"
            + f" for helping people practice {config.options['id_type'][:-1]} identification for Science Olympiad.\n"
            + f"The bot's source can be found here: {config.options['source_link']}",
            inline=False,
        )
        embed.add_field(
            name="Support",
            value="If you are experiencing any issues, have feature requests, "
            + "or want to get updates on bot status, join our support server below.",
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=f"This bot is in {len(self.bot.guilds)} servers. "
            + f"The WebSocket latency is {round(self.bot.latency*1000)} ms.",
            inline=False,
        )
        await ctx.send(embed=embed)
        await ctx.send(config.options["support_server"])

    # ping command - gives bot latency
    @commands.command(help="- Pings the bot and displays latency",)
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    async def ping(self, ctx):
        logger.info("command: ping")
        lat = round(self.bot.latency * 1000)
        logger.info(f"latency: {lat}")
        await ctx.send(f"**Pong!** The WebSocket latency is `{lat}` ms.")

    # invite command - sends invite link
    @commands.command(help="- Get the invite link for this bot")
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.channel))
    async def invite(self, ctx):
        logger.info("command: invite")

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name="Invite",
            value=f"To invite this bot to your own server, use the following invite links.\n {config.options['invite']}",
            inline=False,
        )
        await ctx.send(embed=embed)
        await ctx.send(config.options["support_server"])

    # ignore command - ignores a given channel
    @commands.command(
        brief="- Ignore all commands in a channel",
        help="- Ignore all commands in a channel. The 'manage guild' permission is needed to use this command.",
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def ignore(self, ctx, channels: commands.Greedy[discord.TextChannel] = None):
        logger.info("command: invite")

        if channels is None:
            logger.info("defaulting to current")
            await ctx.send(
                "**No valid channels were found.**\n*Defaulting to current channel...*"
            )
            channels = [ctx.channel]

        logger.info(f"ignored channels: {[c.name for c in channels]}")
        added = ""
        removed = ""
        for channel in channels:
            if database.zscore("ignore:global", str(channel.id)) is None:
                added += f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                database.zadd("ignore:global", {str(channel.id): ctx.guild.id})
            else:
                removed += f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                database.zrem("ignore:global", str(channel.id))

        ignored = "".join(
            [
                f"`#{esc(channel.name)}` (`{esc(channel.category.name) if channel.category else 'No Category'}`)\n"
                for channel in map(
                    lambda c: ctx.guild.get_channel(int(c)),
                    database.zrangebyscore(
                        "ignore:global", ctx.guild.id - 0.1, ctx.guild.id + 0.1
                    ),
                )
            ]
        )

        await ctx.send(
            (f"**Ignoring:**\n{added}" if added else "")
            + (f"**Stopped ignoring:**\n{removed}" if removed else "")
            + (f"**Ignored Channels:**\n{ignored}" if ignored else "")
        )

    # leave command - removes itself from guild
    @commands.command(
        brief="- Remove the bot from the guild",
        help="- Remove the bot from the guild. The 'manage guild' permission is needed to use this command.",
        aliases=["kick"],
    )
    @commands.check(CustomCooldown(2.0, bucket=commands.BucketType.channel))
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def leave(self, ctx, confirm: typing.Optional[bool] = False):
        logger.info("command: leave")

        if database.exists(f"leave:{ctx.guild.id}"):
            logger.info("confirming")
            if confirm:
                logger.info(f"confirmed. Leaving {ctx.guild}")
                database.delete(f"leave:{ctx.guild.id}")
                await ctx.send("**Ok, bye!**")
                await ctx.guild.leave()
                return
            logger.info("confirm failed. leave canceled")
            database.delete(f"leave:{ctx.guild.id}")
            await ctx.send("**Leave canceled.**")
            return

        logger.info("not confirmed")
        database.set(f"leave:{ctx.guild.id}", 0, ex=60)
        await ctx.send(
            "**Are you sure you want to remove me from the guild?**\n"
            + f"Use `{config.options['prefixes'][0]}leave yes` to confirm, `{config.options['prefixes'][0]}leave no` to cancel. "
            + "You have 60 seconds to confirm before it will automatically cancel."
        )

    # ban command - prevents certain users from using the bot
    @commands.command(help="- ban command", hidden=True)
    @commands.is_owner()
    async def ban(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: ban")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zadd("banned:global", {str(user.id): 0})
        await ctx.send(f"Ok, {esc(user.name)} cannot use the bot anymore!")

    # unban command - prevents certain users from using the bot
    @commands.command(help="- unban command", hidden=True)
    @commands.is_owner()
    async def unban(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: unban")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zrem("banned:global", str(user.id))
        await ctx.send(f"Ok, {esc(user.name)} can use the bot!")

    # correct command - see how many times someone got a specimen correct
    @commands.command(help=f"- see answered {config.options['id_type']} command", hidden=True)
    @commands.is_owner()
    async def correct(
        self,
        ctx,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None,
    ):
        logger.info("command: correct")
        if user is None:
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        await send_leaderboard(
            ctx,
            f"Top Correct {config.options['id_type'].capitalize()} ({esc(user.name)})",
            1,
            database_key=f"correct.user:{user.id}",
            items_per_page=25,
        )


def setup(bot):
    bot.add_cog(Meta(bot))
