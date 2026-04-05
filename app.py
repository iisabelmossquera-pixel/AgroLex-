from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import openai
import os

# API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Chatbot - Derecho Agrario MVP")

DB_PATH = "faqs.db"


# ---------------------------
# HOME
# ---------------------------
@app.get("/")
def home():
    return {"mensaje": "Bienvenido a AgroLex 🌱 - Chatbot de Derecho Agrario"}


# ---------------------------
# CHAT UI
# ---------------------------
@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgroLex Chat</title>
        <style>
            body {
                font-family: Arial;
                background: #f5f5f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .chat-box {
                width: 350px;
                background: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .messages {
                height: 300px;
                overflow-y: auto;
                margin-bottom: 10px;
            }
            .input-box {
                display: flex;
            }
            input {
                flex: 1;
                padding: 10px;
            }
            button {
                padding: 10px;
                background: #4CAF50;
                color: white;
                border: none;
            }
        </style>
    </head>
    <body>
        <div class="chat-box">
            <h3>AgroLex 🌱</h3>
            <div class="messages" id="messages"></div>
            <div class="input-box">
                <input id="input" placeholder="Escribe tu pregunta..." />
                <button onclick="send()">Enviar</button>
            </div>
        </div>

        <script>
            async function send() {
                let input = document.getElementById("input");
                let msg = input.value;

                document.getElementById("messages").innerHTML += "<p><b>Tú:</b> " + msg + "</p>";

                let res = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({message: msg})
                });

                let data = await res.json();

                document.getElementById("messages").innerHTML += "<p><b>AgroLex:</b> " + data.reply + "</p>";

                input.value = "";
            }
        </script>
    </body>
    </html>
    """


# ---------------------------
# DB INIT
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT UNIQUE,
        answer TEXT
    )
    """)

    sample = [
        ("¿qué es el derecho agrario?", "Es la rama del derecho que regula el uso y la explotación de la tierra."),
        ("¿qué es la reforma agraria?", "Es la redistribución de la tierra para lograr mayor equidad social."),
        ("¿qué es la función social de la tierra?", "La tierra debe ser productiva y beneficiar a la sociedad."),
        ("¿qué son los contratos agrarios?", "Son acuerdos legales que regulan actividades agrícolas."),
        ("importancia del derecho agrario", "Garantiza seguridad alimentaria y desarrollo sostenible.")
    ]

    for q, a in sample:
        try:
            c.execute("INSERT INTO faq (question, answer) VALUES (?, ?)", (q, a))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


# ---------------------------
# FAQ SEARCH
# ---------------------------
def get_faq_answer(user_question: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT answer FROM faq WHERE question LIKE ?", (f"%{user_question}%",))
    rows = c.fetchall()

    conn.close()

    if rows:
        return rows[0][0]
    return None


# ---------------------------
# OPENAI RESPONSE
# ---------------------------
async def generate_llm_response(prompt: str) -> str:
    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "Lo siento, no puedo responder en este momento."


# ---------------------------
# MODELS
# ---------------------------
class UserQuery(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    source: str


# ---------------------------
# STARTUP
# ---------------------------
@app.on_event("startup")
def startup_event():
    init_db()


# ---------------------------
# CHAT ENDPOINT
# ---------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(user_query: UserQuery):
    question = user_query.message.strip().lower()

    if not question:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    faq_ans = get_faq_answer(question)
    if faq_ans:
        return ChatResponse(reply=faq_ans, source="faq")

    prompt = f"""
Eres un experto en derecho agrario.
Responde de forma clara, breve y sencilla.

Pregunta: {question}
"""

    llm_ans = await generate_llm_response(prompt)
    return ChatResponse(reply=llm_ans, source="llm")


# ---------------------------
# RUN (LOCAL ONLY)
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
