from collections import namedtuple
import time
import asyncio
import aiohttp

Service = namedtuple("Service", ("name", "url", "ip_attr"))

SERVICES = (
    Service("ipify", "https://api.ipify.org?format=json", "ip"),
    Service("ip-api", "http://ip-api.com/json", "this-is-not-an-attr"),
    Service("borken", "http://no-way-this-is-going-to-work.com/json", "ip"),
)


async def aiohttp_get_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def fetch_ip(service):
    start = time.time()
    print("Fetching IP from {}".format(service.name))

    try:
        json_response = await aiohttp_get_json(service.url)
    except Exception:
        return "{} is unresponsive".format(service.name)

    ip = json_response[service.ip_attr]

    return f"{service.name} finished with result: {ip}, took: {time.time() - start:.2f} seconds"


async def main():
    tasks = [asyncio.create_task(fetch_ip(service)) for service in SERVICES]
    done, _ = await asyncio.wait(tasks)

    for task in done:
        try:
            print(task.result())
        except Exception as e:
            print(f"Unexpected error: {e}")


asyncio.run(main())
