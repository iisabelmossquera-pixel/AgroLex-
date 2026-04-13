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
:root {
    --bg: #0f172a;
    --text: white;
    --bot: #1e293b;
    --user: #3b82f6;
}

.light {
    --bg: #f5f5f5;
    --text: #111;
    --bot: #e2e8f0;
    --user: #2563eb;
}

body {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    flex-direction: column;
    height: 100vh;
    transition: 0.3s;
}

.header {
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header span:first-child {
    font-size: 32px;
    font-weight: bold;
    letter-spacing: 1px;
}

.chat {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.msg {
    padding: 12px 16px;
    border-radius: 16px;
    margin-bottom: 10px;
    max-width: 70%;
    animation: fade 0.2s;
}

.user {
    background: var(--user);
    align-self: flex-end;
}

.bot {
    background: var(--bot);
    align-self: flex-start;
}

.input-area {
    display: flex;
    padding: 10px;
}

input {
    flex: 1;
    padding: 12px;
    border-radius: 10px;
    border: none;
}

button {
    margin-left: 10px;
    padding: 12px;
    border: none;
    border-radius: 10px;
    background: #22c55e;
    color: white;
    cursor: pointer;
}

button:hover {
    background: #16a34a;
}

.toggle {
    cursor: pointer;
    font-size: 18px;
}

.typing {
    font-style: italic;
    opacity: 0.7;
}

@keyframes fade {
    from {opacity:0; transform: translateY(5px);}
    to {opacity:1;}
}
</style>
</head>

<body>

<div class="header">
    <span>🌱 AgroLex</span>
    <span class="toggle" onclick="toggleMode()">🌙</span>
</div>

<div id="chat" class="chat"></div>

<div class="input-area">
    <input id="input" placeholder="Haz tu pregunta legal..." />
    <button onclick="send()">Enviar</button>
</div>

<script>

function toggleMode() {
    document.body.classList.toggle("light");
}

async function send() {
    let input = document.getElementById("input");
    let msg = input.value;

    if (!msg) return;

    addMessage(msg, "user");

    let typingDiv = addMessage("Escribiendo...", "bot typing");

    let res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    });

    let data = await res.json();

    typingDiv.remove();
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

    return div;
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
                {"role": "system", "content": "Eres un abogado experto en derecho agrario en Panamá. Explica claro, con ejemplos simples."},
                {"role": "user", "content": msg.message}
            ]
        )

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        return {"reply": str(e)}
