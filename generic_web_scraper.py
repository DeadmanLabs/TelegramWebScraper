import requests, os, asyncio, logging
from bs4 import BeautifulSoup

async def worker():
    while True:
        task = await queue.get()
        active_threads += 1
        await task
        active_threads -= 1
        queue.task_done()

async def scrape(url: str, process: callable[list[str], dict[str, any]]) -> list[str]:
    print(f'[{active_threads}/{queue.qsize()}] - Scraping:', url)
    response = requests.get(url)
    checked.append(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tasks = []
    spider_links, json_info = process(soup)
    for link in spider_links:
        if link not in checked:
            task = asyncio.create_task(scrape(link, process))
            tasks.append(task)
            await queue.put(task)
    await asyncio.gather(*tasks)
    

async def main(threads: int, log_file: str, process: callable[list[str], dict[str, any]]):
    global queue
    queue = asyncio.Queue()
    global checked
    checked = []
    global active_threads
    active_threads = 0
    file = open(log_file, "a")
    try:
        workers = [asyncio.create_task(worker()) for _ in range(threads)]
        task = asyncio.create_task(scrape(input("Enter starting site: "), process))
        await queue.put(task)
        await queue.join()
    except KeyboardInterrupt:
        file.close()

def run(process: callable[list[str], dict[str, any]]):
    log_file = input("Enter your log name: ")
    asyncio.run(main(100, log_file, process))