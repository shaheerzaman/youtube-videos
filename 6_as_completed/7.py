import time
import random
import asyncio
import aiohttp
from collections import namedtuple
from concurrent.futures import FIRST_COMPLETED

Service = namedtuple("Service", ("name", "url", "ip_attr"))

SERVICES = (
    Service("ipify", "https://api.ipify.org?format=json", "ip"),
    Service("ip-api", "http://ip-api.com/json", "query"),
)

DEFAULT_TIMEOUT = 0.01


async def aiohttp_get_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def fetch_ip(service):
    start = time.time()
    print("Fetching IP from {}".format(service.name))

    await asyncio.sleep(random.randint(1, 3) * 0.1)
    try:
        json_response = await aiohttp_get_json(service.url)
    except Exception:
        return f"{service.name} is unresponsive"

    ip = json_response[service.ip_attr]

    print(
        f"{service.name} finished with result: {ip}, took: {time.time() - start:.2f} seconds"
    )
    return ip


async def main():
    timeout = 5  # seconds
    response = {"message": "Result from asynchronous.", "ip": "not available"}

    tasks = [asyncio.create_task(fetch_ip(service)) for service in SERVICES]
    done, pending = await asyncio.wait(
        tasks, timeout=timeout, return_when=FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()

    for task in done:
        response["ip"] = task.result()

    print(response)


asyncio.run(main())
