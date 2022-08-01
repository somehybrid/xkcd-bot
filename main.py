from client import Client
from discord import app_commands
import discord
import aioredis
import scraper
import difflib
import random
import json
import time

redis = aioredis.from_url("redis://localhost")
intents = discord.Intents.default()
client = Client(intents=intents)
run = False


async def sync():
    global run
    if not run:
        await client.tree.sync()
        run = True


@client.event
async def on_ready():
    await client.change_presence(
         activity=discord.Activity(type=discord.ActivityType.watching, name="xkcd comics")
    )
    print("Logged in as")
    print(client.user.name)
    print("------")
    await scraper.xkcd_scraper(redis)
    print(len(client.guilds))


@client.tree.command(name="xkcd", description="Get an xkcd comic")
@app_commands.describe(inp="The comic's number or title")
async def main(interaction: discord.Interaction, inp: str = None):
    await interaction.response.defer(ephemeral=False, thinking=True)
    if inp is None:
        i = random.randint(1, int(await redis.get("current")))
        while i == 404:
            i = random.randint(1, int(await redis.get("current")))
        item = json.loads(await redis.get(i))
        embed = discord.Embed(title=item["title"], url=item["img"], description=item["alt"])
        embed.set_image(url=item["img"])
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        if await redis.get(int(inp)) is None:
            embed = discord.Embed(title="Error", description="Comic not found", color=0xFF0000)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        item = json.loads(await redis.get(int(inp)))
    except ValueError:
        item = await redis.get(inp.lower())
        if item is None:
            curmax = ["", 0]
            keys = await redis.keys()
            for key in keys:
                ratio = difflib.SequenceMatcher(a=key.decode('utf-8'), b=inp.lower()).ratio()
                if ratio > 0.75:
                    if ratio > curmax[1]:
                        curmax = [key, ratio]
            if curmax[1] == 0:
                embed = discord.Embed(title="Error", description="Comic not found", color=0xFF0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            else:
                item = json.loads(await redis.get(curmax[0]))
        else:
            item = json.loads(item)

    embed = discord.Embed(title=item["title"], url=item["img"], description=item["alt"],
                          colour=discord.Colour.from_rgb(150, 168, 200))
    embed.set_image(url=item["img"])
    await interaction.followup.send(embed=embed, ephemeral=True)


@client.tree.command()
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    t1 = time.perf_counter()
    t = await interaction.followup.send(content="Pinging...", ephemeral=True)
    t2 = time.perf_counter()
    await t.edit(content=f"Pong! {round(t2 - t1, 2)}ms latency")

<<<<<<< HEAD
client.run("MTAwMjg5NDA4MjAwNTI5MTA3MA.GRUUel.CfePl65PXEJ2IKKuphLs12H9cMrksQyZWInIXY")
=======
client.run("token")
>>>>>>> 53a2e44610a928f858319ffb1ccb815884c4fc4d
