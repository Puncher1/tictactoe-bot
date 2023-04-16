from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

from .common import GuildID

if TYPE_CHECKING:
    from bot import TicTacToeBot

DEV_TEST_GUILD_ID = GuildID.dev_test


class TicTacToe(commands.Cog):
    """Play Tic-Tac-Toe against me or another player"""

    def __init__(self, bot: TicTacToeBot):
        self.bot: TicTacToeBot = bot

    @app_commands.command(name="tictactoe", description="Play Tic-Tac-Toe against me or another player")
    @app_commands.describe(player="The player to play against.")
    @app_commands.guilds(DEV_TEST_GUILD_ID)
    async def _tictactoe(self, interaction: discord.Interaction, player: Optional[discord.Member]):
        await interaction.response.send_message("Nice")


async def setup(bot: TicTacToeBot):
    await bot.add_cog(TicTacToe(bot))
