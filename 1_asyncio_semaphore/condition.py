import asyncio
import random


async def producer(
    buffer: list, condition: asyncio.Condition, name: str, item_count: int
) -> None:
    for i in range(item_count):
        item = f"item {i + 1} from {name}"
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate work before producing

        async with condition:  # Acquire the lock before checking/modifying the buffer
            # Wait if the buffer is full
            while len(buffer) >= 5:  # Maximum buffer size is 5
                print(f"[{name}] Buffer is full ({len(buffer)} items). Waiting...")
                await condition.wait()  # Release lock and wait for a notification

            buffer.append(item)
            print(f"[{name}] Produced {item}. Buffer size: {len(buffer)}")

            # Notify waiting consumers that an item is available
            condition.notify_all()  # Notify one waiting consumer

    print(f"[{name}] Finished producing {item_count} items.")


async def consumer(buffer: list[int], condition: asyncio.Condition, name: str):
    """Consumes items from the buffer."""
    while True:
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Simulate work before consuming

        async with condition:  # Acquire the lock before checking/modifying the buffer
            # Wait if the buffer is empty
            while not buffer:
                print(f"[{name}] Buffer is empty. Waiting...")
                await condition.wait()  # Release lock and wait for a notification

            # Remove an item from the buffer
            item = buffer.pop(0)
            print(f"[{name}] Consumed {item}. Buffer size: {len(buffer)}")

            # Notify waiting producers that space is available
            condition.notify_all()  # Notify one waiting producer


async def main():
    """Main function to run the producer-consumer example."""
    buffer = []
    # Create a Condition. It includes an internal lock.
    condition = asyncio.Condition()

    # Create producer and consumer tasks
    producer1_task = asyncio.create_task(producer(buffer, condition, "Producer-1", 10))
    # producer2_task = asyncio.create_task(producer(buffer, condition, "Producer-2", 5))
    consumer1_task = asyncio.create_task(consumer(buffer, condition, "Consumer-1"))
    consumer2_task = asyncio.create_task(consumer(buffer, condition, "Consumer-2"))

    await asyncio.gather(producer1_task, consumer1_task, consumer2_task)


if __name__ == "__main__":
    print("Starting producer-consumer example...")
    asyncio.run(main())
