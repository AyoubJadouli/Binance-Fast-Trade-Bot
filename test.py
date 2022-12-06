import asyncio
import time


async def l1():
    while True:
        await asyncio.sleep(0)
        print(1)
        time.sleep(1)

async def l2():
    await asyncio.sleep(0)
    while True:
        time.sleep(2)
        print(2)
        

async def main(loop):
    background_tasks = set()
    task1=asyncio.create_task(l1())
    task2=asyncio.create_task(l2())
    #await asyncio.gather(l1(loop),l2(loop))
    
    #await asyncio.gather(task1,task2)
    await asyncio.wait([task1,task2],timeout=0.2)
    # await asyncio.wait(task2,timeout=0.3)

    while True:
        print("main lopp ...")
        time.sleep(1)

if __name__ == '__main__':
    print("main code")
    # loop = asyncio.get_event_loop()
    # # main_gr=asyncio.gather(main(loop))
    # # refresh_gr=asyncio.gather(loop_refresh_all_orderbooks(loop))
    # # all_gr=asyncio.gather(main_gr,refresh_gr)
    # loop.run_until_complete(main(loop))
    await l1()
    