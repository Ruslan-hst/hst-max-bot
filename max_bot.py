import asyncio
import logging
import os
from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, BotStarted

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "f9LHodD0cOKj3WBJkAvespLdqmkf3OqnUL_GAUM7L1fBPYA8SapIg-RVuC159COeVHfp2j9hgt0RO21TDhnE")
OWNER_ID = int(os.environ.get("MAX_OWNER_ID", "0"))
WIDGET_URL = os.environ.get("WIDGET_URL", "https://heartfelt-taffy-c8d866.netlify.app/")

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.bot_started()
async def on_start(event: BotStarted):
    """Когда пользователь нажимает /start или открывает бота"""
    user = event.user
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"

    # Логируем в консоль
    logging.info(f"NEW USER: {user_id} | {name} | {username}")

    # Уведомление владельцу
    if OWNER_ID:
        try:
            await bot.send_message(
                user_id=OWNER_ID,
                text=f"🏒 Новый пользователь открыл склад в MAX!\n\n"
                     f"👤 {name}\n"
                     f"🔗 {username}\n"
                     f"🆔 ID: {user_id}"
            )
        except Exception as e:
            logging.error(f"Failed to notify owner: {e}")

    # Ответ пользователю с кнопкой виджета
    await bot.send_message(
        user_id=user_id,
        text=f"🏒 Хоккейные клюшки ТОП\n\n"
             f"Нажми кнопку ниже чтобы проверить наличие клюшек 👇"
    )


@dp.message_created()
async def on_message(event: MessageCreated):
    """Любое сообщение от пользователя"""
    user = event.message.sender
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"
    text = event.message.body.text if event.message.body else ""

    logging.info(f"MESSAGE from {user_id} | {name} | {username}: {text}")

    # Уведомление владельцу
    if OWNER_ID:
        try:
            await bot.send_message(
                user_id=OWNER_ID,
                text=f"💬 Сообщение в MAX боте\n\n"
                     f"👤 {name}\n"
                     f"🔗 {username}\n"
                     f"🆔 ID: {user_id}\n"
                     f"📝 {text}"
            )
        except Exception as e:
            logging.error(f"Failed to notify owner: {e}")

    # Ответ пользователю
    await bot.send_message(
        user_id=user_id,
        text=f"Открой виджет чтобы проверить наличие клюшек 👇\n\n"
             f"Или напиши нам напрямую: https://max.ru/id164908988785_bot"
    )


async def main():
    logging.info("Starting MAX bot (long polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
