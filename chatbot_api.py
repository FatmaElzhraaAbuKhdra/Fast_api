# install: pip install fastapi uvicorn cx_Oracle pydantic

from fastapi import FastAPI, Request
from pydantic import BaseModel
import cx_Oracle
import re

app = FastAPI(title="SWA Chatbot API")


dsn = cx_Oracle.makedsn("YOUR_DB_HOST", 1521, service_name="YOUR_SERVICE")
conn = cx_Oracle.connect(user="YOUR_DB_USER", password="YOUR_DB_PASS", dsn=dsn)


class ChatRequest(BaseModel):
    user: str
    question: str

def normalize(text: str):
    text = text.lower()
    text = re.sub(r'[\u064B-\u0652]', '', text)  
    text = re.sub(r'[^a-z\u0600-\u06FF0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- Define your tables and columns ---
TABLES = {
    "ACC_USERS": {
        "REAL_NAME": "اسمك الحقيقي",
        "USER_TYPE": "نوع المستخدم",
        "ROLE_ID": "دورك"
    },
# الجداول
}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    user = req.user
    question = normalize(req.question)
    
    cursor = conn.cursor()
    
    # البحث في كل الجداول
    for table, columns in TABLES.items():
        for col, desc in columns.items():
            try:
                cursor.execute(f"SELECT {col} FROM {table} WHERE USER_NAME = :user", user=user)
                row = cursor.fetchone()
                if row and normalize(str(row[0])) in question:
                    return {"reply": f"{desc}: {row[0]}"}
                elif row:
                    # لو السطر موجود والعمود له معنى للسؤال
                    for keyword in question.split():
                        if keyword in normalize(desc):
                            return {"reply": f"{desc}: {row[0]}"}
            except Exception as e:
                continue

    return {"reply": "آسف، لا أملك معلومات عن ذلك."}
