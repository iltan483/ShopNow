
from flask import Flask
import os
import threading
import time

app = Flask(__name__)

INSTANCE_ID = os.getenv("INSTANCE_ID", "Servidor 1")
PORT = int(os.getenv("PORT", 5001))

active_requests = 0
lock = threading.Lock()


@app.before_request
def start_request():
    global active_requests
    with lock:
        active_requests += 1


@app.after_request
def finish_request(response):
    global active_requests
    with lock:
        active_requests -= 1
    return response


@app.route("/")
def home():
    time.sleep(1)

    return {
        "mensagem": "ShopNow funcionando!",
        "servidor": INSTANCE_ID
    }


@app.route("/health")
def health():
    return {
        "status": "online",
        "servidor": INSTANCE_ID
    }


@app.route("/connections")
def connections():
    with lock:
        return {
            "servidor": INSTANCE_ID,
            "conexoes_ativas": active_requests
        }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, threaded=True, debug=False)
