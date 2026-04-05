from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import os
from openai import OpenAI

# ------------------------
# OPENAI (NUEVA VERSION)
# ------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="AgroLex - Derecho Agrario")

DB_PATH = "faqs.db"


# ------------------------
# HOME
# ------------------------
@app.get("/")
def home():
    return {"mensaje": "AgroLex 🌱 funcionando correctamente"}


# ------------------------
# CHAT UI
# ------------------------
@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui():
    return """
    <html>
    <body style="font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh;">
        <div>
            <h2>AgroLex 🌱</h2>
            <input id="msg" placeholder="Escribe..." />
            <button onclick="send()">Enviar</button>
            <div id="chat"></div>
        </div>

        <script>
        async function send() {
            let msg = document.getElementById("msg").value;

            let res = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: msg})
            });

            let data = await res.json();
            document.getElementById("chat").innerHTML += "<p><b>Tú:</b> " + msg + "</p>";
            document.getElementById("chat").innerHTML += "<p><b>AgroLex:</b> " + data.reply + "</p>";
        }
        </script>
    </body>
    </html>
    """


# ------------------------
# DB
# ------------------------
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
        ("derecho agrario", "Rama del derecho que regula la tierra."),
        ("reforma agraria", "Redistribución de tierras para equidad."),
        ("función social de la tierra", "La tierra debe ser productiva y útil a la sociedad.")
    ]

    for q, a in sample:
        try:
            c.execute("INSERT INTO faq (question, answer) VALUES (?, ?)", (q, a))
        except:
            pass

    conn.commit()
    conn.close()


def get_faq(question: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT answer FROM faq WHERE question LIKE ?", (f"%{question}%",))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


# ------------------------
# MODELOS
# ------------------------
class UserQuery(BaseModel):
    message: str


# ------------------------
# STARTUP
# ------------------------
@app.on_event("startup")
def startup():
    init_db()


# ------------------------
# CHAT
# ------------------------
@app.post("/chat")
async def chat(data: UserQuery):

    msg = data.message.strip().lower()

    if not msg:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    # FAQ primero
    faq = get_faq(msg)
    if faq:
        return {"reply": faq, "source": "faq"}

    # OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en derecho agrario."},
                {"role": "user", "content": msg}
            ]
        )

        return {"reply": response.choices[0].message.content, "source": "llm"}

    except Exception as e:
        return {"reply": "Error en IA", "source": "error"}
