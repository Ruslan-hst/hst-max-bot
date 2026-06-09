import asyncio
import logging
import os
from maxapi import Bot, Dispatcher
from maxapi.types import (
    MessageCreated, BotStarted, MessageCallback,
    RequestContactButton, ButtonsPayload, ContactAttachmentPayload
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("MAX_OWNER_ID", "0"))
WIDGET_URL = os.environ.get("WIDGET_URL", "https://heartfelt-taffy-c8d866.netlify.app/")

bot = Bot(TOKEN)
dp = Dispatcher()


async def notify_owner(text):
    if not OWNER_ID:
        return
    try:
        await bot.send_message(user_id=OWNER_ID, text=text)
    except Exception as e:
        logging.error(f"Failed to notify owner: {e}")


def contact_keyboard():
    """Клавиатура с кнопкой запроса контакта"""
    return ButtonsPayload(
        buttons=[[RequestContactButton(text="📞 Поделиться номером телефона")]]
    )


@dp.bot_started()
async def on_start(event: BotStarted):
    user = event.user
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"

    logging.info(f"BOT STARTED: {user_id} | {name} | {username}")

    await notify_owner(
        f"🏒 Открыл склад в MAX!\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 ID: {user_id}"
    )

    # Приветствие + кнопка поделиться контактом
    await bot.send_message(
        user_id=user_id,
        text=(
            "🏒 Хоккейные клюшки ТОП\n\n"
            "Нажми кнопку ниже чтобы проверить наличие клюшек 👇\n\n"
            "Или поделись номером — мы пришлём уведомление о новых поставках:"
        ),
        attachments=[contact_keyboard()]
    )


@dp.message_created()
async def on_message(event: MessageCreated):
    user = event.message.sender
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"

    # Проверяем — вдруг пришёл контакт
    attachments = event.message.attachments or []
    for att in attachments:
        if isinstance(att, ContactAttachmentPayload):
            phone = att.vcf_info or "не указан"
            contact_name = att.max_info.first_name if att.max_info else name
            logging.info(f"CONTACT from {user_id}: {phone}")
            await notify_owner(
                f"📞 Новый контакт из MAX!\n\n"
                f"👤 {contact_name}\n"
                f"🔗 {username}\n"
                f"🆔 ID: {user_id}\n"
                f"📱 Телефон: {phone}"
            )
            await bot.send_message(
                user_id=user_id,
                text="✅ Спасибо! Мы сохранили твой контакт и пришлём уведомление о новых поставках."
            )
            return

    # Обычное сообщение
    text = event.message.body.text if event.message.body else ""
    logging.info(f"MESSAGE from {user_id} | {name}: {text}")

    await notify_owner(
        f"💬 Сообщение в MAX боте\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 ID: {user_id}\n"
        f"📝 {text}"
    )

    await bot.send_message(
        user_id=user_id,
        text=(
            "Открой виджет чтобы проверить наличие клюшек 👇\n\n"
            f"Или напиши нам напрямую: https://max.ru/id164908988785_bot"
        ),
        attachments=[contact_keyboard()]
    )


async def main():
    logging.info("Starting MAX bot v3 (long polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
