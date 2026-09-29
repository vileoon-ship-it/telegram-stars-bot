import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"


def tg(method, data):
    response = requests.post(
        f"{API}/{method}",
        json=data,
        timeout=15
    )
    return response.json()


PRODUCTS = {
    "buy_100": {
        "title": "1 вопрос",
        "description": "Оплата одного вопроса",
        "amount": 100
    },
    "buy_250": {
        "title": "Небольшой расклад",
        "description": "Оплата небольшого расклада",
        "amount": 250
    },
    "buy_500": {
        "title": "Большой расклад",
        "description": "Оплата большого расклада",
        "amount": 500
    },
    "buy_1000": {
        "title": "Очень большой подробный расклад",
        "description": "Оплата очень большого подробного расклада",
        "amount": 1000
    }
}


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    # 1. Telegram проверяет оплату перед списанием Stars
    if "pre_checkout_query" in update:
        query = update["pre_checkout_query"]

        tg("answerPreCheckoutQuery", {
            "pre_checkout_query_id": query["id"],
            "ok": True
        })

        return "ok", 200

    # 2. Нажатие на кнопку с раскладом
    if "callback_query" in update:
        callback = update["callback_query"]

        callback_id = callback["id"]
        data = callback.get("data", "")
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")

        # Убираем загрузку с нажатой кнопки
        tg("answerCallbackQuery", {
            "callback_query_id": callback_id
        })

        product = PRODUCTS.get(data)

        if product and chat_id:
            tg("sendInvoice", {
                "chat_id": chat_id,
                "title": product["title"],
                "description": product["description"],
                "payload": data,
                "provider_token": "",
                "currency": "XTR",
                "prices": [
                    {
                        "label": product["title"],
                        "amount": product["amount"]
                    }
                ]
            })

        return "ok", 200

    # 3. Обычные сообщения
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return "ok", 200

    # 4. Telegram сообщает об успешной оплате
    if "successful_payment" in message:
        payment = message["successful_payment"]
        amount = payment.get("total_amount")

        tg("sendMessage", {
            "chat_id": chat_id,
            "text": (
                f"Оплата успешно получена — {amount} ⭐️\n\n"
                "Спасибо за оплату ❤️\n"
                "Теперь можешь написать мне для проведения расклада."
            )
        })

        return "ok", 200

    # 5. Команда /start
    if text.startswith("/start"):
        tg("sendMessage", {
            "chat_id": chat_id,
            "text": (
                "Привет ❤️\n\n"
                "Здесь ты можешь оплатить расклад через Telegram Stars ⭐️\n\n"
                "Выбери нужный вариант:"
            ),
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "1 вопрос — 100 ⭐️",
                            "callback_data": "buy_100"
                        }
                    ],
                    [
                        {
                            "text": "Небольшой расклад — 250 ⭐️",
                            "callback_data": "buy_250"
                        }
                    ],
                    [
                        {
                            "text": "Большой расклад — 500 ⭐️",
                            "callback_data": "buy_500"
                        }
                    ],
                    [
                        {
                            "text": "Очень большой подробный — 1000 ⭐️",
                            "callback_data": "buy_1000"
                        }
                    ]
                ]
            }
        })

        return "ok", 200

    return "ok", 200
