import os
import re
import time
import asyncio
import requests
import aiosqlite
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHAT_ID = int(os.getenv("CHAT_ID"))
DATABASE_NAME = os.getenv("DATABASE_NAME")
INITIAL_ADMIN_ID = int(os.getenv("ADMIN_ID"))
EITAA_TOKEN = os.getenv("EITAA_TOKEN")


# , proxy=("socks5", "127.0.0.1", 10809, True))
telegram_client = TelegramClient('aaa', API_ID, API_HASH)

proxies = {
    'http': 'http://127.0.0.1:1071',
    'https': 'http://127.0.0.1:1071',
    'socks': 'socks://127.0.0.1:1070'
}
# proxies = {
#     'http': 'socks5://127.0.0.1:10809',
#     'https': 'socks5://127.0.0.1:10809'
# }


async def create_database():
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                telegram_chat_id INTEGER,
                chat_id INTEGER,
                replacement_text TEXT,
                PRIMARY KEY (telegram_chat_id, chat_id)
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)
        await conn.commit()
        await conn.close()
    except Exception as e:
        print("Error in create_database: " + str(e))


asyncio.run(create_database())


async def add_admin(user_id):
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        await conn.commit()
        await conn.close()
    except Exception as e:
        print("Error in add_admin: " + str(e))


async def remove_admin(user_id):
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await conn.commit()
        await conn.close()
    except Exception as e:
        print("Error in remove_admin: " + str(e))


@telegram_client.on(events.NewMessage(pattern='/addadmin'))
async def add_admin_command(event):
    if event.message.sender.id == INITIAL_ADMIN_ID:
        try:
            user_id_to_add = int(event.message.text.split()[1])
            await add_admin(user_id_to_add)
            await event.respond(f'User {user_id_to_add} has been added as an admin.')
        except Exception as e:
            print("Error in addadmin command: " + str(e))


@telegram_client.on(events.NewMessage(pattern='/removeadmin'))
async def remove_admin_command(event):
    if event.message.sender.id == INITIAL_ADMIN_ID:
        try:
            user_id_to_remove = int(event.message.text.split()[1])
            await remove_admin(user_id_to_remove)
            await event.respond(f'User {user_id_to_remove} has been removed from admins.')
        except Exception as e:
            print("Error in removeadmin command: " + str(e))


async def is_admin(user_id):
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        await conn.close()
        return result is not None
    except Exception as e:
        print("Error in is_admin: " + str(e))


async def contains_link(message):
    url_pattern = re.compile(r'http\S+|www.\S+')
    return bool(url_pattern.search(message))


async def get_active_chats():
    try:
        conn = await aiosqlite.connect(DATABASE_NAME)
        cursor = await conn.cursor()
        await cursor.execute("SELECT telegram_chat_id, chat_id, replacement_text FROM active_chats")
        active_chats = [(row[0], row[1], row[2]) for row in await cursor.fetchall()]
        await conn.close()
        return active_chats
    except Exception as e:
        print("Error in get_active_chat: " + str(e))


active_chats = asyncio.run(get_active_chats())


@telegram_client.on(events.NewMessage(pattern='/help'))
async def add_chat(event):
    if not await is_admin(event.message.chat_id) and event.message.sender_id != INITIAL_ADMIN_ID:
        return
    if event.message.chat_id == CHAT_ID:
        await telegram_client.send_message(event.message.chat_id, """
        دستورات موجود :\n/removeadmin [user id]\n/addadmin [user id]\n/addchat [telegram chat] [eitaa chat] [replacement test*]\n/deletechat [telegram chat] [eitaa chat]\n/chats\n
        """)


@telegram_client.on(events.NewMessage(pattern='/addchat'))
async def add_chat(event):
    if not await is_admin(event.message.chat_id) and event.message.sender_id != INITIAL_ADMIN_ID:
        return
    if event.message.chat_id == CHAT_ID:
        try:
            chat_to_add, chat_id, * \
                replacement_text = event.message.text.split()[1:]
            replacement_text = ' '.join(
                replacement_text) if replacement_text else ''
            try:
                chat_entity = await telegram_client.get_entity(chat_to_add)
            except Exception as e:
                await event.respond(f"There is no Chat as **{chat_to_add}**")
                return
            telegram_chat_id_to_add = chat_entity.id
            telegram_chat_id_to_add = int(
                '-100' + str(telegram_chat_id_to_add))
            conn = await aiosqlite.connect(DATABASE_NAME)
            cursor = await conn.cursor()

            await cursor.execute("SELECT * FROM active_chats WHERE telegram_chat_id=?", (telegram_chat_id_to_add,))
            data = await cursor.fetchone()

            if data is None:
                await cursor.execute("INSERT INTO active_chats (telegram_chat_id, chat_id, replacement_text) VALUES (?, ?, ?)", (telegram_chat_id_to_add, chat_id, replacement_text))
                await conn.commit()
                active_chats.append(
                    (telegram_chat_id_to_add, chat_id, replacement_text))
                await event.respond(f'Chat **{chat_to_add}** has been added to **{chat_id}** with replacement text "{replacement_text}".')
            else:
                await event.respond(f'Chat **{chat_to_add}** already exists.')

            await conn.close()
        except Exception as e:
            print("Error in addchat: " + str(e))


@telegram_client.on(events.NewMessage(pattern='/deletechat'))
async def delete_chat(event):
    if not await is_admin(event.message.chat_id) and event.message.sender_id != INITIAL_ADMIN_ID:
        return
    if event.message.chat_id == CHAT_ID:
        try:
            chat_to_delete, chat_id = event.message.text.split()[1:3]
            chat_entity = await telegram_client.get_entity(chat_to_delete)
            telegram_chat_id_to_delete = chat_entity.id
            telegram_chat_id_to_delete = int(
                '-100' + str(telegram_chat_id_to_delete))
            conn = await aiosqlite.connect(DATABASE_NAME)
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM active_chats WHERE telegram_chat_id = ? AND chat_id = ?", (telegram_chat_id_to_delete, chat_id))
            await conn.commit()
            await conn.close()
            elements_to_match = (telegram_chat_id_to_delete, chat_id)
            for i in reversed(range(len(active_chats))):
                if active_chats[i][:2] == elements_to_match:
                    del active_chats[i]
            # active_chats.remove((telegram_chat_id_to_delete, chat_id))
            await event.respond(f'Chat {chat_to_delete} has been removed from {chat_id}.')
        except Exception as e:
            print("Error in deletechat: " + str(e))


@telegram_client.on(events.NewMessage(pattern='/chats'))
async def check_chats(event):
    if not await is_admin(event.message.chat_id) and event.message.sender_id != INITIAL_ADMIN_ID:
        return
    if event.message.chat_id == CHAT_ID:
        try:
            conn = await aiosqlite.connect(DATABASE_NAME)
            cursor = await conn.cursor()
            await cursor.execute("SELECT telegram_chat_id, chat_id FROM active_chats")
            active_chats = [(row[0], row[1]) for row in await cursor.fetchall()]
            await conn.close()

            response_message = 'Active chats:\n'

            for telegram_chat_id, chat_id in active_chats:
                response_message += f'Telegram Chat ID: {telegram_chat_id}, Chat ID: {chat_id}\n'

            await event.respond(response_message)

        except Exception as e:
            print("Error in checkchats: " + str(e))


@telegram_client.on(events.NewMessage())
async def telegram_event_handler(event):
    if event.message.chat_id not in [row[0] for row in active_chats]:
        return

    for chat in active_chats:
        if chat[0] == event.message.chat_id:
            chat_id = chat[1]
            replacement_text = chat[2]
            message = event.message.text

            if '@' in message and replacement_text:
                message = re.sub(r'@\w+', replacement_text, message)

            if event.message.media:
                print("---------------------------------")
                print("start of downloding media...")
                print(datetime.now())
                file_path = await telegram_client.download_media(event.message)
                print("---------------------------------")
                print("Download is done --")
                print(datetime.now())
                url = f'https://eitaayar.ir/api/{EITAA_TOKEN}/sendFile'
                headers = {
                    'Content-Type': 'multipart/form-data'
                }
                data = {
                    'chat_id': chat_id,
                    'caption': message,
                    'date': time.time()
                }
                try:
                    with open(file_path, 'rb') as f:
                        files = {'file': f}
                        print("---------------------------------")
                        print("Startint to upload --")
                        print(datetime.now())
                        response = requests.post(
                            url, data=data, files=files, proxies=proxies)
                        print("---------------------------------")
                        print("Upload done --")
                        print(datetime.now())
                        print(response.json())
                except Exception as e:
                    print("Error in request for send text message with file: " + str(e))
                finally:
                    os.remove(file_path)

            else:

                url = f'https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage'

                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'date': time.time()
                }
                try:
                    print("---------------------------------")
                    print("Startint to send text message --")
                    print(datetime.now())
                    response = requests.post(
                        url, headers=headers, data=data, proxies=proxies)
                    print(response.json())
                except Exception as e:
                    print(
                        "Error in request for send text message without file: " + str(e))


async def main():
    await telegram_client.start()
    print("Started...")
    await telegram_client.run_until_disconnected()

asyncio.run(main())
