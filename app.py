import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"

waiting_for_amount = set()


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
        "title": "1 вопрос",
        "description": "Небольшой расклад на один конкретный вопрос",
        "amount": 100
    },
    "buy_250": {
        "title": "2–4 вопроса",
        "description": "Ответы на ваши вопросы подробно",
        "amount": 250
    },
    "buy_500": {
        "title": "Расширенный разбор",
        "description": "От 4 вопросов или подробный разбор одной ситуации",
        "amount": 500
    },
    "buy_1000": {
        "title": "Полный разбор",
        "description": "Полностью разбираем ситуацию, количество вопросов не ограничено",
        "amount": 1000
    }
}


@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message", {})

    if message:
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        # Успешная оплата
        successful_payment = message.get("successful_payment")

        if successful_payment and chat_id:
            amount = successful_payment.get("total_amount")

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    f"Оплата {amount} ⭐ получена!\n\n"
                    "Спасибо за оплату ❤️"
                )
            })

            return "ok", 200

        # Команда /start
        if chat_id and text.startswith("/start"):
            waiting_for_amount.discard(chat_id)

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    "🔮 Оплата расклада Таро ⭐\n\n"
                    "Выбери подходящий формат:\n\n"

                    "🤍1 вопрос — 100 ⭐\n"
                    "Небольшой расклад на один конкретный вопрос.\n\n"

                    "🤍2–4 вопроса — 250 ⭐\n"
                    "Ответы на ваши вопросы подробно\n\n"

                    "🤍Расширенный разбор — 500 ⭐\n"
                    "От 4 вопросов или подробный разбор одной ситуации.\n\n"

                    "🤍Полный разбор — 1000 ⭐\n"
                    "Полностью разбираем ситуацию, количество вопросов не ограничено.\n\n"

                    "💫 Другая сумма\n"
                    "Если нужна другая сумма оплаты — введи её самостоятельно."
                ),
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "1 вопрос — 100 ⭐",
                                "callback_data": "buy_100"
                            }
                        ],
                        [
                            {
                                "text": "2–4 вопроса — 250 ⭐",
                                "callback_data": "buy_250"
                            }
                        ],
                        [
                            {
                                "text": "Расширенный разбор — 500 ⭐",
                                "callback_data": "buy_500"
                            }
                        ],
                        [
                            {
                                "text": "Полный разбор — 1000 ⭐",
                                "callback_data": "buy_1000"
                            }
                        ],
                        [
                            {
                                "text": "💫 Другая сумма ⭐",
                                "callback_data": "custom_amount"
                            }
                        ]
                    ]
                }
            })

            return "ok", 200

        # Ввод своей суммы
        if chat_id in waiting_for_amount:
            try:
                amount = int(text)

                if amount < 1:
                    raise ValueError

                waiting_for_amount.discard(chat_id)

                tg("sendInvoice", {
                    "chat_id": chat_id,
                    "title": "Оплата расклада",
                    "description": f"Оплата расклада Таро — {amount} ⭐",
                    "payload": f"custom_{amount}",
                    "currency": "XTR",
                    "prices": [
                        {
                            "label": "Оплата расклада",
                            "amount": amount
                        }
                    ]
                })

            except ValueError:
                tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": (
                        "Напиши количество звёзд только цифрами ⭐\n\n"
                        "Например: 350"
                    )
                })

            return "ok", 200

    # Нажатие на кнопку
    callback = update.get("callback_query")

    if callback:
        callback_id = callback.get("id")
        chat_id = callback.get("message", {}).get("chat", {}).get("id")
        product_id = callback.get("data")

        tg("answerCallbackQuery", {
            "callback_query_id": callback_id
        })

        # Другая сумма
        if product_id == "custom_amount" and chat_id:
            waiting_for_amount.add(chat_id)

            tg("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    "💫 Введи количество звёзд, "
                    "которое хочешь отправить.\n\n"
                    "Например: 350"
                )
            })

            return "ok", 200

        # Обычные тарифы
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

    # Подтверждение оплаты
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
