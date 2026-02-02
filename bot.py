import asyncio
import json
import logging
import os
import re
from asyncio import Lock
from datetime import date, datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    AIORateLimiter,
)
from telegram.error import BadRequest, RetryAfter

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен берём из переменной окружения (на хостинге задаёшь BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения! Укажи его в настройках хостинга.")

# ================== РАСПИСАНИЕ ==================
SCHEDULES = {
    "math": {
        "title": "📐 Математика (профиль)",
        "pn": (
            "*Понедельник*\n"
            "2️⃣ География 🌍 *(08.55 : 09.40)*\n"
            "3️⃣ Алгебра ➗ *(09.55 : 10.40)*\n"
            "4️⃣ Геометрия 📐 *(10.55 : 11.40)*\n"
            "5️⃣ Физкультура 🏃 *(11.55 : 12.40)*\n"
            "6️⃣ Русский 🇷🇺 *(12.50 : 13.35)*\n"
            "7️⃣ Химия 🧪 *(13.45 : 14.30)*"
        ),
        "vt": (
            "*Вторник*\n"
            "2️⃣ История 🏛 *(08.55 : 09.40)*\n"
            "3️⃣ Физика ⚡ *(09.55 : 10.40)*\n"
            "4️⃣ Иностранный 🌍 *(10.55 : 11.40)*\n"
            "5️⃣ Информатика 💻 *(11.55 : 12.40)*\n"
            "6️⃣ Белорусский 🇧🇾 *(12.50 : 13.35)*\n"
            "7️⃣ Бел. лит 📚 *(13.45 : 14.30)*\n"
            "8️⃣ Классный час ⏰ *(14.40 : 15.25)*"
        ),
        "sr": (
            "*Среда*\n"
            "2️⃣ Черчение 📏 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Химия 🧪 *(10.55 : 11.40)*\n"
            "5️⃣ Иностранный 🌍 *(11.55 : 12.40)*\n"
            "6️⃣ Физика ⚡ *(12.50 : 13.35)*\n"
            "7️⃣ Алгебра ➗ *(13.45 : 14.30)*\n"
            "8️⃣ Геометрия 📐 *(14.40 : 15.25)*"
        ),
        "cht": (
            "*Четверг*\n"
            "1️⃣ Русский 🇷🇺 *(08.00 : 08.45)*\n"
            "2️⃣ Алгебра ➗ *(08.55 : 09.40)*\n"
            "3️⃣ История 🏛 *(09.55 : 10.40)*\n"
            "4️⃣ Физкультура 🏃 *(10.55 : 11.40)*\n"
            "5️⃣ Белорусский 🇧🇾 *(11.55 : 12.40)*\n"
            "6️⃣ Рус. лит 📚 *(12.50 : 13.35)*\n"
            "7️⃣ Русский 🇷🇺 *(13.45 : 14.30)*\n"
            "8️⃣ Инф. час ⏰ *(14.40 : 15.25)*"
        ),
        "pt": (
            "*Пятница*\n"
            "2️⃣ Физкультура 🏃 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Общество ⚖️ *(10.55 : 11.40)*\n"
            "5️⃣ Доприз/Мед 🪖 *(11.55 : 12.40)*\n"
            "6️⃣ Русский 🇷🇺 *(12.50 : 13.35)*\n"
            "7️⃣ Алгебра ➗ *(13.45 : 14.30)*"
        ),
    },
    "chem": {
        "title": "🧪 Химия (профиль)",
        "pn": (
            "*Понедельник*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ География 🌍 *(08.55 : 09.40)*\n"
            "3️⃣ Химия 🧪 *(09.55 : 10.40)*\n"
            "4️⃣ Химия 🧪 *(10.55 : 11.40)*\n"
            "5️⃣ Физкультура 🏃 *(11.55 : 12.40)*\n"
            "6️⃣ Русский 🇷🇺 *(12.50 : 13.35)*"
        ),
        "vt": (
            "*Вторник*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ История 🏛 *(08.55 : 09.40)*\n"
            "3️⃣ Физика ⚡ *(09.55 : 10.40)*\n"
            "4️⃣ Иностранный 🌍 *(10.55 : 11.40)*\n"
            "5️⃣ Химия 🧪 *(11.55 : 12.40)*\n"
            "6️⃣ Белорусский 🇧🇾 *(12.50 : 13.35)*\n"
            "7️⃣ Бел. лит 📚 *(13.45 : 14.30)*\n"
            "8️⃣ Классный час ⏰ *(14.40 : 15.25)*"
        ),
        "sr": (
            "*Среда*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ Черчение 📏 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Информатика 💻 *(10.55 : 11.40)*\n"
            "5️⃣ Иностранный 🌍 *(11.55 : 12.40)*\n"
            "6️⃣ Физика ⚡ *(12.50 : 13.35)*"
        ),
        "cht": (
            "*Четверг*\n"
            "1️⃣ Русский 🇷🇺 *(08.00 : 08.45)*\n"
            "2️⃣ Химия 🧪 *(08.55 : 09.40)*\n"
            "3️⃣ История 🏛 *(09.55 : 10.40)*\n"
            "4️⃣ Физкультура 🏃 *(10.55 : 11.40)*\n"
            "5️⃣ Белорусский 🇧🇾 *(11.55 : 12.40)*\n"
            "6️⃣ Рус. лит 📚 *(12.50 : 13.35)*\n"
            "7️⃣ Русский 🇷🇺 *(13.45 : 14.30)*\n"
            "8️⃣ Инф. час ⏰ *(14.40 : 15.25)*"
        ),
        "pt": (
            "*Пятница*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ Физкультура 🏃 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Общество ⚖️ *(10.55 : 11.40)*\n"
            "5️⃣ Доприз/Мед 🪖 *(11.55 : 12.40)*\n"
            "6️⃣ Русский 🇷🇺 *(12.50 : 13.35)*"
        ),
    },
    "base": {
        "title": "📘 База",
        "pn": (
            "*Понедельник*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ География 🌍 *(08.55 : 09.40)*\n"
            "5️⃣ Физкультура 🏃 *(11.55 : 12.40)*\n"
            "6️⃣ Русский 🇷🇺 *(12.50 : 13.35)*\n"
            "7️⃣ Химия 🧪 *(13.45 : 14.30)*"
        ),
        "vt": (
            "*Вторник*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ История 🏛 *(08.55 : 09.40)*\n"
            "3️⃣ Физика ⚡ *(09.55 : 10.40)*\n"
            "4️⃣ Иностранный 🌍 *(10.55 : 11.40)*\n"
            "5️⃣ Информатика 💻 *(11.55 : 12.40)*\n"
            "6️⃣ Белорусский 🇧🇾 *(12.50 : 13.35)*\n"
            "7️⃣ Бел. лит 📚 *(13.45 : 14.30)*\n"
            "8️⃣ Классный час ⏰ *(14.40 : 15.25)*"
        ),
        "sr": (
            "*Среда*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ Черчение 📏 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Химия 🧪 *(10.55 : 11.40)*\n"
            "5️⃣ Иностранный 🌍 *(11.55 : 12.40)*\n"
            "6️⃣ Физика ⚡ *(12.50 : 13.35)*"
        ),
        "cht": (
            "*Четверг*\n"
            "1️⃣ Русский 🇷🇺 *(08.00 : 08.45)*\n"
            "3️⃣ История 🏛 *(09.55 : 10.40)*\n"
            "4️⃣ Физкультура 🏃 *(10.55 : 11.40)*\n"
            "5️⃣ Белорусский 🇧🇾 *(11.55 : 12.40)*\n"
            "6️⃣ Рус. лит 📚 *(12.50 : 13.35)*\n"
            "7️⃣ Русский 🇷🇺 *(13.45 : 14.30)*\n"
            "8️⃣ Инф. час ⏰ *(14.40 : 15.25)*"
        ),
        "pt": (
            "*Пятница*\n"
            "1️⃣ Алгебра ➗ *(08.00 : 08.45)*\n"
            "2️⃣ Физкультура 🏃 *(08.55 : 09.40)*\n"
            "3️⃣ Биология 🧬 *(09.55 : 10.40)*\n"
            "4️⃣ Общество ⚖️ *(10.55 : 11.40)*\n"
            "5️⃣ Доприз/Мед 🪖 *(11.55 : 12.40)*"
        ),
    },
}

# ================== СТОЛОВАЯ ==================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
group_data = {}
locks = {}

def get_lock(chat_id):
    if chat_id not in locks:
        locks[chat_id] = Lock()
    return locks[chat_id]

def safe_name(text):
    text = text or "chat"
    text = re.sub(r'[\\/:*?"<>|]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text[:30]

def get_file(chat_id, chat_title):
    return os.path.join(DATA_DIR, f"stolovaya_{safe_name(chat_title)}_{chat_id}.json")

def load_data(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_chat_state(chat_id, chat_title):
    path = get_file(chat_id, chat_title)
    data = load_data(path)
    if data.get("date") == date.today().isoformat():
        return {
            "votes": data.get("votes", {}),
            "last_vote_time": data.get("last_vote_time", {}),
            "poll_message_id": data.get("poll_message_id"),
            "results_message_id": data.get("results_message_id"),
        }
    return {"votes": {}, "last_vote_time": {}, "poll_message_id": None, "results_message_id": None}

def save_chat_state(chat_id, chat_title, state):
    save_data(
        get_file(chat_id, chat_title),
        {**state, "chat_id": chat_id, "chat_title": chat_title, "date": date.today().isoformat()},
    )

# ================== МЕНЮ ==================
MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📅 Расписание", callback_data="menu_schedule")],
    [InlineKeyboardButton("🍽 Столовая", callback_data="menu_stolovaya")],
    [InlineKeyboardButton("🧹 Дежурства", callback_data="duties")],
])

PROFILE_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📐 Математика", callback_data="profile_math")],
    [InlineKeyboardButton("🧪 Химия", callback_data="profile_chem")],
    [InlineKeyboardButton("📘 База", callback_data="profile_base")],
    [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
])

def days_menu(profile):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Пн ", callback_data=f"day*{profile}*pn"),
            InlineKeyboardButton("Вт ", callback_data=f"day*{profile}*vt"),
            InlineKeyboardButton("Ср ", callback_data=f"day*{profile}*sr"),
        ],
        [
            InlineKeyboardButton("Чт ", callback_data=f"day*{profile}*cht"),
            InlineKeyboardButton("Пт ", callback_data=f"day*{profile}*pt"),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main_from_profile")],
    ])

STOL_MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍽 Создать опрос", callback_data="stol_create_poll")],
    [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="stol_show_results")],
    [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
])

STOL_POLL_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🍽 Буду есть", callback_data="stol_eat")],
    [InlineKeyboardButton("🙅 Не буду есть", callback_data="stol_no_eat")],
    [InlineKeyboardButton("🏫 Не буду в школе", callback_data="stol_absent")],
])

DUTIES_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
])

DUTIES_TEXT = (
    "📌 Гардероб / столовая\n\n"
    "Понедельник:\n"
    "1. Акрамова С.\n"
    "2. Рыбарт В.\n"
    "3. Еремеева К.\n"
    "4. Дятлов В.\n\n"
    "Вторник:\n"
    "1. Каверзникова А.\n"
    "2. Иванова А.\n"
    "3. Рыбарт В.\n"
    "4. Овсянник С.\n\n"
    "Среда:\n"
    "1. Зайцева А.\n"
    "2. Комар В.\n"
    "3. Перевозникова А.\n"
    "4. Щербич В.\n\n"
    "Четверг:\n"
    "1. Щигельская В.\n"
    "2. Цмыг А.\n"
    "3. Цмыг Я.\n"
    "4. Овсянник С.\n\n"
    "Пятница:\n"
    "1. Пациенок Д.\n"
    "2. Дубовик А.\n"
    "3. Дятлов В.\n"
    "4. Самойлов В."
)

# ================== ФУНКЦИИ ==================
async def safe_edit(query, text, reply_markup=None, parse_mode=None):
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            return
        raise

def get_results_text(votes):
    eat = []
    no_eat = []
    absent = []
    for v in votes.values():
        name = v["name"]
        if v.get("username"):
            name += f" (@{v['username']})"
        if v["status"] == "eat":
            eat.append(name)
        elif v["status"] == "no_eat":
            no_eat.append(name)
        else:
            absent.append(name)
    tomorrow = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
    return (
        f"📊 Результаты на {tomorrow}\n\n"
        f"🍽 Будут есть ({len(eat)}):\n" + ("\n".join(eat) or "—") + "\n\n"
        f"🙅 Не будут есть ({len(no_eat)}):\n" + ("\n".join(no_eat) or "—") + "\n\n"
        f"🏫 Не придут в школу ({len(absent)}):\n" + ("\n".join(absent) or "—")
    )

async def update_results_robust(bot, chat_id, msg_id, text):
    if not msg_id:
        return False
    for _ in range(8):
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text)
            return True
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.5)
        except BadRequest as e:
            if "not modified" in str(e).lower() or "message to edit not found" in str(e).lower():
                return True
        except Exception as e:
            logger.warning(f"Ошибка обновления результатов: {e}")
            await asyncio.sleep(1.2)
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери раздел:", reply_markup=MAIN_MENU)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return

    await query.answer()

    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    chat_title = chat.title or "Чат"
    user = query.from_user
    uid = str(user.id)

    # Расписание
    if data == "menu_schedule":
        await safe_edit(query, "Выбери профиль:", reply_markup=PROFILE_MENU)
        return

    if data.startswith("profile_"):
        profile = data.split("_")[1]
        await safe_edit(
            query,
            SCHEDULES[profile]["title"],
            reply_markup=days_menu(profile),
            parse_mode="Markdown"
        )
        return

    if data.startswith("day*"):
        _, profile, day = data.split("*")
        await safe_edit(
            query,
            SCHEDULES[profile][day],
            reply_markup=days_menu(profile),
            parse_mode="Markdown"
        )
        return

    if data in ("back_main", "back_main_from_profile"):
        await safe_edit(query, "Выбери раздел:", reply_markup=MAIN_MENU)
        return

    # Дежурства
    if data == "duties":
        await safe_edit(
            query,
            DUTIES_TEXT,
            reply_markup=DUTIES_MENU
        )
        return

    # Столовая
    if data == "menu_stolovaya":
        await safe_edit(query, "Выбери действие:", reply_markup=STOL_MAIN_MENU)
        return

    if data in ("stol_create_poll", "stol_show_results"):
        try:
            await query.message.delete()
        except Exception:
            pass

    async with get_lock(chat_id):
        if chat_id not in group_data:
            group_data[chat_id] = load_chat_state(chat_id, chat_title)
        g = group_data[chat_id]
        now = datetime.utcnow()

        if data == "stol_create_poll":
            g["votes"].clear()
            g["last_vote_time"].clear()
            poll_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="🍽 Опрос на завтра",
                reply_markup=STOL_POLL_MARKUP
            )
            g["poll_message_id"] = poll_msg.message_id
            try:
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=poll_msg.message_id,
                    disable_notification=True
                )
            except Exception as e:
                logger.warning(f"Не удалось закрепить: {e}")

            res_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=get_results_text(g["votes"])
            )
            g["results_message_id"] = res_msg.message_id
            save_chat_state(chat_id, chat_title, g)
            return

        if data in ("stol_eat", "stol_no_eat", "stol_absent"):
            status_map = {"stol_eat": "eat", "stol_no_eat": "no_eat", "stol_absent": "absent"}
            status = status_map[data]
            g["votes"][uid] = {
                "name": user.first_name or "Без имени",
                "username": user.username,
                "status": status
            }
            g["last_vote_time"][uid] = now.isoformat()

            if g.get("results_message_id"):
                new_text = get_results_text(g["votes"])
                await update_results_robust(context.bot, chat_id, g["results_message_id"], new_text)

            save_chat_state(chat_id, chat_title, g)
            await query.answer("Голос учтён ✓")
            return

        if data == "stol_show_results":
            await context.bot.send_message(
                chat_id=chat_id,
                text=get_results_text(g["votes"])
            )
            return

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Ошибка в обработчике:", exc_info=context.error)

# ================== ЗАПУСК ==================
async def main():
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .rate_limiter(AIORateLimiter())
        .job_queue(None)                # отключаем JobQueue полностью
        .concurrent_updates(4)          # параллельная обработка
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(callback))
    application.add_error_handler(error_handler)

    print("Бот запущен")

    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        poll_interval=0.5,
        timeout=20,
        allowed_updates=Update.ALL_TYPES,
    )

    # Держим процесс живым
    await asyncio.Event().wait()

    # При остановке
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nБот остановлен (Ctrl+C)")
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
