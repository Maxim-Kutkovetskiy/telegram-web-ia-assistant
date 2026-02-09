#!/usr/bin/env python3
"""
Следит за локальным ngrok (порт 4040) и обновляет конфигурационный JSON
актуальным публичным https-URL. Подходит для локального тестирования
виджета Тильды, который читает apiBase из этого JSON.
"""

import json
import os
import time
import requests
from dotenv import load_dotenv

# загружаем переменные окружения из .env
load_dotenv()

NGROK_API = "http://127.0.0.1:4040/api/tunnels"
# JSONBIN: URL вашего bin'а и master key из окружения
CONFIG_URL = "https://api.jsonbin.io/v3/b/6927156aae596e708f725703"
JSONBIN_MASTER_KEY = os.getenv("JSONBIN_MASTER_KEY")
POLL_INTERVAL = 10  # секунд


def get_https_tunnel():
    resp = requests.get(NGROK_API, timeout=5)
    resp.raise_for_status()
    tunnels = resp.json().get("tunnels", [])
    for tunnel in tunnels:
        if tunnel.get("proto") == "https":
            return tunnel["public_url"].rstrip("/")
    raise RuntimeError("https-туннель ngrok не найден. Убедитесь, что ngrok запущен.")


def update_config(api_base):
    payload = {"apiBase": api_base}
    headers = {
        "Content-Type": "application/json",
        "X-Bin-Versioning": "false",
    }
    if JSONBIN_MASTER_KEY:
        headers["X-Master-Key"] = JSONBIN_MASTER_KEY
    resp = requests.put(CONFIG_URL, headers=headers, data=json.dumps(payload), timeout=5)
    print(f"[sync_ngrok] PUT {CONFIG_URL} -> {resp.status_code}")
    print(f"[sync_ngrok] Response: {resp.text}")
    resp.raise_for_status()
    print(f"[sync_ngrok] Конфиг обновлён: {api_base}")


def main():
    last_url = None
    while True:
        try:
            current = get_https_tunnel()
            if current != last_url:
                update_config(current)
                last_url = current
        except Exception as err:
            print(f"[sync_ngrok] Ошибка: {err}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

