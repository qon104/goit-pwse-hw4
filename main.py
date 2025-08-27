import json
import os
import socket
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_from_directory

# --- Конфигурация ---
HTTP_PORT = 3000
SOCKET_PORT = 5000
STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")

# Создаём директорию storage и файл data.json, если их нет
os.makedirs(STORAGE_DIR, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# --- Flask-приложение ---
app = Flask(__name__, template_folder="templates", static_folder="static")

# --- Главная страница ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Страница с формой ---
@app.route("/message", methods=["GET", "POST"])
def message():
    if request.method == "POST":
        username = request.form.get("username")
        message = request.form.get("message")

        if username and message:
            data = f"{username}|{message}"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data.encode("utf-8"), ("127.0.0.1", SOCKET_PORT))
            sock.close()

        return redirect("/message")

    return render_template("message.html")

# --- Отдача статических файлов (style.css, logo.png) ---
@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

# --- Обработка 404 ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"), 404

# --- UDP Socket-сервер ---
def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", SOCKET_PORT))

    while True:
        data, _ = sock.recvfrom(1024)
        data = data.decode("utf-8")
        username, message = data.split("|")

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)

        all_data[str(datetime.now())] = {"username": username, "message": message}

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

# --- Запуск HTTP и Socket серверов ---
if __name__ == "__main__":
    socket_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_thread.start()

    app.run(host="127.0.0.1", port=HTTP_PORT)
