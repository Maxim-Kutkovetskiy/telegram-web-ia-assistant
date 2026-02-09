import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from functions import (
    validate_booking_data,
    add_booking_to_sheet,
    send_telegram_notification,
    ask_openai_assistant,
    save_booking_data,
    submit_tool_outputs,
    normalize_booking_datetime,
    build_booking_notification
)
import threading
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
import asyncio
import json

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Flask(__name__)
CORS(app)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "msg": "pong"})

@app.route('/api/booking', methods=['POST'])
def api_booking():
    data = request.json
    is_valid, err = validate_booking_data(data)
    if not is_valid:
        return jsonify({"success": False, "error": err}), 400
    result = add_booking_to_sheet(data)
    if result["success"]:
        msg = build_booking_notification(data, "сайта")
        send_telegram_notification(msg)
        return jsonify({"success": True, "msg": "Заявка сохранена!"})
    else:
        return jsonify({"success": False, "error": result["error"]}), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    # FIXME: Эта реализация блокирует Flask до завершения всех запросов к OpenAI assistant!
    #         Для production требуется вынести agent loop в отдельный воркер или переключиться на асинхронный движок (Quart, FastAPI + httpx).
    data = request.json or {}
    user_id = data.get('user_id')
    msg = data.get('message', '')
    thread_id = data.get('thread_id')
    result = ask_openai_assistant(msg, thread_id)
    if result.get('status') == 'error':
        return jsonify({"success": False, "error": result.get('error', 'Ассистент не отвечает')})
    # Agent-loop (for MVP only!)
    while result.get("status") == "requires_action":
        tool_outputs = []
        for call in result.get("tool_calls", []):
            if call["function"]["name"] == "save_booking_data":
                args = json.loads(call["function"]["arguments"])
                sheet_result = save_booking_data(**args)
                tool_outputs.append({
                    "tool_call_id": call["id"],
                    "output": json.dumps(sheet_result)
                })
        submit_resp = submit_tool_outputs(result["thread_id"], result["run_id"], tool_outputs)
        result = ask_openai_assistant("", result["thread_id"])
        # FIXME: В таком цикле весь сервер зависает! Production solution — только через async FSM.
    return jsonify({
        "success": True,
        "reply": result.get("reply"),
        "thread_id": result.get("thread_id"),
        "history": result.get("history")
    })

CHOOSING, FASTBOOK, F_NAME, F_PHONE, F_SERVICE, F_DATE, F_MASTER, F_COMMENT = range(8)
CONSULT_THREAD = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Быстрая запись", "Консультация"]]
    await update.message.reply_text(
        "Здравствуйте! Добро пожаловать в салон красоты ArtBeauty. "
        "Чем могу помочь вам сегодня? Рассказать о наших услугах, ценах или хотите записаться на процедуру?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Быстрая запись":
        await update.message.reply_text("Давайте быстро вас запишем! Как вас зовут?", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        context.user_data['booking'] = {}
        return F_NAME
    elif text == "Консультация":
        await update.message.reply_text("Чем могу помочь? Опишите ваш вопрос.", reply_markup=ReplyKeyboardRemove())
        return FASTBOOK
    else:
        await update.message.reply_text("Пожалуйста, выберите одну из опций.")
        return CHOOSING

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data['booking']['name'] = name
    await update.message.reply_text("Ваш телефон?")
    return F_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['booking']['phone'] = phone
    await update.message.reply_text("Какая услуга интересует?")
    return F_SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    context.user_data['booking']['service'] = service
    await update.message.reply_text("На какую дату и время вас записать? Формат: ДД.ММ.ГГГГ ЧЧ:ММ (например, 05.05.2025 14:30)")
    return F_DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text
    ok, normalized = normalize_booking_datetime(date_text)
    if not ok:
        await update.message.reply_text(
            f"Ошибка: {normalized}\nВведите дату ещё раз в формате ДД.ММ.ГГГГ ЧЧ:ММ."
        )
        return F_DATE
    context.user_data['booking']['date'] = normalized
    context.user_data['booking']['datetime'] = normalized
    await update.message.reply_text("К какому мастеру вы хотите записаться? (или пропустите)")
    return F_MASTER

async def get_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    master = update.message.text
    context.user_data['booking']['master'] = master
    await update.message.reply_text("Комментарий к заявке? (или пропустите)")
    return F_COMMENT

async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text
    booking = context.user_data.get('booking', {})
    booking['comment'] = comment
    booking['source'] = 'Telegram'
    is_valid, err = validate_booking_data(booking)
    if not is_valid:
        await update.message.reply_text(f"Ошибка: {err}")
        return ConversationHandler.END
    result = add_booking_to_sheet(booking)
    if result["success"]:
        msg = build_booking_notification(booking, "Telegram бота")
        send_telegram_notification(msg)
        await update.message.reply_text("Спасибо! Ваша заявка принята и передана админу.")
    else:
        await update.message.reply_text("Ошибка при записи заявки. Попробуйте позже.")
    # вернуть пользователя к выбору действия
    keyboard = [["Быстрая запись", "Консультация"]]
    await update.message.reply_text(
        "Хотите сделать ещё что-то?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING

# --- Консультация с Function Calling Agent loop ---
async def consult_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXME: Блокирующий agent loop внутри асинхронного хендлера!
    # Для production state-machine реализовать агентский цикл с промежуточными переходами через callback/context.
    user_id = str(update.message.from_user.id)
    msg = update.message.text
    thread_id = CONSULT_THREAD.get(user_id)
    answer = ask_openai_assistant(msg, thread_id)
    if answer.get('status') == 'error':
        reply = answer.get('error', 'Ассистент не отвечает.')
        await update.message.reply_text(reply)
        return FASTBOOK
    while answer.get("status") == "requires_action":
        tool_outputs = []
        for call in answer.get("tool_calls", []):
            if call["function"]["name"] == "save_booking_data":
                args = json.loads(call["function"]["arguments"])
                sheet_result = save_booking_data(**args)
                tool_outputs.append({
                    "tool_call_id": call["id"],
                    "output": json.dumps(sheet_result)
                })
        submit_resp = submit_tool_outputs(answer["thread_id"], answer["run_id"], tool_outputs)
        answer = ask_openai_assistant("", answer["thread_id"])
        # FIXME: Это блокирует бота внутри event-loop! Виден только на тестах. Для продакшена — FSM!
    CONSULT_THREAD[user_id] = answer.get("thread_id")
    reply = answer.get("reply")
    if not reply:
        reply = (
            "Готово! Ваша заявка сформирована. "
            "Если остались вопросы — задайте их, пожалуйста."
        )
    await update.message.reply_text(
        reply + "\n\nХотите записаться на услугу? Просто нажмите /start и выберите 'Быстрая запись'."
    )
    return FASTBOOK

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Диалог прерван. Вы можете начать сначала с /start', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def run_tg_bot():
    async def post_init(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Начать диалог")
        ])

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            F_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            F_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            F_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            F_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_master)],
            F_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            FASTBOOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, consult_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('cancel', cancel))
    # БЕЗ asyncio.run(...)! run_polling сам заботится о loop.
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=int(os.getenv("PORT", 5000)),
            debug=False,  # важно: reloader выключен, иначе сигнал в отдельном потоке упадет
            use_reloader=False
        ),
        daemon=True
    ).start()
    run_tg_bot()
