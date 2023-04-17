from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union, Literal
from enum import Enum

import discord
from discord.ext import commands
from discord.ext.commands import errors

from .common import Color, Emoji
from .common import GuildID

if TYPE_CHECKING:
    from bot import TicTacToeBot
    from utils.types import Context

DEV_TEST_GUILD_ID = GuildID.dev_test


class _ExtensionState(Enum):
    loaded = 0
    unloaded = 1
    reloaded = 2


class Admin(commands.Cog):
    """Admin-only commands which only can be used by the owner."""

    def __init__(self, bot: TicTacToeBot):
        self.bot: TicTacToeBot = bot

    async def cog_check(self, ctx: Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.command(aliases=["l"])
    async def load(self, ctx: Context, *, extension: str):
        if not extension.startswith("cogs."):
            extension = f"cogs.{extension}"

        try:
            await self.bot.load_extension(extension)
        except Exception as e:
            content = f"**Failed loading `{extension}`!**\n```{e.__class__.__name__}: {e}```"
        else:
            content = f"**Successfully loaded `{extension}`!**"

        await ctx.reply(content, mention_author=False)

    @commands.command()
    async def unload(self, ctx: Context, *, extension: str):
        if not extension.startswith("cogs."):
            extension = f"cogs.{extension}"

        try:
            await self.bot.unload_extension(extension)
        except Exception as e:
            content = f"**Failed unloading `{extension}`!**\n```{e.__class__.__name__}: {e}```"
        else:
            content = f"**Successfully unloaded `{extension}`!**"

        await ctx.reply(content, mention_author=False)

    @commands.group(name="reload", aliases=["r"], invoke_without_command=True)
    async def _reload(self, ctx: Context, *, extension: str):
        if not extension.startswith("cogs."):
            extension = f"cogs.{extension}"

        try:
            await self.bot.reload_extension(extension)
        except Exception as e:
            content = f"**Failed reloading `{extension}`!**\n```{e.__class__.__name__}: {e}```"
        else:
            content = f"**Successfully reloaded `{extension}`!**"

        await ctx.reply(content, mention_author=False)

    async def reload_or_load_extension(self, extension: str) -> _ExtensionState:
        try:
            await self.bot.load_extension(extension)
            ext_state = _ExtensionState.loaded
        except errors.ExtensionAlreadyLoaded:
            await self.bot.reload_extension(extension)
            ext_state = _ExtensionState.reloaded

        return ext_state

    def create_cogs_embed(
        self,
        *,
        loaded: List[str],
        unloaded: List[str],
        reloaded: Optional[List[str]] = None,
        failed: Optional[List[str]] = None,
    ) -> discord.Embed:

        if reloaded is None:
            reloaded = []

        if failed is None:
            failed = []

        loaded_content = "\n".join(loaded)
        unloaded_content = "\n".join(unloaded)
        reloaded_content = "\n".join(reloaded)
        failed_content = "\n".join(failed)

        if len(loaded) > 0:
            loaded_content = f"{Emoji.arrow_up} **Loaded - [{len(loaded)}]**\n{loaded_content}\n\n"

        if len(unloaded) > 0:
            unloaded_content = f"{Emoji.arrow_down} **Unloaded - [{len(unloaded)}]**\n{unloaded_content}\n\n"

        if len(reloaded) > 0:
            reloaded_content = f"{Emoji.arrows_counterclockwise} **Reloaded - [{len(reloaded)}]**\n{reloaded_content}\n\n"

        if len(failed) > 0:
            failed_content = f"{Emoji.x} **Failed - [{len(failed)}]**\n{failed_content}"

        description = f"{loaded_content}{unloaded_content}{reloaded_content}{failed_content}"
        embed = discord.Embed(color=Color.info, description=description)

        return embed

    @_reload.command(name="all")
    async def _reload_all(self, ctx: Context):
        available_extensions = self.bot.get_allowed_extensions()

        loaded = []
        unloaded = []
        reloaded = []
        failed = []

        future_unload = [ext for ext in self.bot.extensions if ext not in available_extensions]
        for extension in future_unload:
            try:
                await self.bot.unload_extension(extension)
                unloaded.append(f"`{extension}`")
            except Exception as e:
                failed.append(f"`{extension}`: `{e.__class__.__name__}`")

        for extension in available_extensions:
            try:
                ext_state = await self.reload_or_load_extension(extension)
            except Exception as e:
                failed.append(f"`{extension}`: `{e.__class__.__name__}`")
            else:
                ext_str = f"`{extension}`"
                if ext_state == _ExtensionState.loaded:
                    loaded.append(ext_str)
                elif ext_state == _ExtensionState.reloaded:
                    reloaded.append(ext_str)

        embed = self.create_cogs_embed(loaded=loaded, unloaded=unloaded, reloaded=reloaded, failed=failed)
        embed.title = "Cogs Update"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.group(name="cogs")
    async def _cogs(self, ctx: Context):
        pass

    @_cogs.command(name="list")
    async def _cogs_list(self, ctx: Context):
        all_extensions = self.bot.get_all_extensions()
        unloaded = [f"`{ext}`" for ext in all_extensions if ext not in self.bot.extensions]
        loaded = [f"`{ext}`" for ext in self.bot.extensions]

        embed = self.create_cogs_embed(loaded=loaded, unloaded=unloaded)
        embed.title = "Cogs List"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    async def sync(self, ctx: Context, option: Optional[Union[Literal["all"], int]] = None):
        valid_str_options = ("all",)
        if option is None:
            guild = self.bot.get_guild(DEV_TEST_GUILD_ID)
            await self.bot.tree.sync(guild=guild)
            await ctx.reply(f"Done! Synced all guild commands in `{guild.name}`!", mention_author=False)  # type: ignore

        elif isinstance(option, int):
            guild = self.bot.get_guild(option)
            if guild is None:
                return await ctx.reply(f"{Emoji.x} Invalid guild given!")

            await self.bot.tree.sync(guild=guild)
            await ctx.reply(f"Done! Synced all guild commands in `{guild.name}`!", mention_author=False)  # type: ignore

        else:
            if option not in valid_str_options:
                raise errors.BadArgument

            if option == "all":
                for guild in self.bot.guilds:
                    await self.bot.tree.sync(guild=guild)

                await ctx.reply("Done! Synced all local guild commands!", mention_author=False)

    @commands.command(aliases=["s"])
    async def shutdown(self, ctx: Context):
        """Shuts down the bot."""
        await ctx.message.add_reaction(Emoji.white_check_mark)
        await self.bot.close()


async def setup(bot: TicTacToeBot):
    await bot.add_cog(Admin(bot))
