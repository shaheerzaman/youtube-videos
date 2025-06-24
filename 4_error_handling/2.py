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
MAXIMUM_FETCHES = 500

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
            elif randint(0, 50) == 10:
                raise Exception("Random generic exception")
            return await response.json()


async def post_number_of_comments(
    session: aiohttp.ClientSession, fetcher: URLFetcher, post_id: int
) -> int:
    """Retrieve data for current post and recursively for all comments."""
    url = URL_TEMPLATE.format(post_id)
    try:
        response = await fetcher.fetch(session, url)
    except (BoomException, Exception) as e:
        log.error("Error retrieving post : {}".format(post_id))
        log.error(f"Exception: {e}")
        raise e

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
    try:
        results = await asyncio.gather(*tasks)
    except (BoomException, Exception) as e:
        log.error(f"Error retrieving post : {post_id}")
        log.error(f"Exception: {e}")
        raise e

    # reduce the descendents comments and add it to this post's
    number_of_comments += sum(results)
    log.debug("{:^6} > {} comments".format(post_id, number_of_comments))

    return number_of_comments


async def get_comments_of_top_stories(
    session: aiohttp.ClientSession, limit: int, iteration: int
) -> int:
    """Retrieve top stories in HN."""

    fetcher = URLFetcher()  # create a new fetcher for this task
    try:
        response = await fetcher.fetch(session, TOP_STORIES_URL)
    except BoomException as e:
        log.error("Error retrieving top stories: {}".format(e))
        # return instead of re-raising as it will go unnoticed
        return
    except Exception as e:  # catch generic exceptions
        log.error("Unexpected exception: {}".format(e))
        return

    tasks = [
        post_number_of_comments(session, fetcher, post_id)
        for post_id in response[:limit]
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # we can safely iterate the results
    for post_id, result in zip(response[:limit], results):
        # and manually check the types
        if isinstance(result, BoomException):
            log.error("Error retrieving comments for top stories: {}".format(result))
        elif isinstance(result, Exception):
            log.error("Unexpected exception: {}".format(result))
        else:
            log.info("Post {} has {} comments ({})".format(post_id, result, iteration))

    return fetcher.fetch_counter  # return the fetch count


async def poll_top_stories_for_comments(
    session: aiohttp.ClientSession, period: int, limit: int
) -> None:
    """Periodically poll for new stories and retrieve number of comments."""

    iteration = 1
    errors = []
    while True:
        log.info(
            "Calculating comments for top {} stories. ({})".format(limit, iteration)
        )

        task = asyncio.create_task(
            get_comments_of_top_stories(session, limit, iteration)
        )

        now = datetime.now()

        def callback(fut):
            try:
                fetch_count = fut.result()
            except BoomException as e:
                log.debug("Adding {} to errors".format(e))
                errors.append(e)
            except Exception as e:
                log.exception("Unexpected error")
                errors.append(e)
            else:
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
