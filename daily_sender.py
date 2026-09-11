import asyncio
import datetime
from zoneinfo import ZoneInfo
from get_current_info import _daily_update
import aiohttp
from discord import Webhook

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
    log(result, "debug")
    with open('/mount/results.txt', 'w', encoding='utf-8') as file:
        file.write(str(result))
    if send_to_discord:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url('https://discord.com/api/webhooks/1287802925971673169/mz6yehCyxWob4FXkVmoKUjY9PiSSxaDPegcCVo3m7bp4BbXaxKjjHRv8KBC-ACzAd6Mp', session=session)
            await webhook.send("update", username="user_name", avatar_url="https://www.goethe.flensburg.de/files/logo/logo196.png")

async def get_sleep_time(Abend):
    now = berlin_now()
    if Abend:
        target_time = now.replace(hour=18, minute=30, second=00, microsecond=0)
    else:
        target_time = now.replace(hour=6, minute=30, second=0, microsecond=0)
    if now > target_time:
        target_time += datetime.timedelta(days=1)
    wait_time = (target_time - now).total_seconds()
    return wait_time

async def schedule_daily_task():
    now = berlin_now()
    await log("Updating File on Startup: " + str(now.date()) + " | " + now.strftime("%A") + " at " + now.strftime("%H:%M:%S"))
    result = await _daily_update()
    result.append([None,'','','','','','','']) #False = Abend
    await send_update(result, send_to_discord = False)
    await log("Done! ✅")
    current_time = now.time()
    if datetime.time(6, 30) <= current_time < datetime.time(18, 30):
        await log("start on Abend")
        currentPlace = 0
    else:
        await log("start on Morgen")
        currentPlace = 1
    while True:
        if currentPlace == 0:
            await asyncio.sleep(await get_sleep_time(True))
            now = berlin_now()
            if now.strftime("%A") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Sunday"]:
                await log("Abends: " + str(now.date()) + " | " + now.strftime("%A"))
                result = await _daily_update()
                result.append([False,'','','','','','','']) #False = Abend
                await send_update(result)
            currentPlace = 1
        if currentPlace == 1:
            await asyncio.sleep(await get_sleep_time(False))
            now = berlin_now()
            if now.strftime("%A") in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                await log("Morgens: " + str(now.date()) + " | " + now.strftime("%A"))
                result = await _daily_update()
                result.append([True,'','','','','','','']) #True = Morgen
                await send_update(result)
            currentPlace = 0


if __name__ == "__main__":
    asyncio.run(schedule_daily_task())