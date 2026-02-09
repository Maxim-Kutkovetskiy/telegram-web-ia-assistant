import os
import json
import pytz
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import time

# Загрузка переменных из .env
load_dotenv()

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Проверка наличия credentials.json
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
if not os.path.exists(CREDENTIALS_PATH):
    raise FileNotFoundError(f"credentials.json отсутствует по пути: {CREDENTIALS_PATH}")

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH,
    scopes=SCOPES,
)
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

def normalize_booking_datetime(value):
    """
    Приводит дату/время к формату ДД.ММ.ГГГГ ЧЧ:ММ и проверяет, что дата в будущем.
    Возвращает (True, normalized_str) или (False, error_message).
    """
    if not value:
        return False, "Не заполнено обязательное поле: date/datetime"
    try:
        tz = pytz.timezone(TIMEZONE)
        parsed_naive = datetime.strptime(value.strip(), "%d.%m.%Y %H:%M")
        parsed_dt = tz.localize(parsed_naive)
    except ValueError:
        return False, "Дата должна быть в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 05.05.2025 14:30)"
    now = datetime.now(tz)
    if parsed_dt < now:
        return False, "Укажите дату и время в будущем."
    normalized = parsed_dt.strftime("%d.%m.%Y %H:%M")
    return True, normalized


def validate_booking_data(data):
    """
    Проверяет наличие обязательных полей для заявки и синхронизирует названия
    между разными источниками (сайт, Telegram-бот, OpenAI tools).
    Возвращает (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Некорректные данные заявки."

    # Общие обязательные поля
    for field in ['name', 'phone', 'service']:
        if not data.get(field):
            return False, f"Не заполнено обязательное поле: {field}"

    # Дата/время: допускаем как date, так и datetime
    date_value = data.get('date') or data.get('datetime')
    ok, normalized_date = normalize_booking_datetime(date_value)
    if not ok:
        return False, normalized_date
    data.setdefault('date', normalized_date)
    data.setdefault('datetime', normalized_date)

    # Мастер может приходить как master или master_category — поле не обязательное,
    # но синхронизируем названия, чтобы таблица получала master.
    master_value = data.get('master') or data.get('master_category') or ""
    data.setdefault('master', master_value)
    data.setdefault('master_category', master_value)

    return True, ""

def save_booking_data(name, phone, service, datetime, master_category, comments=None):
    """
    Функция для OpenAI Function Calling и прямого вызова: сохраняет запись в Google Sheets.
    Аргументы строго по схеме ассистента!
    comments может быть пропущенным.
    """
    data = {
        "name": name,
        "phone": phone,
        "service": service,
        "date": datetime,
        "master": master_category,
        "comment": comments if comments is not None else "",
        "source": "OpenAI Assistant"
    }
    # Используем add_booking_to_sheet внутри
    return add_booking_to_sheet(data)

def add_booking_to_sheet(data):
    """
    Добавляет заявку в Google Таблицу. Возвращает dict:
    {"success": True/False, "data":..., "error": ...}
    """
    row = [
        data.get('name', ''),
        data.get('phone', ''),
        data.get('service', ''),
        data.get('date', ''),
        data.get('master', ''),
        data.get('comment', ''),
        data.get('source', ''),
        datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M'),
    ]
    body = {'values': [row]}
    try:
        result = sheet.values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range="A2",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return {"success": True, "data": result, "error": None}
    except Exception as ex:
        print(f"[GoogleSheets] Ошибка при добавлении заявки: {ex}")
        return {"success": False, "data": None, "error": str(ex)}

def send_telegram_notification(text):
    """
    Отправляет уведомление в служебный Telegram-чат. Всегда возвращает dict с ключами success/error.
    """
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN или ADMIN_CHAT_ID не задан"}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    print(f"[Telegram][debug] chat_id={ADMIN_CHAT_ID}")
    payload = {
        'chat_id': ADMIN_CHAT_ID,
        'text': text,
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "error": None}
        else:
            print(f"[Telegram] Ошибка: {resp.status_code} - {resp.text}")
            return {"success": False, "error": resp.text}
    except Exception as ex:
        print(f"[Telegram] Сетевая ошибка: {ex}")
        return {"success": False, "error": str(ex)}


def build_booking_notification(data, source_label="Telegram бота"):
    """
    Формирует текст уведомления о новой заявке.
    """
    tz = pytz.timezone(TIMEZONE)
    now_str = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    return (
        f"🤖 НОВАЯ ЗАЯВКА через {source_label}!\n"
        f"Имя: {data.get('name', '—')}\n"
        f"Телефон: {data.get('phone', '—')}\n"
        f"Услуга: {data.get('service', '—')}\n"
        f"Дата: {data.get('date', '—')}\n"
        f"Мастер: {data.get('master', '—')}\n"
        f"Комментарий: {data.get('comment', '—')}\n"
        f"Время: {now_str}"
    )

def ask_openai_assistant(message, thread_id=None):
    """
    Критические внешние запросы (создание thread, message, run, polling) делаем через try/except.
    При любой ошибке — аккуратный возврат и текст ошибки.
    """
    if not OPENAI_API_KEY or not OPENAI_ASSISTANT_ID:
        return {"status": "error", "error": "OpenAI ключи не заданы."}
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2",
    }
    # 1. Получить или создать thread (только через try)
    try:
        if not thread_id:
            thread_resp = requests.post(
                "https://api.openai.com/v1/threads",
                headers=headers,
                data=json.dumps({}),
                timeout=20
            )
            thread_resp.raise_for_status()
            thread_id = thread_resp.json()["id"]
    except Exception as ex:
        return {"status": "error", "error": f"Ошибка создания thread: {ex}"}
    # 2. Отправить сообщение в thread
    try:
        msg_url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        msg_payload = {"role": "user", "content": message}
        msg_resp = requests.post(msg_url, headers=headers, data=json.dumps(msg_payload), timeout=20)
        msg_resp.raise_for_status()
    except Exception as ex:
        return {"status": "error", "error": f"Ошибка отправки сообщения: {ex}"}
    # 3. Запустить ассистента (run) для thread
    try:
        run_url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
        run_payload = {"assistant_id": OPENAI_ASSISTANT_ID}
        run_resp = requests.post(run_url, headers=headers, data=json.dumps(run_payload), timeout=20)
        run_resp.raise_for_status()
        run_id = run_resp.json()["id"]
    except Exception as ex:
        return {"status": "error", "error": f"Ошибка запуска run: {ex}"}
    # 4. Poll статуса
    status = "in_progress"
    timeout_poll = 60
    poll_url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
    poll_resp = None
    for i in range(timeout_poll):
        try:
            poll_resp = requests.get(poll_url, headers=headers, timeout=20)
            poll_resp.raise_for_status()
            status = poll_resp.json().get("status", "")
            if status in ["completed", "failed", "cancelled", "requires_action"]:
                break
            time.sleep(2)
        except Exception as ex:
            return {"status": "error", "error": f"Ошибка polling run: {ex}"}
    if poll_resp is None:
        return {"status": "error", "error": "Ассистент не дал ответ: polling run не инициализирован."}
    if status == "requires_action":
        run_details = poll_resp.json()
        tool_calls = run_details.get("required_action", {}).get("submit_tool_outputs", {}).get("tool_calls", [])
        return {
            "status": "requires_action",
            "tool_calls": tool_calls,
            "run_id": run_id,
            "thread_id": thread_id
        }
    elif status == "completed":
        # Получить историю сообщений (try-except для robustness)
        try:
            history_url = f"https://api.openai.com/v1/threads/{thread_id}/messages?order=desc&limit=30"
            history_resp = requests.get(history_url, headers=headers, timeout=20)
            history = []
            if history_resp.status_code == 200:
                history_json = history_resp.json()
                for item in reversed(history_json.get('data', [])):
                    role = item.get("role", "user")
                    content = ""
                    try:
                        content = item["content"][0]["text"]["value"]
                    except Exception:
                        content = str(item["content"][0]) if item.get("content") else ""
                    history.append({"role": role, "content": content})
            response_text = "(Нет ответа ассистента)"
            for msg in reversed(history):
                if msg["role"] == "assistant" and msg["content"]:
                    response_text = msg["content"]
                    break
            return {
                "status": "completed",
                "reply": response_text,
                "thread_id": thread_id,
                "history": history
            }
        except Exception as ex:
            return {"status": "error", "error": f"Ошибка получения истории: {ex}"}
    else:
        return {"status": status, "run_id": run_id, "thread_id": thread_id}

def submit_tool_outputs(thread_id, run_id, tool_outputs):
    """
    Отправляет результаты выполнения функций обратно в OpenAI.
    tool_outputs — список словарей с ключами: "tool_call_id", "output"
    """
    if not OPENAI_API_KEY:
        return {"status": "error", "error": "OpenAI ключ не задан."}
    url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}/submit_tool_outputs"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v2",
    }
    payload = {"tool_outputs": tool_outputs}
    run_resp = requests.post(url, headers=headers, data=json.dumps(payload))
    try:
        run_resp.raise_for_status()
        return run_resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Здесь можно добавить функции для получения цен/мастеров/услуг из Google Sheets либо статично

def get_services_list():
    # TODO: Реализовать, если нужна выдача услуг и цен
    return ["Стрижка", "Маникюр", "Педикюр"]

# Аналогично - функции для валидации и обработки входных данных есть смысл добавить по мере необходимости.
