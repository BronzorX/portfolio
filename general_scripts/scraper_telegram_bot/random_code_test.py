import asyncio

import telegram

token = ""


async def get_bot():
    bot = telegram.Bot(token)
    async with bot:
        print(await bot.get_me())


async def receive_update():
    bot = telegram.Bot(token)
    async with bot:
        updates = (await bot.get_updates())
        print(updates)


async def send_message():
    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text='Offerta amazon blablablablablabla', chat_id=335691755)


if __name__ == '__main__':
    asyncio.run(send_message())
