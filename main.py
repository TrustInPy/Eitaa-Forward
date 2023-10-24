from bot import client
from task import starter


async def setup_database():
    await run_database()


async def main():
    await setup_database()
    await starter()

    print("--------------------------------------------------------")
    print("Database ready +++")


client.loop.run_until_complete(main())

client.start()
print("--------------------------------------------------------")
print("Bot started... ")

client.run_until_disconnected()