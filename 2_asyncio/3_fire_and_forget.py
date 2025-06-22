"""
An example of the "fire and forget" pattern awaiting for lower priority.
Lower priority task is slower than higher priority tasks.
Hence it should not block higher priorith tasks.
"""

import asyncio
from datetime import datetime
from typing import Any

import aiohttp


URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{}.json"
FETCH_TIMEOUT = 10
MIN_COMMENTS = 5
fetch_counter = 0


async def fetch(session: aiohttp.ClientSession, url) -> dict[Any, Any]:
    global fetch_counter
    fetch_counter += 1
    async with session.get(url, timeout=FETCH_TIMEOUT) as response:
        return await response.json()


async def email_comments(number_of_comments):
    await asyncio.sleep(1)
    print(f"******* Emailing comments ************** {number_of_comments}")


async def post_number_of_comments(
    session: aiohttp.ClientSession,
    post_id: int,
    task_registry: set[asyncio.Task] | None,
) -> tuple[int, set[asyncio.Task]]:
    """Retrieve data for current post and recursively for all comments."""

    url = URL_TEMPLATE.format(post_id)
    now = datetime.now()
    response = await fetch(session, url)
    print(
        f" > Fetching of {post_id} took {(datetime.now() - now).total_seconds()} seconds"
    )

    if "kids" not in response:  # base case, there are no comments
        return 0, None

    # calculate this post's comments as number of comments
    number_of_comments = len(response["kids"])

    # create recursive tasks for all comments
    print(f'> Fetching {number_of_comments} child posts of post {post_id}"')

    tasks = [
        post_number_of_comments(session, kid_id, task_registry)
        for kid_id in response["kids"]
    ]

    # schedule the tasks and retrieve results
    results = await asyncio.gather(*tasks)

    # reduce the descendents comments and add it to this post'
    for num_comments, _ in results:
        number_of_comments += num_comments

    if number_of_comments > MIN_COMMENTS:
        task = asyncio.create_task(email_comments(number_of_comments))
        task_registry.add(task)

    print(f"{post_id} > {number_of_comments} comments")

    return number_of_comments, task_registry


async def main() -> None:
    """Async entry point coroutine."""
    post_id = 8863
    now = datetime.now()
    task_registry = set()
    async with aiohttp.ClientSession() as session:
        now = datetime.now()
        comments, task_registry = await post_number_of_comments(
            session, post_id, task_registry
        )
        print(
            f"Calculating comments took {(datetime.now() - now).total_seconds():.2f} seconds and {fetch_counter} fetches"
        )

    print(f"-- Post {post_id} has {comments} comments")

    await asyncio.gather(*list(task_registry))


if __name__ == "__main__":
    asyncio.run(main())
