# 🌐 Beauty Salon AI Assistant — Telegram & Website Bot

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.2-green?logo=flask)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)
![OpenAI](https://img.shields.io/badge/OpenAI-Assistant-orange?logo=openai)
![Google Sheets](https://img.shields.io/badge/Google-Sheets-darkgreen?logo=googlesheets)

> Интеллектуальный ассистент для салона красоты с Telegram-ботом и веб-интерфейсом

[Демонстрация](#-демонстрация) • [Возможности](#-возможности) • [Быстрый старт](#-быстрый-старт) • [Установка](#-установка) • [Деплой](#-деплой-на-сервер) • [Архитектура](#-архитектура)

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Демонстрация](#-демонстрация)
- [Архитектура](#-архитектура)
- [Технологии](#-технологии)
- [Структура проекта](#-структура-проекта)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Локальная разработка](#-локальная-разработка)
- [Деплой на сервер](#-деплой-на-сервер)
- [Конфигурация](#-конфигурация)
- [API Reference](#-api-reference)
- [Безопасность](#-безопасность)
- [Решение проблем](#-решение-проблем)
- [Дорожная карта](#-дорожная-карта)


---

## 🎯 О проекте

**Beauty Salon AI Assistant** — это многофункциональная система для автоматизации работы салона красоты. Проект объединяет:

- **Telegram-бота** для общения с клиентами
- **Веб-API** для приема заявок с сайта
- **AI-ассистента** на базе OpenAI для интеллектуальной обработки запросов

### ✨ Ключевые преимущества

| | Преимущество | Описание |
|---|---|---|
| 🤖 | **Умный ассистент** | OpenAI Assistant с базой знаний о салоне |
| 📱 | **Два канала связи** | Telegram и веб-сайт |
| 📊 | **Единая база** | Все заявки в Google Sheets |
| ⚡ | **Автоматизация** | Авто-запись, уведомления, синхронизация |
| 🔌 | **Интеграции** | Ngrok, JSONBin, Google APIs |

---

## ✨ Возможности

- 💬 Консультация клиентов через AI-ассистента (Telegram и веб-сайт)
- 📝 Быстрая запись на услуги через диалог с ботом
- 📨 Приём заявок с веб-сайта через REST API
- 📊 Автоматическое сохранение данных в Google Sheets
- 🔔 Мгновенные уведомления администратору о новых заявках
- 🌐 Синхронизация публичного URL через Ngrok + JSONBin
- 🧠 Контекстные диалоги с поддержкой истории (OpenAI Threads)

---

## 🖥️ Демонстрация

![Описание файла](https://drive.google.com/uc?export=view&id=1OCE3l4lKgMQYujeYJ8lR8FzeCh9sIh__)
<div align="center">
  <img src="https://via.placeholder.com/300x600/0088cc/ffffff?text=Telegram+Bot+Demo" alt="Telegram Bot Demo" width="300">
  <p><em>Стартовое меню бота с кнопками «Быстрая запись» и «Консультация»</em></p>
</div>

---

## 🏗️ Архитектура

Проект построен по модульной архитектуре с чётким разделением ответственности.
![Описание файла](https://drive.google.com/uc?export=view&id=1whik210F16I40G3eZfl-MPp6ZfW3cyms)
### Основные компоненты

| Компонент | Назначение |
|---|---|
| `main.py` | Ядро системы (Flask + Telegram Bot) |
| `functions.py` | Бизнес-логика и утилиты |
| `sync_ngrok_url.py` | Синхронизация публичных URL |
| База знаний | FAQ салона в JSON-формате |
| Конфигурация | `.env` файл с настройками |

### Поток данных
Клиент → [Telegram / Website] → Flask API → Валидация → Google Sheets → Уведомление админу → Ответ клиенту

text


---

## 🛠️ Технологии

| Технология | Назначение | Версия |
|---|---|---|
| Python | Основной язык | 3.9+ |
| Flask | Веб-фреймворк | 3.0.2 |
| Telegram API | Бот-платформа | python-telegram-bot 20.6 |
| OpenAI Assistant | AI-ассистент | openai >= 1.35.0 |
| Google Sheets API | База данных | google-api-client 2.118.0 |
| Ngrok | Туннелирование | — |

---

## 📁 Структура проекта
```
telegram-web-ia-assistant/
│
├── main.py # Основное приложение (Flask + Telegram Bot)
├── functions.py # Бизнес-логика и утилиты
├── sync_ngrok_url.py # Синхронизация Ngrok URL
├── data/
│ ├── knowledge.txt # База знаний (FAQ)
│ ├── Промпт.txt # Промпт для OpenAI Assistant
│ └── OpenAI Function Calling.txt # Схема функции сохранения
├── requirements.txt # Зависимости Python
├── .env.example # Пример конфигурации
├── .gitignore # Игнорируемые файлы Git
├── credentials.json # Google Service Account (НЕ в репозитории!)
└── README.md # Документация
```



---

## ⚡ Быстрый старт

### Вариант A: Локальный запуск (разработка)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Maxim-Kutkovetskiy/telegram-web-ia-assistant.git
cd telegram-web-ia-assistant

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Настройте конфигурацию
cp .env.example .env
# Отредактируйте .env файл, добавив ваши ключи

# 4. Получите Google Service Account ключ и сохраните как credentials.json

# 5. Запустите приложение
python main.py
Вариант B: Запуск с публичным доступом (для тестирования)
Bash

# 1. Запустите основное приложение
python main.py

# 2. В отдельном терминале запустите Ngrok
ngrok http 5000

# 3. В третьем терминале запустите синхронизатор
python sync_ngrok_url.py
```
## 💻 Установка
```
Предварительные требования
Python 3.9+ и pip
Telegram Bot Token (от @BotFather)
OpenAI API Key (от platform.openai.com)
Google Service Account (для Google Sheets API)
Ngrok Account (для публичного доступа, опционально)
```
### Пошаговая установка
1. Настройка окружения
```Bash
git clone https://github.com/Maxim-Kutkovetskiy/telegram-web-ia-assistant.git
cd telegram-web-ia-assistant
python -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows
```
2. Установка зависимостей
```Bash

pip install -r requirements.txt
```
3. Конфигурация
```Bash
Создайте .env на основе .env.example:

env

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_ASSISTANT_ID=asst_your_assistant_id
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_EMAIL=your_service_account_email
NGROK_AUTHTOKEN=your_ngrok_authtoken
JSONBIN_MASTER_KEY=your_jsonbin_master_key
FLASK_SECRET_KEY=your_secret_key_here
BASE_URL=http://localhost:5000
TIMEZONE=Europe/Moscow
```
4. Настройка Google Sheets
```
Создайте Google Cloud Project.
Включите Google Sheets API.
Создайте Service Account и скачайте credentials.json.
Поделитесь Google Sheet с email сервисного аккаунта.
```
5. Настройка OpenAI Assistant
```
Создайте Assistant в OpenAI Dashboard.
Добавьте функцию save_booking_data.
Загрузите базу знаний (knowledge.txt).
Настройте промпт (Промпт.txt).
Скопируйте Assistant ID в .env.
```
## 🖥️ Локальная разработка
Структура запуска
```Bash
# 1. Только локальная разработка
python main.py

# 2. Разработка с публичным доступом
python main.py              # Терминал 1
ngrok http 5000             # Терминал 2
python sync_ngrok_url.py    # Терминал 3

# 3. Только API-тестирование
python -m pytest tests/                   # Запуск тестов
curl http://localhost:5000/ping           # Проверка API
```
## ☁️ Деплой на сервер
```Bash
Вариант A: VPS (Ubuntu / Debian)

# 1. Подготовка сервера
ssh user@your-server-ip
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git nginx -y
```
### 2. Клонирование и настройка
```Bash
cd /var/www
git clone https://github.com/Maxim-Kutkovetskiy/telegram-web-ia-assistant.git
cd telegram-web-ia-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### 3. Настройка systemd службы
```Bash
sudo nano /etc/systemd/system/beauty-bot.service
Содержимое beauty-bot.service:

ini

[Unit]
Description=Beauty Salon Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/telegram-web-ia-assistant
Environment="PATH=/var/www/telegram-web-ia-assistant/venv/bin"
ExecStart=/var/www/telegram-web-ia-assistant/venv/bin/python /var/www/telegram-web-ia-assistant/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
Bash

# 4. Запуск службы
sudo systemctl daemon-reload
sudo systemctl enable beauty-bot
sudo systemctl start beauty-bot
sudo systemctl status beauty-bot
```
## ⚙️ Конфигурация
### Основные настройки (`.env`)

| Переменная | Описание | Обязательно | Пример |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | ✅ | `8214874151:AAHMNO...` |
| `OPENAI_API_KEY` | Ключ OpenAI API | ✅ | `sk-proj-...` |
| `OPENAI_ASSISTANT_ID` | ID ассистента OpenAI | ✅ | `asst_OJL4...` |
| `GOOGLE_SHEET_ID` | ID Google Таблицы | ✅ | `1xHTwNBqeMA...` |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | Email сервисного аккаунта | ✅ | `bot@project.iam.gserviceaccount.com` |
| `ADMIN_CHAT_ID` | ID чата для уведомлений | ✅ | `-1003...` |
| `BASE_URL` | Базовый URL приложения | ✅ | `http://localhost:5000` |
| `TIMEZONE` | Часовой пояс | ✅ | `Europe/Moscow` |
| `NGROK_AUTHTOKEN` | Токен Ngrok | ⚠️ | `2B...` |
| `JSONBIN_MASTER_KEY` | Ключ JSONBin | ⚠️ | `$2a$10$...` |
| `FLASK_SECRET_KEY` | Секретный ключ Flask | ✅ | `your-secret-key` |

> ⚠️ — требуется только при использовании публичного доступа через Ngrok
📚 API Reference
```
Flask API Endpoints

GET /ping
Проверка работоспособности сервера.
```
```Bach
Response:


JSON

{
  "status": "ok",
  "msg": "pong"
}
POST /api/booking
Создание новой заявки с веб-сайта.

Request:

JSON

{
  "name": "Иван Иванов",
  "phone": "+79991234567",
  "service": "Стрижка",
  "date": "25.12.2024 14:30",
  "master": "Топ-Стилист",
  "comment": "Хочу подстричься покороче"
}
Response:

JSON

{
  "success": true,
  "msg": "Заявка сохранена!"
}
POST /api/chat
Общение с OpenAI Assistant через API.

Request:

JSON

{
  "user_id": "unique_user_id",
  "message": "Хочу записаться на окрашивание",
  "thread_id": "optional_thread_id"
}
Response:

JSON

{
  "success": true,
  "reply": "Конечно! Давайте запишем вас...",
  "thread_id": "thread_abc123"
}
```

## 🔧 Решение проблем
```
<details> <summary><b>❌ Telegram бот не отвечает</b></summary>
Проблема: Бот не реагирует на команды.

Решение:

Bash

# 1. Проверьте токен
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# 2. Проверьте, запущен ли бот
ps aux | grep python

# 3. Проверьте логи
python main.py 2>&1 | grep -i "error\|exception"

# 4. Убедитесь, что используется polling
# В main.py должно быть: application.run_polling()
</details><details> <summary><b>❌ Ошибка Google Sheets API</b></summary>
Проблема: google.auth.exceptions.DefaultCredentialsError

Решение:

Bash

# 1. Проверьте наличие credentials.json
ls -la credentials.json

# 2. Проверьте доступ к таблице
# Поделитесь таблицей с сервисным аккаунтом:
# bot-telegram-and-the-website@bot-telegram-and-the-website.iam.gserviceaccount.com

# 3. Проверьте GOOGLE_SHEET_ID в .env
</details>
```
## 🗺️ Дорожная карта
```
Версия 1.0 (Текущая)
 [v] Telegram бот с консультациями
 [v] TБыстрая запись через диалог
 [v] Интеграция с OpenAI Assistant
 [v] Веб-API для сайта
 [v] Google Sheets как БД
 [v] Автоматические уведомления
 
Версия 1.1 (Планируется)
 [ ] Панель администратора
 [ ] Календарь записей
 [ ] Напоминания клиентам
 [ ] Система лояльности
 [ ] Экспорт данных в Excel
 
Версия 2.0 (Будущее)
 [ ] Мобильное приложение
 [ ] Система онлайн-оплаты
 [ ] AI-анализ отзывов
 [ ] Интеграция с Instagram / Facebook
 [ ] Система управления персоналом
