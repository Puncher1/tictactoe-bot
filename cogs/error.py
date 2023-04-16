from __future__ import annotations

import os
import traceback
import sys
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands
from discord.ext.commands import errors

from .common import Color
from utils.dt import Datetime
from utils.debug import log, LogLevel

if TYPE_CHECKING:
    from bot import TicTacToeBot
    from utils.types import Context


ERROR_LOG_CHANNEL_ID = 1097267327751442542


def get_full_traceback(error: Any, /) -> str:
    """Returns the full traceback."""

    etype = type(error)
    trace = error.__traceback__

    lines = traceback.format_exception(etype, error, trace)
    full_traceback_text = ''.join(lines)

    return full_traceback_text


class ErrorHandler(commands.Cog):
    """Handles command errors globally."""

    def __init__(self, bot: TicTacToeBot):
        self.bot: TicTacToeBot = bot

    def create_error_embed(self, content: str, *, ctx: Context, try_again: bool = True, usage: bool = True) -> discord.Embed:
        content += "\nPlease try again." if try_again else ""

        if usage:
            signature = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}"
            content += f"\n\n**Usage:**\n`{signature}`"

        embed = discord.Embed(color=Color.error, description=content)
        embed.set_author(name="Error")

        return embed

    def create_log_file(self, error: commands.CommandError, /) -> discord.File:
        dt = Datetime.get_local_datetime()
        dt_fm = dt.strftime("%y%m%d_%H%M%S")

        filename = f"error_{dt_fm}.txt"
        filepath = f"./temp/{filename}"
        with open(filepath, "w+", encoding="utf-8") as file:
            file.write(get_full_traceback(error))

        error_file = discord.File(filepath, filename=filename)
        return error_file

    async def send_to_log(self, description: str, error_file: discord.File, /):
        error_log_channel: discord.TextChannel = self.bot.get_channel(ERROR_LOG_CHANNEL_ID)  # type: ignore
        await error_log_channel.send(content=description, file=error_file)

        os.remove(error_file.fp.name)  # type: ignore

    async def process_ctx_error(self, *, error: Any, ctx: Context):
        error_file = self.create_log_file(error)
        description = (
            f"**Guild:** `{ctx.guild.name}` | `{ctx.guild.id}` \n"  # type: ignore
            f"**Short Traceback** \n"
            f"```{error.__class__.__name__}: {error}``` \n"
            f"**Full Traceback**"
        )
        await self.send_to_log(description, error_file)

        content = "**An unexpected error has occurred!**\nThe full traceback has been sent to the owner."
        embed = self.create_error_embed(content, ctx=ctx, try_again=False, usage=False)

        await ctx.send(embed=embed)

    async def process_event_error(self, *, error: Any, event: str):
        error_file = self.create_log_file(error)
        description = (
            f"**Event:** `{event}` \n"
            f"**Short Traceback** \n"
            f"```{error.__class__.__name__}: {error}``` \n"
            f"**Full Traceback**"
        )
        await self.send_to_log(description, error_file)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        log_error = False
        if isinstance(error, errors.CommandNotFound):
            return

        elif isinstance(error, errors.MissingRequiredArgument):
            content = "**A required argument is missing!**"
            embed = self.create_error_embed(content, ctx=ctx)
            await ctx.send(embed=embed)

        elif isinstance(error, errors.BadArgument):
            content = "**Invalid argument given!**"
            embed = self.create_error_embed(content, ctx=ctx)
            await ctx.send(embed=embed)

        elif isinstance(error, errors.CheckFailure):
            if ctx.cog.qualified_name == "Admin":  # type: ignore
                return
            log_error = True

        else:
            log_error = True

        if log_error:
            await self.process_ctx_error(error=error, ctx=ctx)
            log(f"{error.__class__.__name__}: {error}", level=LogLevel.error, context=f"command:{ctx.command.name}")

    async def on_error(self, event: str):
        error = sys.exc_info()[1]
        await self.process_event_error(error=error, event=event)
        log(f"{error.__class__.__name__}: {error}", level=LogLevel.error, context=f"event:{event}")


async def setup(bot: TicTacToeBot):
    await bot.add_cog(ErrorHandler(bot))
