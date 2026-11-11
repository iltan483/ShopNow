
from flask import Flask, jsonify
import requests
import threading
import os

app = Flask(__name__)

SERVERS = [
    {
        "name": "Servidor 1",
        "url": "http://127.0.0.1:5001",
        "active_requests": 0
    },
    {
        "name": "Servidor 2",
        "url": "http://127.0.0.1:5002",
        "active_requests": 0
    },
    {
        "name": "Servidor 3",
        "url": "http://127.0.0.1:5003",
        "active_requests": 0
    }
]

ALGORITHM = os.getenv("ALGORITHM", "round_robin")
current_server = 0
lock = threading.Lock()


def get_available_servers():
    available = []

    for server in SERVERS:
        try:
            response = requests.get(
                server["url"] + "/health",
                timeout=1
            )

            if response.status_code == 200:
                available.append(server)

        except requests.RequestException:
            continue

    return available


def get_next_server():
    global current_server

    available = get_available_servers()

    if not available:
        return None

    with lock:
        if ALGORITHM == "least_connections":
            server = min(
                available,
                key=lambda s: s["active_requests"]
            )
        else:
            server = None

            for offset in range(len(SERVERS)):
                index = (current_server + offset) % len(SERVERS)
                candidate = SERVERS[index]

                if candidate in available:
                    server = candidate
                    current_server = (index + 1) % len(SERVERS)
                    break

        if server:
            server["active_requests"] += 1

        return server


@app.route("/")
def home():
    server = get_next_server()

    if server is None:
        return jsonify({"erro": "Nenhum servidor disponível"}), 503

    try:
        response = requests.get(server["url"], timeout=5)

        return jsonify({
            "servidor_atendido": server["name"],
            "algoritmo": ALGORITHM,
            "resposta": response.json()
        }), response.status_code

    except requests.RequestException:
        return jsonify({"erro": "Falha ao acessar o servidor"}), 503

    finally:
        with lock:
            server["active_requests"] -= 1


@app.route("/lb-status")
def status():
    servidores = []

    for server in SERVERS:
        try:
            response = requests.get(
                server["url"] + "/health",
                timeout=1
            )
            online = response.status_code == 200

        except requests.RequestException:
            online = False

        with lock:
            active = server["active_requests"]

        servidores.append({
            "nome": server["name"],
            "status": "online" if online else "offline",
            "requisicoes_ativas": active
        })

    return jsonify({
        "algoritmo": ALGORITHM,
        "servidores": servidores
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, threaded=True, debug=False)
