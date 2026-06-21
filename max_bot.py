import asyncio
import logging
import os
from maxapi import Bot, Dispatcher
from maxapi.types import (
    MessageCreated, BotStarted,
    RequestContactButton, ButtonsPayload, ContactAttachmentPayload, LinkButton, OpenAppButton
)
from maxapi.types.attachments.contact import Contact
from maxapi.types.attachments.buttons.attachment_button import AttachmentButton
from maxapi.enums import AttachmentType

import re

def parse_vcard(vcf):
    if not vcf:
        return None, None
    m = re.search(r'TEL[^:]*:([\+\d]+)', vcf)
    phone = m.group(1) if m else None
    m2 = re.search(r'FN:([^\n\r]+?)(?:\s+\w+:|END:)', vcf)
    name = m2.group(1).strip() if m2 else None
    return phone, name


logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("MAX_BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("MAX_OWNER_ID", "0"))
WIDGET_URL = "https://heartfelt-taffy-c8d866.netlify.app/"
MANAGER_URL = "https://t.me/hockey_top_bot"
MAX_BOT_USERNAME = "id164908988785_1_bot"

bot = Bot(TOKEN)
dp = Dispatcher()

# Храним ID пользователей, которым уже показали приветствие
seen_users = set()


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


def main_keyboard():
    payload = ButtonsPayload(
        buttons=[
            [OpenAppButton(text="🏒 Проверить наличие", web_app=MAX_BOT_USERNAME)],
            [LinkButton(text="💬 Написать менеджеру", url=MANAGER_URL)]
        ]
    )
    return AttachmentButton(type=AttachmentType.INLINE_KEYBOARD, payload=payload)


async def send_welcome(user_id, name, username):
    seen_users.add(user_id)
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
                "👋 Привет! Это бот склада «Хоккейные клюшки ТОП».\n\n"
                "Если у вас есть какие-то вопросы — напишите менеджеру."
            ),
            attachments=[main_keyboard()]
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
                raw_vcf = att.payload.vcf_info or ""
                parsed_phone, _ = parse_vcard(raw_vcf)
                phone = parsed_phone or raw_vcf or "не указан"
                contact_user = att.payload.max_info
        elif isinstance(att, ContactAttachmentPayload):
            raw_vcf = att.vcf_info or ""
            parsed_phone, _ = parse_vcard(raw_vcf)
            phone = parsed_phone or raw_vcf or "не указан"
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

    if user_id not in seen_users:
        seen_users.add(user_id)
        reply_text = (
            "👋 Привет! Это бот склада «Хоккейные клюшки ТОП».\n\n"
            "Если у вас есть какие-то вопросы — напишите менеджеру."
        )
    else:
        reply_text = (
            "Я не решаю такие вопросы 🙂\n"
            "Если у вас есть вопрос — напишите менеджеру, "
            "или нажмите «Проверить наличие» для просмотра склада."
        )

    try:
        await bot.send_message(
            user_id=user_id,
            text=reply_text,
            attachments=[main_keyboard()]
        )
    except Exception as e:
        logging.error(f"reply error: {e}")
        await bot.send_message(user_id=user_id, text=reply_text)


async def main():
    logging.info("Starting MAX bot v3 (long polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
