"""
This module defines a subclass of discord.Client which has a tree attribute and
syncs the tree on start.
"""
from discord import app_commands
import discord


class Client(discord.Client):
    """
    A subclass of discord.Client which has a tree attribute and syncs the tree on start.
    """
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
