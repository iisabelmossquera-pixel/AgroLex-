from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Message(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgroLex 🌱</title>
        <style>
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: white;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }

            .header {
                padding: 15px;
                text-align: center;
                background: #020617;
                font-weight: bold;
                font-size: 18px;
            }

            .chat {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            }

            .msg {
                margin-bottom: 12px;
                padding: 10px 14px;
                border-radius: 12px;
                max-width: 70%;
            }

            .user {
                background: #2563eb;
                align-self: flex-end;
            }

            .bot {
                background: #1e293b;
                align-self: flex-start;
            }

            .input-area {
                display: flex;
                padding: 10px;
                background: #020617;
            }

            input {
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                border: none;
                outline: none;
            }

            button {
                margin-left: 10px;
                padding: 12px;
                border: none;
                border-radius: 8px;
                background: #22c55e;
                color: white;
                cursor: pointer;
            }
        </style>
    </head>
    <body>

        <div class="header">AgroLex 🌱</div>

        <div id="chat" class="chat"></div>

        <div class="input-area">
            <input id="input" placeholder="Escribe tu pregunta..." />
            <button onclick="send()">Enviar</button>
        </div>

        <script>
            async function send() {
                let input = document.getElementById("input");
                let msg = input.value;

                if (!msg) return;

                addMessage(msg, "user");

                let res = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({message: msg})
                });

                let data = await res.json();

                addMessage(data.reply, "bot");

                input.value = "";
            }

            function addMessage(text, type) {
                let chat = document.getElementById("chat");
                let div = document.createElement("div");

                div.className = "msg " + type;
                div.innerText = text;

                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
        </script>

    </body>
    </html>
    """


@app.post("/chat")
def chat(msg: Message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en derecho agrario. Responde claro y breve."},
                {"role": "user", "content": msg.message}
            ]
        )

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        return {"reply": str(e)}
