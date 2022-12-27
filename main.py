import requests, os, asyncio, logging
from bs4 import BeautifulSoup
from telegram import Chat, ChatMember, Update
from telegram.ext import CallbackContext, CommandHandler, Updater

file = open(input("Enter your log name: "), "a")
max_threads = 100
queue = asyncio.Queue()
checked = []
telegram_chats = []
clear = lambda: os.system('clear')
openai_key = ""
telegram_key = ""
active_threads = 0

async def worker():
    while True:
        task = await queue.get()
        active_threads += 1
        await task
        active_threads -= 1
        queue.task_done()

async def scrape(url: str) -> tuple[list[str], list[str]]:
        print(f'[{active_threads}/{queue.qsize()}] - Scraping:', url)
        response = requests.get(url)
        checked.append(url)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all(href=True)
        tasks = []
        for link in links:
            link_url = link["href"]
            if link_url.startswith("https://t.me/"):
                if (link_url not in telegram_chats):
                    print("[!] - Discovered Telegram URL:", link_url)
                    print("[!] - Telegram Urls:", telegram_chats)
                    telegram_chats.append(link_url)
                    type, description, messages = await handle_telegram(link_url)
                    file.write(f'{link_url},{type},{description},{messages},\n')
            elif link_url.startswith("https://") or link_url.startswith("http://"):
                if (link_url not in checked):
                    task = asyncio.create_task(scrape(link_url))
                    tasks.append(task)
                    await queue.put(task)
                    checked.append(link_url)
        await asyncio.gather(*tasks)

async def handle_telegram(channel: str) -> tuple[list[str], list[str]]:
    updater = Updater(token=telegram_key, use_context=True)
    print("[!] - Checking Telegram URL...")
    channel_id, channel_type = updater.bot.extract_chat_id_and_type(channel)
    print(f'[!] - Channel {channel_id} is {channel_type}')
    #private - DM, group - chatroom, supergroup - really big groupchat, channel - announcements
    await updater.bot.join_chat(channel_id)
    print(f'[!] - Chat Joined!')
    channel = await updater.bot.get_chat(channel_id)
    description = channel.description
    messages = await updater.bot.get_history(chat_id=channel_id, limit=10)
    print(f'[!] - {channel} - {channel_type} - {description}')
    return channel_type, description, messages

async def main():
    try:
        workers = [asyncio.create_task(worker()) for _ in range(max_threads)]
        task = asyncio.create_task(scrape("https://cracked.to/"))
        await queue.put(task)
        #task = asyncio.create_task(scrape("https://nulled.to/"))
        #await queue.put(task)
        await queue.join()
    except KeyboardInterrupt:
        file.close()

asyncio.run(main())