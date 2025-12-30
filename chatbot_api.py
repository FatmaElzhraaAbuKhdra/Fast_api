from fastapi import FastAPI
from pydantic import BaseModel
import oracledb
import re

app = FastAPI(title="SWA Chatbot API")

# اتصال Oracle
dsn = oracledb.makedsn("95.216.70.183", 1521, service_name="orclpdb")
conn = oracledb.connect(
    user="COMP",
    password="COMP",
    dsn=dsn
)

class ChatRequest(BaseModel):
    user: str
    question: str

def normalize(text: str):
    """تنظيف النصوص لمطابقة الكلمات"""
    text = text.lower()
    text = re.sub(r'[\u064B-\u0652]', '', text)  # إزالة التشكيل
    text = re.sub(r'[^a-z\u0600-\u06FF0-9 ]', '', text)  # الحروف العربية والإنجليزية والأرقام
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# mapping الكولمنز إلى الشرح
COLUMNS_MAPPING = {
    "EMPLOYEE_NAME_A": "اسم الموظف بالعربي",
    "EMPLOYEE_NAME_E": "اسم الموظف بالانجليزي",
    "JOB_NUMBER": "الرقم الوظيفي",
    "HIRE_DATE": "تاريخ التعين",
    "DEPT_ID": "كود الاداره",
    "JOB_DESCRIPTION": "المسمي الوظيفي",
    "COMPANY_CODE": "كود الشركة",
    "FISCAL_YEAR": "السنة المالية",
    "BRANCH_ID": "كود الفرع"
}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    user = req.user
    question = normalize(req.question)

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT NVL(E.EMPLOYEE_NAME_A, E.EMPLOYEE_NAME_E) AS employee_name,
                   E.EMPLOYEE_NAME_A, E.EMPLOYEE_NAME_E, E.JOB_NUMBER, E.HIRE_DATE, 
                   E.DEPT_ID, E.JOB_DESCRIPTION, E.COMPANY_CODE, E.FISCAL_YEAR, E.BRANCH_ID
            FROM EMPLOYEES E
            JOIN ACC_USERS A ON E.EMPLOYEE_ID = A.EMP_ID
            WHERE A.USER_NAME = :user
        """, user=user)
        row = cursor.fetchone()
        if not row:
            return {"reply": "آسف، لا أملك معلومات عنك."}

        # إنشاء dict لكولمنز الموظف
        employee_data = dict(zip([
            "EMPLOYEE_NAME_A","EMPLOYEE_NAME_E","JOB_NUMBER","HIRE_DATE",
            "DEPT_ID","JOB_DESCRIPTION","COMPANY_CODE","FISCAL_YEAR","BRANCH_ID"
        ], row[1:]))

        # مطابقة السؤال مع أي كولمن
        for col, desc in COLUMNS_MAPPING.items():
            if col in employee_data and normalize(str(employee_data[col])) in question:
                return {"reply": f"{desc}: {employee_data[col]}"}
            for keyword in question.split():
                if keyword in normalize(desc):
                    return {"reply": f"{desc}: {employee_data[col]}"}

        return {"reply": f"اسمك: {row[0]}"}

    except Exception as e:
        return {"reply": f"حدث خطأ: {str(e)}"}
