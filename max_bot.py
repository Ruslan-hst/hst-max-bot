import asyncio
import logging
import os
from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, BotStarted

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("MAX_OWNER_ID", "0"))
WIDGET_URL = os.environ.get("WIDGET_URL", "https://heartfelt-taffy-c8d866.netlify.app/")

bot = Bot(TOKEN)
dp = Dispatcher()


async def notify_owner(user_id, name, username, event_type):
    """Отправить уведомление владельцу"""
    if not OWNER_ID:
        return
    icons = {"open": "🏒 Открыл виджет склада", "start": "👋 Написал /start", "message": "💬 Написал сообщение"}
    text = (
        f"{icons.get(event_type, '📌 Событие')}\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 ID: {user_id}"
    )
    try:
        await bot.send_message(user_id=OWNER_ID, text=text)
    except Exception as e:
        logging.error(f"Failed to notify owner: {e}")


@dp.bot_started()
async def on_start(event: BotStarted):
    """Срабатывает когда пользователь нажимает кнопку открытия бота или виджета"""
    user = event.user
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"

    logging.info(f"BOT STARTED: {user_id} | {name} | {username}")

    await notify_owner(user_id, name, username, "open")

    await bot.send_message(
        user_id=user_id,
        text=(
            "🏒 Хоккейные клюшки ТОП\n\n"
            "Нажми кнопку ниже чтобы проверить наличие клюшек 👇"
        )
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

    await notify_owner(user_id, name, username, "message")

    await bot.send_message(
        user_id=user_id,
        text=(
            "Открой виджет чтобы проверить наличие клюшек 👇\n\n"
            f"Или напиши нам напрямую: https://max.ru/id164908988785_bot"
        )
    )


async def main():
    logging.info("Starting MAX bot (long polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
