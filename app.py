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
    result = response.json()
    print("TELEGRAM:", method, result, flush=True)
    return result


PRODUCTS = {
    "buy_100": {
        "title": "1–2 вопроса",
        "description": "Расклад Таро на 1–2 вопроса",
        "amount": 100
    },
    "buy_250": {
        "title": "Небольшой расклад",
        "description": "Небольшой расклад Таро на 3–5 вопросов",
        "amount": 250
    },
    "buy_500": {
        "title": "Большой расклад",
        "description": "Большой расклад с разбором всей ситуации",
        "amount": 500
    },
    "buy_1000": {
        "title": "Полный разбор ситуации",
        "description": "Полный разбор ситуации — любое количество вопросов с моей стороны",
        "amount": 1000
    }
}


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    # Сообщения
    message = update.get("message", {})

    if message:
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        # Успешная оплата
        successful_payment = message.get("successful_payment")

        if successful_payment and chat_id:
            amount = successful_payment.get("total_amount")

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    f"Оплата {amount} ⭐ получена!\n\n"
                    "Спасибо за оплату ❤️\n\n"
                    "Теперь пришли свой вопрос и подробно опиши ситуацию.\n"
                    "Если расклад про отношения — напиши имена и немного контекста."
                )
            })

            return "ok", 200

        # /start
        if chat_id and text.startswith("/start"):
            tg("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    "Привет! Я бот для оплаты раскладов Таро ⭐\n\n"
                    "Выбери нужный формат:"
                ),
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "1–2 вопроса — 100 ⭐",
                                "callback_data": "buy_100"
                            }
                        ],
                        [
                            {
                                "text": "Небольшой расклад 3–5 вопросов — 250 ⭐",
                                "callback_data": "buy_250"
                            }
                        ],
                        [
                            {
                                "text": "Большой расклад — 500 ⭐",
                                "callback_data": "buy_500"
                            }
                        ],
                        [
                            {
                                "text": "Полный разбор ситуации — 1000 ⭐",
                                "callback_data": "buy_1000"
                            }
                        ]
                    ]
                }
            })

    # Нажатие кнопки
    callback = update.get("callback_query")

    if callback:
        callback_id = callback.get("id")
        chat_id = callback.get("message", {}).get("chat", {}).get("id")
        product_id = callback.get("data")

        tg("answerCallbackQuery", {
            "callback_query_id": callback_id
        })

        product = PRODUCTS.get(product_id)

        if product and chat_id:
            tg("sendInvoice", {
                "chat_id": chat_id,
                "title": product["title"],
                "description": product["description"],
                "payload": product_id,
                "currency": "XTR",
                "prices": [
                    {
                        "label": product["title"],
                        "amount": product["amount"]
                    }
                ]
            })

    # Telegram запрашивает подтверждение перед оплатой
    pre_checkout_query = update.get("pre_checkout_query")

    if pre_checkout_query:
        tg("answerPreCheckoutQuery", {
            "pre_checkout_query_id": pre_checkout_query["id"],
            "ok": True
        })

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
