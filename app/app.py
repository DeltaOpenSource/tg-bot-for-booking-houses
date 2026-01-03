import os
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

TOKEN = os.getenv('TOKEN')


if not TOKEN:
    raise ValueError("Bot token is not set in environment variables!")

app = FastAPI()

def parse_message(message):
    if "message" not in message or "text" not in message["message"]:
        return None, None  

    chat_id = message["message"]["chat"]["id"]
    txt = message["message"]["text"]
    return chat_id, txt

@app.post('/setwebhook')
async def setwebhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    payload = {
        "url": "https://tg-bot-for-booking-houses.vercel.app/webhook",
        "allowed_updates": ["message", "callback_query", "my_chat_member"]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code == 200:
        return JSONResponse(content={"status": "Webhook set with my_chat_member support"}, status_code=200)
    else:
        return JSONResponse(content={"error": response.text}, status_code=response.status_code)

@app.on_event("startup")
async def startup_event():
    await setwebhook()


async def tel_send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "Открыть приложение", "web_app": {"url": "https://deltaopensource.github.io/tg-bot-crypto/frontend/"}},
                ]
            ]
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        print("Ошибка отправки сообщения:", response.text)

    return response

async def tel_send_message_not_markup(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        print("Ошибка отправки сообщения:", response.text)

    return response

user_states = {}



@app.post('/webhook')
async def webhook(request: Request, background_tasks: BackgroundTasks):
    msg = await request.json()
    print("Получен вебхук:", msg)

    if "callback_query" in msg:
        callback = msg["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_data = callback["data"]


        return JSONResponse(content={"status": "deleted"}, status_code=200)

    chat_id, txt = parse_message(msg)
    if chat_id is None or txt is None:
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    if chat_id in user_states and user_states[chat_id] == "awaiting_response":
        background_tasks.add_task(process_user_request, chat_id, txt)

    elif txt.lower() == "/start":
        await tel_send_message(chat_id, 
            "Добро пожаловать в crypto! "
        )

    return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/")
async def index():
    return "<h1>Telegram Bot Webhook is Running</h1>"

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)), log_level="info")
