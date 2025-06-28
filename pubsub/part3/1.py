import asyncio
import logging
import random
import signal
import string
import uuid

import attr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@attr.s
class PubSubMessage:
    instance_name = attr.ib()
    message_id = attr.ib(repr=False)
    hostname = attr.ib(repr=False, init=False)
    restarted = attr.ib(repr=False, default=False)
    saved = attr.ib(repr=False, default=False)
    acked = attr.ib(repr=False, default=False)
    extended_cnt = attr.ib(repr=False, default=0)

    def __attrs_post_init__(self):
        self.hostname = f"{self.instance_name}.example.net"


async def publish(queue):
    """Simulates an external publisher of messages.

    Args:
        queue (asyncio.Queue): Queue to publish messages to.
    """
    choices = string.ascii_lowercase + string.digits

    while True:
        msg_id = str(uuid.uuid4())
        host_id = "".join(random.choices(choices, k=4))
        isinstance_name = f"cattle-{host_id}"
        msg = PubSubMessage(message_id=msg_id, instance_name=isinstance_name)
        asyncio.create_task(queue.put(msg))
        logging.debug(f"published message {msg}")
        await asyncio.sleep(random.random())


async def restart_host(msg):
    """Restart a given host.

    Args:
        msg (PubSubMessage): consumed event message for a particular
            host to be restarted.
    """
    await asyncio.sleep(random.random())
    msg.restarted = True
    logging.info(f"Restarted {msg.hostname}")


async def save(msg):
    """Save message to a database.

    Args:
        msg (PubSubMessage): consumed event message to be saved.
    """
    await asyncio.sleep(random.random())
    msg.save = True
    logging.info(f"saved {msg} into database")


async def cleanup(msg):
    """Cleanup tasks related to completing work on a message.

    Args:
        msg (PubSubMessage): consumed event message that is done being
            processed.
    """
    await asyncio.sleep(random.random())
    msg.acked = True
    logging.info(f"Done. Acked {msg}")


async def extend(msg, event):
    """Periodically extend the message acknowledgement deadline.

    Args:
        msg (PubSubMessage): consumed event message to extend.
        event (asyncio.Event): event to watch for message extention or
            cleaning up.
    """
    while not event.is_set():
        msg.extended_cnt += 1
        logging.info(f"Extend deadline by 3 seconds for {msg}")
        await asyncio.sleep(2)

    else:
        await cleanup(msg)


async def handle_message(msg):
    """Kick off tasks for a given message.

    Args:
        msg (PubSubMessage): consumed message to process.
    """
    event = asyncio.Event()
    t = asyncio.create_task(extend(msg, event))
    all_t = await asyncio.gather(save(msg), restart_host(msg))
    event.set()


async def consume(queue):
    """Consumer client to simulate subscribing to a publisher.

    Args:
        queue (asyncio.Queue): Queue from which to consume messages.
    """
    while True:
        msg = await queue.get()
        logging.info(f"Consumed {msg}")
        handle_task = asyncio.create_task(handle_message(msg))


async def shutdown():
    """Cleanup tasks tied to the service's shutdown."""

    logging.info("Closing database connections")
    logging.info("Nacking outstanding messages")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    logging.info("Flushing metrics")


async def main():
    queue = asyncio.Queue()

    try:
        # pub_task = loop.create_task(publish(queue))
        # sub_taks = loop.create_task(consume(queue))
        # loop.run_forever()
        results = await asyncio.gather(
            publish(queue), consume(queue), return_exceptions=True
        )
    except KeyboardInterrupt:
        logging.info("Process started")
        logging.info("successfully shutdown the Mayhem system")
    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
