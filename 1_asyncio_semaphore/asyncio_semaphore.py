import asyncio
import aiohttp
import time


async def fetch_url(url, semaphore, session):
    """Fetches data from a URL, respecting the semaphore limit."""
    async with semaphore:
        print(f"[{asyncio.current_task().get_name()}] Acquiring semaphore for {url}...")

        try:
            print(f"[{asyncio.current_task().get_name()}] Fetching {url}...")

            async with session.get(url) as response:
                await asyncio.sleep(0.1)
                status = response.status
                print(
                    f"[{asyncio.current_task().get_name()}] Finished fetching {url} with status {status}"
                )
                return url, status
        except aiohttp.ClientError as e:
            print(f"[{asyncio.current_task().get_name()}] Error fetching {url}: {e}")
            return url, None
        finally:
            pass


async def main(urls, max_concurrent_requests):
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    print(f"Created semaphore with limit: {max_concurrent_requests}")

    async with aiohttp.ClientSession() as session:
        fetch_tasks = []
        for i, url in enumerate(urls):
            task = asyncio.create_task(
                fetch_url(url, semaphore, session), name=f"Task-{i}"
            )
            fetch_tasks.append(task)

        results = await asyncio.gather(*fetch_tasks)

        print("--- Results ---")
        for url, status in results:
            print(f"URL: {url}, Status: {status}")


if __name__ == "__main__":
    example_urls = [
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
        "https://www.google.com/",
    ]

    max_concurrent = 3

    print("Starting asynchronous fetching with semaphore...")
    start_time = time.time()
    asyncio.run(main(example_urls, max_concurrent))
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
