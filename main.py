from discord import app_commands
import discord
import aioredis
import aiohttp
import asyncio
import random
import client
import tqdm
import json
import time

redis = aioredis.from_url("redis://localhost")
intents = discord.Intents.default()
client = client.Client(intents=intents)
run = False


async def cscrape(session, i):
    async with session.get(f"https://xkcd.com/{i}/info.0.json") as response:
        item = await response.json()
        await redis.set(item["title"].lower(), json.dumps({"img": item["img"], "alt": item["alt"],
                                                           "title": item["title"]}))
        await redis.set(item["num"], json.dumps({"img": item["img"], "alt": item["alt"], "title": item["title"]}))

async def xkcd_scraper():
    tasks = []
    if not await redis.exists("standards"):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://xkcd.com/info.0.json") as response:
                item = await response.json()
                await redis.set("current", item["num"])
                current = int(await redis.get("current"))
            for i in tqdm.tqdm(range(1, current), desc="Adding tasks"):
                if i != 404:
                    tasks.append(cscrape(session, i))
            await asyncio.gather(*tasks)
            print("saving to database")
            await redis.save()
            print("finished scraping")


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
    await xkcd_scraper()
    await sync()

@client.tree.command()
@app_commands.describe(inp="The comic's number or title")
async def xkcd(interaction: discord.Interaction, inp: str = None):
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
        item = json.loads(await redis.get(inp.lower()))

    if item is None:
        embed = discord.Embed(title="Error", description="Comic not found", color=0xFF0000)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
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

client.run("token")
