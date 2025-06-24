"""
An example of periodically scheduling coroutines

"""

import asyncio
from datetime import datetime
from random import randint
import aiohttp
import logging


LOGGER_FORMAT = "%(asctime)s %(message)s"
URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{}.json"
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
FETCH_TIMEOUT = 10
MAXIMUM_FETCHES = 5

logging.basicConfig(format=LOGGER_FORMAT, datefmt="[%H:%M:%S]")
log = logging.getLogger()
log.setLevel(logging.INFO)


class BoomException(Exception):
    pass


class URLFetcher:
    """Provides counting of URL fetches for a particular task."""

    def __init__(self) -> None:
        self.fetch_counter = 0

    async def fetch(self, session: aiohttp.ClientSession, url: str):
        """Fetch a URL using aiohttp returning parsed JSON response.

        As suggested by the aiohttp docs we reuse the session.

        """
        self.fetch_counter += 1
        async with session.get(url, timeout=FETCH_TIMEOUT) as response:
            if self.fetch_counter > MAXIMUM_FETCHES:
                raise BoomException("BOOM!")
            elif randint(0, 3) == 0:
                raise Exception("Random generic exception")

            return await response.json()


async def post_number_of_comments(
    session: aiohttp.ClientSession, fetcher: URLFetcher, post_id: int
) -> int:
    """Retrieve data for current post and recursively for all comments."""
    url = URL_TEMPLATE.format(post_id)
    response = await fetcher.fetch(session, url)

    # base case, there are no comments
    if response is None or "kids" not in response:
        return 0

    # calculate this post's comments as number of comments
    number_of_comments = len(response["kids"])

    # create recursive tasks for all comments
    tasks = [
        post_number_of_comments(session, fetcher, kid_id) for kid_id in response["kids"]
    ]

    # schedule the tasks and retrieve results
    results = await asyncio.gather(*tasks)

    # reduce the descendents comments and add it to this post's
    number_of_comments += sum(results)
    log.debug("{:^6} > {} comments".format(post_id, number_of_comments))

    return number_of_comments


async def get_comments_of_top_stories(
    session: aiohttp.ClientSession, limit: int, iteration: int
) -> int:
    """Retrieve top stories in HN."""

    fetcher = URLFetcher()  # create a new fetcher for this task
    response = await fetcher.fetch(session, TOP_STORIES_URL)
    tasks = [
        post_number_of_comments(session, fetcher, post_id)
        for post_id in response[:limit]
    ]
    results = await asyncio.gather(*tasks)
    for post_id, num_comments in zip(response[:limit], results):
        log.info(
            "Post {} has {} comments ({})".format(post_id, num_comments, iteration)
        )

    return fetcher.fetch_counter  # return the fetch count


async def poll_top_stories_for_comments(
    session: aiohttp.ClientSession, period: int, limit: int
) -> None:
    """Periodically poll for new stories and retrieve number of comments."""

    iteration = 1
    while True:
        log.info(
            "Calculating comments for top {} stories. ({})".format(limit, iteration)
        )

        task = asyncio.create_task(
            get_comments_of_top_stories(session, limit, iteration)
        )

        now = datetime.now()

        def callback(fut):
            fetch_count = fut.result()
            log.info(
                "> Calculating comments took {:.2f} seconds and {} fetches".format(
                    (datetime.now() - now).total_seconds(), fetch_count
                )
            )

        task.add_done_callback(callback)

        log.info("Waiting for {} seconds...".format(period))
        iteration += 1
        await asyncio.sleep(period)


async def main(period: int, limit: int) -> None:
    async with aiohttp.ClientSession() as session:
        await poll_top_stories_for_comments(session, period, limit)


if __name__ == "__main__":
    asyncio.run(main(period=5, limit=5))
