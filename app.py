import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"

def tg(method, data):
    return requests.post(f"{API}/{method}", json=data, timeout=30).json()

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    if "pre_checkout_query" in update:
        query = update["pre_checkout_query"]
        tg("answerPreCheckoutQuery", {
            "pre_checkout_query_id": query["id"],
            "ok": True
        })
        return "ok", 200

    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id and text.startswith("/pay"):
        try:
            amount = int(text.split()[1])

            if amount <= 0:
                raise ValueError

            result = tg("createInvoiceLink", {
                "title": "Tarot reading",
                "description": "Payment for a Tarot reading",
                "payload": f"tarot_{amount}",
                "currency": "XTR",
                "prices": [
                    {
                        "label": "Tarot reading",
                        "amount": amount
                    }
                ]
            })

            if result.get("ok"):
                tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": f"Счёт на {amount} ⭐:\n{result['result']}"
                })
            else:
                tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "Не получилось создать счёт."
                })

        except (ValueError, IndexError):
            tg("sendMessage", {
                "chat_id": chat_id,
                "text": "Напиши, например: /pay 500"
            })

    return "ok", 200
