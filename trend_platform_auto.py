import sqlite3
import re
import requests
import threading
import time
import os
from datetime import datetime
from flask import Flask, jsonify, render_template_string

# --- 1. Сразу создаем приложение Flask ---
app = Flask(__name__)

# --- 2. Настройка БД и констант ---
DB = "trend_platform.db"
SCAN_INTERVAL = 3600 

def init_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS ideas(id INTEGER PRIMARY KEY, topic TEXT UNIQUE, score INTEGER, source TEXT, created TEXT)')
    conn.commit()
    return conn

db = init_db()
cur = db.cursor()

# --- 3. Функции бота ---
def save(topic, source):
    try:
        score = len(topic) // 2 
        cur.execute("INSERT OR IGNORE INTO ideas(topic,score,source,created) VALUES(?,?,?,?)",
                    (topic, score, source, str(datetime.now())))
        db.commit()
    except Exception as e:
        print(f"Error saving: {e}")

def reddit():
    try:
        r = requests.get("https://api.reddit.com/r/popular", headers={"User-Agent": "bot"}, timeout=10)
        return [post["data"]["title"] for post in r.json()["data"]["children"]]
    except: return []

def news():
    try:
        r = requests.get("https://news.google.com/rss", timeout=10)
        return re.findall("<title>(.*?)</title>", r.text)[1:20]
    except: return []

def scan():
    for t in reddit(): save(t, "reddit")
    for t in news(): save(t, "news")

def auto_scan():
    while True:
        scan()
        time.sleep(SCAN_INTERVAL)

# --- 4. Запуск потока сканирования ---
threading.Thread(target=auto_scan, daemon=True).start()

# --- 5. Роуты Flask ---
@app.route("/")
def home():
    cur.execute("SELECT topic, score FROM ideas ORDER BY score DESC LIMIT 20")
    topics = cur.fetchall()
    return render_template_string("<h1>Trends</h1><ul>{% for t in topics %}<li>{{t[0]}} ({{t[1]}})</li>{% endfor %}</ul>", topics=topics)

# --- 6. Запуск сервера ---
if __name__ == "__main__":
    # Render использует переменную PORT, если её нет — используем 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

