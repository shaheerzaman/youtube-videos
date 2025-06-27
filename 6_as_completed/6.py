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
    print(f"Fetching IP from {service.name}")

    try:
        json_response = await aiohttp_get_json(service.url)
    except Exception:
        print(f"{service.name} is unresponsive".format(service.name))
    else:
        ip = json_response[service.ip_attr]

        print(
            f"{service.name} finished with result: {ip}, took: {time.time() - start:.2f} seconds"
        )


async def main():
    tasks = [asyncio.create_task(fetch_ip(service)) for service in SERVICES]
    await asyncio.wait(tasks)  # intentionally ignore results


asyncio.run(main())
