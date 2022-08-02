"""
A discord bot used to get xkcd comics
"""
import pathlib
import difflib
import random
import json
import time
from discord import app_commands
import discord
import aioredis
from client import Client
import scraper

redis = aioredis.from_url("redis://localhost")
intents = discord.Intents.default()
client = Client(intents=intents)

path = pathlib.Path(__file__).parent.absolute()
with open(path / "token.txt", encoding="utf-8") as f:
    token = f.read()


@client.event
async def on_ready():
    """
    Called when the bot is ready
    """
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="xkcd comics"
        )
    )
    print("Logged in as")
    print(client.user.name)
    print("------")
    await scraper.xkcd_scraper(redis)
    print(len(client.guilds))


@client.tree.command(name="xkcd", description="Get an xkcd comic")
@app_commands.describe(inp="The comic's number or title")
async def main(interaction: discord.Interaction, inp: str = None):
    """
    The main command used to get xkdc comics
    """
    await interaction.response.defer(ephemeral=False, thinking=True)
    if inp is None:
        i = random.randint(1, int(await redis.get("current")))
        while i == 404:
            i = random.randint(1, int(await redis.get("current")))
        item = json.loads(await redis.get(i))
        embed = discord.Embed(
            title=item["title"], url=item["img"], description=item["alt"]
        )
        embed.set_image(url=item["img"])
        await interaction.followup.send(embed=embed, ephemeral=False)
        return

    try:
        if await redis.get(int(inp)) is None:
            embed = discord.Embed(
                title="Error", description="Comic not found", color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
            return
        item = json.loads(await redis.get(int(inp)))
    except ValueError:
        item = await redis.get(inp.lower())
        if item is None:
            curmax = ["", 0]
            keys = await redis.keys()
            for key in keys:
                ratio = difflib.SequenceMatcher(
                    a=key.decode("utf-8"), b=inp.lower()
                ).ratio()
                if ratio > 0.75:
                    if ratio > curmax[1]:
                        curmax = [key, ratio]
            if curmax[1] == 0:
                embed = discord.Embed(
                    title="Error", description="Comic not found", color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=False)
                return
            item = json.loads(await redis.get(curmax[0]))
        else:
            item = json.loads(item)

    embed = discord.Embed(
        title=item["title"],
        url=item["img"],
        description=item["alt"],
        colour=discord.Colour.from_rgb(150, 168, 200),
    )
    embed.set_image(url=item["img"])
    await interaction.followup.send(embed=embed, ephemeral=False)


@client.tree.command()
async def ping(interaction: discord.Interaction):
    """
    Returns the latency of the bot
    """
    await interaction.response.defer(ephemeral=False, thinking=True)
    time_1 = time.perf_counter()
    message = await interaction.followup.send(content="Pinging...", ephemeral=False)
    time_2 = time.perf_counter()
    await message.edit(content=f"Pong! {round(time_2 - time_1, 2)}ms latency")


client.run(token)
