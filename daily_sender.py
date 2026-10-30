import asyncio
import datetime
from zoneinfo import ZoneInfo
from get_current_info import _daily_update
import aiohttp
from discord import Webhook
import json

try:
    config = json.load(open('./config.json'))
except FileNotFoundError:
    print("config.json not found. Please create the file with the necessary configuration.")
    exit(1)

TIMEZONE = 'Europe/Berlin'
BERLIN_TZ = ZoneInfo(TIMEZONE)


def berlin_now():
    return datetime.datetime.now(BERLIN_TZ)


async def log(message, mode="info"):
    if not mode == "debug":
        with open('./logs/daily_sender.log', 'a') as file:
            file.write(message + '\n')
            file.close()
    print(message)

async def send_update(result, send_to_discord = True):
    #await log(result, "debug")
    with open('/mount/results.txt', 'w', encoding='utf-8') as file:
        file.write(str(result))
    if send_to_discord:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(config['WEBHOOK_URL'], session=session)
            await webhook.send("update", username="user_name", avatar_url=config['LOGO_URL'])

async def get_sleep_time(TimeOfDay):
    now = berlin_now()
    if TimeOfDay == 0:
        target_time = now.replace(hour=18, minute=30, second=00, microsecond=0)
    elif TimeOfDay == 1:
        target_time = now.replace(hour=6, minute=30, second=0, microsecond=0)
    if now > target_time:
        target_time += datetime.timedelta(days=1)
    wait_time = (target_time - now).total_seconds()
    return wait_time

async def schedule_daily_task():
    now = berlin_now()
    await log("Updating File on Startup: " + str(now.date()) + " | " + now.strftime("%A") + " at " + now.strftime("%H:%M:%S"))
    result = await _daily_update(vertretungsplan_URL=config['VERTRETUNGSPLAN_URL'])
    result.append([None,'','','','','','','']) #1 = Abend
    await send_update(result, send_to_discord = False)
    await log("Done! ✅")
    current_time = berlin_now()
    currentPlace = None
    if current_time.replace(hour=6, minute=30, second=0, microsecond=0) <= current_time < current_time.replace(hour=18, minute=30, second=0, microsecond=0):
        await log("start on Abend")
        currentPlace = 0
    elif current_time >= current_time.replace(hour=18, minute=30, second=0, microsecond=0) or current_time < current_time.replace(hour=6, minute=30, second=0, microsecond=0):
        await log("start on Morgens-1")
        currentPlace = 1
    while True:
        if currentPlace == 0:
            await asyncio.sleep(await get_sleep_time(0))
            now = berlin_now()
            if now.strftime("%A") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Sunday"]:
                await log("Abends: " + str(now.date()) + " | " + now.strftime("%A"))
                result = await _daily_update(vertretungsplan_URL=config['VERTRETUNGSPLAN_URL'])
                result.append([0,'','','','','','','']) #0 = Abend
                await send_update(result)
            currentPlace = 1
        if currentPlace == 1:
            await asyncio.sleep(await get_sleep_time(1))
            now = berlin_now()
            if now.strftime("%A") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                await log("Morgens-1: " + str(now.date()) + " | " + now.strftime("%A"))
                result = await _daily_update(vertretungsplan_URL=config['VERTRETUNGSPLAN_URL'])
                result.append([1,'','','','','','','']) #1 = Morgen
                await send_update(result)
            currentPlace = 0
            while current_time < current_time.replace(hour=7, minute=43, second=0, microsecond=0):
                await asyncio.sleep(120) #2 min.
                now = berlin_now()
                if now.strftime("%A") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                    await log("Morgens-2: " + str(now.date()) + " | " + now.strftime("%A"))
                    result = await _daily_update(vertretungsplan_URL=config['VERTRETUNGSPLAN_URL'])
                    result.append([2,'','','','','','','']) #2 = Morgen with update
                    await send_update(result)


if __name__ == "__main__":
    asyncio.run(schedule_daily_task())