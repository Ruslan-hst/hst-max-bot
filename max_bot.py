import asyncio
import logging
import os
from maxapi import Bot, Dispatcher
from maxapi.types import (
    MessageCreated, BotStarted,
    RequestContactButton, ButtonsPayload, ContactAttachmentPayload
)
from maxapi.types.attachments.contact import Contact
from maxapi.types.attachments.buttons.attachment_button import AttachmentButton
from maxapi.enums import AttachmentType

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("MAX_OWNER_ID", "0"))

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
    payload = ButtonsPayload(
        buttons=[[RequestContactButton(text="📞 Поделиться номером телефона")]]
    )
    return AttachmentButton(type=AttachmentType.INLINE_KEYBOARD, payload=payload)


async def send_welcome(user_id, name, username):
    await notify_owner(
        f"🏒 Открыл склад в MAX!\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 ID: {user_id}"
    )
    try:
        await bot.send_message(
            user_id=user_id,
            text=(
                "🏒 Хоккейные клюшки ТОП\n\n"
                "Нажми кнопку ниже чтобы проверить наличие клюшек 👇\n\n"
                "Или поделись номером — пришлём уведомление о новых поставках:"
            ),
            attachments=[contact_keyboard()]
        )
    except Exception as e:
        logging.error(f"send_welcome error: {e}")
        await bot.send_message(
            user_id=user_id,
            text="🏒 Хоккейные клюшки ТОП\n\nНажми кнопку ниже чтобы проверить наличие клюшек 👇"
        )


@dp.bot_started()
async def on_bot_started(event: BotStarted):
    user = event.user
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"
    logging.info(f"BOT STARTED: {user_id} | {name} | {username}")
    await send_welcome(user_id, name, username)


@dp.message_created()
async def on_message(event: MessageCreated):
    user = event.message.sender
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "без ника"

    body = event.message.body
    attachments = body.attachments if body and body.attachments else []

    # Логируем все вложения для диагностики
    for att in attachments:
        logging.info(f"ATTACHMENT type={type(att).__name__} data={att}")

    # Контакт — проверяем оба варианта: Contact и ContactAttachmentPayload
    for att in attachments:
        phone = None
        if isinstance(att, Contact):
            # Contact.payload содержит ContactAttachmentPayload
            if att.payload and isinstance(att.payload, ContactAttachmentPayload):
                phone = att.payload.vcf_info or "не указан"
                contact_user = att.payload.max_info
        elif isinstance(att, ContactAttachmentPayload):
            phone = att.vcf_info or "не указан"
            contact_user = att.max_info

        if phone is not None:
            contact_name = contact_user.first_name if contact_user else name
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
                text="✅ Спасибо! Пришлём уведомление о новых поставках."
            )
            return

    text = body.text.strip() if body and body.text else ""
    logging.info(f"MESSAGE from {user_id} | {name}: {text}")

    if text.lower() in ["/start", "start"]:
        await send_welcome(user_id, name, username)
        return

    await notify_owner(
        f"💬 Сообщение в MAX боте\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 ID: {user_id}\n"
        f"📝 {text}"
    )
    try:
        await bot.send_message(
            user_id=user_id,
            text="Открой виджет чтобы проверить наличие клюшек 👇",
            attachments=[contact_keyboard()]
        )
    except Exception as e:
        logging.error(f"reply error: {e}")
        await bot.send_message(
            user_id=user_id,
            text="Открой виджет чтобы проверить наличие клюшек 👇"
        )


async def main():
    logging.info("Starting MAX bot v3 (long polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
