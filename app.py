from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import openai
import os

# API KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Chatbot - Derecho Agrario MVP")

DB_PATH = "faqs.db"

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
        ("¿Qué es el derecho agrario?", "Es la rama del derecho que regula el uso y la explotación de la tierra."),
        ("¿Qué es la reforma agraria?", "Es la redistribución de la tierra para lograr mayor equidad social."),
        ("¿Qué es la función social de la tierra?", "La tierra debe ser productiva y beneficiar a la sociedad."),
        ("¿Qué son los contratos agrarios?", "Son acuerdos legales que regulan actividades agrícolas."),
        ("Importancia del derecho agrario", "Garantiza seguridad alimentaria y desarrollo sostenible.")
    ]

    for q, a in sample:
        try:
            c.execute("INSERT INTO faq (question, answer) VALUES (?, ?)", (q.lower(), a))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

def get_faq_answer(user_question: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT answer FROM faq WHERE question LIKE ?", (f"%{user_question}%",))
    rows = c.fetchall()
    conn.close()

    if rows:
        return rows[0][0]
    return None

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

class UserQuery(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    source: str

@app.on_event("startup")
def startup_event():
    init_db()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
