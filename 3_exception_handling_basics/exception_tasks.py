import asyncio


async def func_a() -> str:
    try:
        print("hello from func a")
        await asyncio.sleep(10)
        return "result from a"
    except asyncio.CancelledError as e:
        print("child func_a was cancelled")
        raise e


async def func_b() -> str:
    try:
        print("hello from func b")
        await asyncio.sleep(3)
        return "result from b"
    except asyncio.CancelledError as e:
        print("child func_b was cancelled")


async def func_c():
    print("hello from func c")
    await asyncio.sleep(5)
    raise ValueError("Error in func c")
    return "result from c"


async def main():
    result = await asyncio.gather(func_a(), func_b(), func_c())
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
