from telethon import TelegramClient, events

telegram_client = TelegramClient('aaa', '23382905', 'bot83779:55b9fbae-1a76-4731-9add-173dbc02b839', proxy=("socks5", "127.0.0.1", 10809, True))

@telegram_client.on(events.NewMessage(chats='thethewholeme'))
async def my_event_handler(event):
    await telegram_client.forward_messages('eitaayar_bot', event.message)

with telegram_client:
    telegram_client.run_until_disconnected()
