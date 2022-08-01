import asyncio
import aiohttp
import json


async def cscrape(session, i, redis):
    async with session.get(f"https://xkcd.com/{i}/info.0.json") as response:
        item = await response.json()
        await redis.set(item["title"].lower(), json.dumps({"img": item["img"], "alt": item["alt"],
                                                           "title": item["title"]}))
        await redis.set(item["num"], json.dumps({"img": item["img"], "alt": item["alt"], "title": item["title"]}))

async def xkcd_scraper(redis):
    tasks = []
    if not await redis.exists("standards"):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://xkcd.com/info.0.json") as response:
                item = await response.json()
                await redis.set("current", item["num"])
                current = int(await redis.get("current"))
            for i in range(1, current):
                if i != 404:
                    tasks.append(cscrape(session, i, redis))
            await asyncio.gather(*tasks)
            print("saving to database")
            await redis.save()
            print("finished scraping")
