from telethon import TelegramClient, events
import asyncio
import requests
import time
import re
import os
import aiosqlite
from dotenv import load_dotenv

load_dotenv()
CHAT_ID = int(os.getenv("CHAT_ID"))
DATABASE_NAME = int(os.getenv("DATABASE_NAME"))


telegram_client = TelegramClient('aaa', '23382905', 'e461dd337c4a9c41578cd48c0e9ab3de', proxy=(
    "socks5", "127.0.0.1", 10809, True))

token = 'bot56443:49f2b2c3-047a-4897-a5c8-0236f2622680'
# token = 'bot83779:55b9fbae-1a76-4731-9add-173dbc02b839'
chat_id = 'testtest11'
replacement_text = '@test'


async def create_database(DATABASE_NAME):
    try:
        connection = await aiosqlite.connect(DATABASE_NAME)
        print("Database connection established.")
        return connection
    except aiosqlite.Error as e:
        print(f"Error: {e}")
        return None


async def create_connections_table(connection):
    try:
        cursor = await connection.cursor()
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS free_games (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                tel_channel TEXT NOT NULL,
                eitaa_channel TEXT NOT NULL
            );

            """
        )
        await connection.commit()
        print("Connections table created.")
    except aiosqlite.Error as e:
        print(f"Error creating table: {e}")



@telegram_client.on(events.NewMessage(chats=('testesge')))
async def telegram_event_handler(event):
    message = event.message.text
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

        response = requests.post(url, data=data, files=files)

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

        response = requests.post(url, headers=headers, data=data)

        print(response.json())


@telegram_client.on(events.NewMessage(func=lambda e: e.is_group))
async def telegram_event_handler(event):
    if event.message.chat_id == CHAT_ID:
        message = event.message.text
        if message == "/connect":
            try:
                conn = await aiosqlite.connect(DATABASE_NAME)
                cursor = await conn.curser()
                await cursor.execute("SELECT * FROM connections")
                connections = await cursor.fetchall()
                await conn.close()
            except Exception as e:
                print(e)
            connection_button = []
            if connections:
                await telegram_client.send_message(CHAT_ID, "اتصالات موجود:", buttons=connection_button)
                for connection in connections:
                    # tel_channel, eitaa_channel = connection
                    print("Bot Started.")
                    print(connection)



telegram_client.start()
asyncio.get_event_loop().run_forever()
