
import os
import ipaddress
import asyncio
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from database import init_db, register_user, get_user

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 TELEGRAM INSPECTOR\n\n"
        "Команды:\n"
        "/consent — регистрация с согласием\n"
        "/lookup ID — поиск регистрации (администратор)\n"
        "/ipcheck IP — проверка IP (администратор)\n\n"
        "Пример:\n"
        "/ipcheck 8.8.8.8"
    )


async def consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    register_user(user.id, user.username)

    await update.message.reply_text(
        "✅ Регистрация выполнена.\n"
        "Ваш Telegram ID сохранён."
    )


async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /lookup TELEGRAM_ID"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Некорректный Telegram ID.")
        return

    result = get_user(target_id)

    if result:
        telegram_id, username = result
        await update.message.reply_text(
            f"👤 Найденная регистрация\n\n"
            f"ID: {telegram_id}\n"
            f"Username: @{username or 'не указан'}"
        )
    else:
        await update.message.reply_text(
            "Пользователь не найден в базе регистраций."
        )


def get_ip_info(ip):
    url = f"https://ipwho.is/{ip}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


async def ipcheck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /ipcheck IP\n"
            "Пример: /ipcheck 8.8.8.8"
        )
        return

    raw_ip = context.args[0]

    try:
        address = ipaddress.ip_address(raw_ip)
    except ValueError:
        await update.message.reply_text("❌ Некорректный IP-адрес.")
        return

    if not address.is_global:
        await update.message.reply_text(
            "❌ Можно проверять только публичные IP-адреса."
        )
        return

    await update.message.reply_text("🔍 Проверяю IP-адрес...")

    try:
        data = await asyncio.to_thread(get_ip_info, str(address))

        if not data.get("success"):
            await update.message.reply_text(
                "Не удалось получить информацию об IP."
            )
            return

        connection = data.get("connection") or {}

        result = (
            "🔎 IP INSPECTOR\n\n"
            f"🌐 IP: {data.get('ip', 'Неизвестно')}\n"
            f"🏙 Город: {data.get('city', 'Неизвестно')}\n"
            f"📍 Регион: {data.get('region', 'Неизвестно')}\n"
            f"🌍 Страна: {data.get('country', 'Неизвестно')}\n"
            f"🏳 Код страны: {data.get('country_code', 'Неизвестно')}\n"
            f"📡 Провайдер: {connection.get('isp', 'Неизвестно')}\n"
            f"🔢 ASN: {connection.get('asn', 'Неизвестно')}\n"
            f"🏢 Организация: {connection.get('org', 'Неизвестно')}\n\n"
            "ℹ️ Геолокация IP приблизительная."
        )

        await update.message.reply_text(result)

    except requests.RequestException:
        await update.message.reply_text(
            "Ошибка подключения к сервису проверки IP."
        )
    except Exception:
        await update.message.reply_text(
            "Произошла ошибка при обработке запроса."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN.")

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("consent", consent))
    app.add_handler(CommandHandler("lookup", lookup))
    app.add_handler(CommandHandler("ipcheck", ipcheck))

    print("Telegram Inspector запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()

