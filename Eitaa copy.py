import os
import re
import time
import asyncio
import requests
import aiosqlite
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()
CHAT_ID = int(os.getenv("ADMIN_ID"))
DATABASE_NAME = os.getenv("DATABASE_NAME")


telegram_client = TelegramClient('aaa', '23382905', 'e461dd337c4a9c41578cd48c0e9ab3de', proxy=(
    "socks5", "127.0.0.1", 10809, True))

token = 'bot56443:49f2b2c3-047a-4897-a5c8-0236f2622680'
# token = 'bot83779:55b9fbae-1a76-4731-9add-173dbc02b839'
chat_id = 'testtest11'
replacement_text = '@test'


async def create_database():
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id INTEGER PRIMARY KEY
            )
        """)        
        await conn.commit()
        await conn.close()
    except Exception as e:
            print("Error in create_database: " + e)

asyncio.run(create_database())


async def contains_link(message):
    url_pattern = re.compile(r'http\S+|www.\S+')
    return bool(url_pattern.search(message))


async def get_active_chats():
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("SELECT chat_id FROM active_chats")
        active_chats = [row[0] for row in await cursor.fetchall()]
        await conn.close()
        return active_chats
    except Exception as e:
            print("Error in get_active_chat: " + e)

active_chats = asyncio.run(get_active_chats())


@telegram_client.on(events.NewMessage(pattern='/addchat'))
async def add_chat(event):
    if event.message.chat_id == CHAT_ID:
        try :
            chat_to_add = event.message.text.split()[1]
            chat_entity = await telegram_client.get_entity(chat_to_add)
            chat_id_to_add = chat_entity.id
            chat_id_to_add = int('-100' + str(chat_id_to_add))
            conn = await aiosqlite.connect(DATABASE_NAME)
            cursor = await conn.cursor()
            await cursor.execute("INSERT OR IGNORE INTO active_chats (chat_id) VALUES (?)", (chat_id_to_add,))
            await conn.commit()
            await conn.close()
            active_chats.append(chat_id_to_add)
            await event.respond(f'Chat {chat_to_add} has been added.')
        except Exception as e:
            print("Error in addchat: " + e)


@telegram_client.on(events.NewMessage(pattern='/deletechat'))
async def delete_chat(event):
    if event.message.chat_id == CHAT_ID:
        try :
            chat_to_delete = event.message.text.split()[1]
            chat_entity = await telegram_client.get_entity(chat_to_delete)
            chat_id_to_delete = chat_entity.id
            chat_id_to_delete = int('-100' + str(chat_id_to_delete))
            conn = await aiosqlite.connect(DATABASE_NAME)
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id_to_delete,))
            await conn.commit()
            await conn.close()
            active_chats.remove(chat_id_to_delete)
            await event.respond(f'Chat {chat_to_delete} has been removed.')
        except Exception as e:
            print("Error in deletechat: " + e)


@telegram_client.on(events.NewMessage())
async def telegram_event_handler(event):
    if event.message.chat_id not in active_chats:
        return

    message = event.message.text

    if await contains_link(message):
        return

    if event.message.grouped_id:
        return

    if re.search(r'http\S+|www.\S+', message):
        return

    if '@' in message:
        message = re.sub(r'@\w+', replacement_text, message)

    if event.message.media:
        file_path = await telegram_client.download_media(event.message)
        files = {'file': open(file_path, 'rb')}

        url = f'https://eitaayar.ir/api/{token}/sendFile'

        headers = {
            'Content-Type': 'multipart/form-data'
        }

        data = {
            'chat_id': chat_id,
            'caption': message,
            'date': time.time()
        }
        try:
            response = requests.post(url, data=data, files=files)
        except Exception as e:
            print("Error in request for send text message with file: " + e)

        files['file'].close()
        os.remove(file_path)
        print(response.json())

    else:

        url = f'https://eitaayar.ir/api/{token}/sendMessage'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'chat_id': chat_id,
            'text': message,
            'date': time.time()
        }
        try:
            response = requests.post(url, headers=headers, data=data)
        except Exception as e:
            print("Error in request for send text message without file: " + e)

        print(response.json())


async def main():
    await telegram_client.start()
    await telegram_client.run_until_disconnected()

asyncio.run(main())
