from telethon import TelegramClient, events
import asyncio
import requests
import time
import re

telegram_client = TelegramClient('aaa2', '25807486', 'ba12a961667ee37788fc5521be91037f', proxy=("socks5", "127.0.0.1", 10809, True))

token = 'bot83779:55b9fbae-1a76-4731-9add-173dbc02b839'
chat_id = 'twiper'
replacement_text = '@twiper'

@telegram_client.on(events.NewMessage(chats=('OfficialPersianTwitter')))
async def telegram_event_handler(event):
    message = event.message.text

    if '@' in message:
        message = re.sub(r'@\w+', replacement_text, message)

    url = f'https://eitaayar.ir/api/{token}/sendMessage'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'chat_id': chat_id,
        'text': message,
        'date': time.time() + 2 
    }

    response = requests.post(url, headers=headers, data=data)

    print(response.json())

telegram_client.start()
asyncio.get_event_loop().run_forever()
