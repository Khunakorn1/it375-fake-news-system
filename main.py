from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
from database import SessionLocal
from models import News
from sqlalchemy.orm import Session
import os
from openai import OpenAI

client = OpenAI(api_key="")


# try:
#     print("--- Available Models ---")
#     for m in client.models.list():
#         print(f"Name: {m.name}")
#     print("------------------------")
# except Exception as e:
#     print(f"Cannot list models: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



db = SessionLocal()

# ================== INIT ==================
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="secret123")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")



# ================== AI LOGIC ==================

def analyze_with_ai(text: str):
    prompt = f"""
คุณคือผู้เชี่ยวชาญด้านตรวจสอบข่าวปลอม

วิเคราะห์ข้อความต่อไปนี้:

{text}

ตอบในรูปแบบนี้เท่านั้น:

Result: (Fake / Suspicious / Real)
Score: (0-100)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI Error:", e)
        return "❌ Server ยุ่ง"


def analyze_news(text: str):

    text = text.lower()

    fake_keywords = [
        "ด่วน",
        "ด่วนที่สุด",
        "แชร์",
        "แชร์ด่วน",
        "ห้ามพลาด",
        "100",
        "100%",
        "จริงแน่นอน",
        "คลิกเลย",
        "ได้เงิน",
        "แจกฟรี",
        "ลงทุน",
        "กำไร",
        "การันตี"
    ]

    score = 0
    found_words = []

    for word in fake_keywords:
        if word in text:
            score += 1
            found_words.append(word)

    print("TEXT:", text)
    print("FOUND:", found_words)
    print("SCORE:", score)

    if score >= 3:
        result = "❌ Fake News"
    elif score == 2:
        result = "⚠️ Suspicious"
    else:
        result = "✅ Likely Real"

    return {
        "result": result,
        "score": score,
        "keywords": found_words
    }




# ================== HOME ==================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    user = request.session.get("user")

    return templates.TemplateResponse( request, "index.html",
        {
            "request": request,
            "message": "Fake News Detection System",
            "activities": ["Paste News", "Analyze", "See Result"],
            "score": 0,
            "user": user
        }
    )

@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse(request, "help.html")

# ================== ADMIN ==================

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):

    if request.session.get("user") != "admin":
        return RedirectResponse("/login", status_code=303)

    news_list = db.query(News).order_by(News.id.desc()).all()

    return templates.TemplateResponse( request, "admin.html",
        {
            "request": request,
            "news_list": news_list,
            "user": request.session.get("user")
        }
    )

@app.get("/admin/delete/{news_id}")
def delete_news(request: Request, news_id: int):

    if request.session.get("user") != "admin":
        return RedirectResponse("/login", status_code=303)

    news = db.query(News).filter(News.id == news_id).first()

    if news:
        db.delete(news)
        db.commit()

    return RedirectResponse("/admin", status_code=303)


# ================== ANALYZE ==================
@app.get("/analyze", response_class=HTMLResponse)
def analyze_form(request: Request):
    return templates.TemplateResponse(
        request,
        "analyze.html",
        context={}
    )


# ================== API ==================
@app.post("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request, text: str = Form(...)):
    ai_result = analyze_with_ai(text)
    rule_result = analyze_news(text)

    return templates.TemplateResponse(
    request,
    "result.html",
    context={
        "text": text,
        "ai_result": ai_result,
        "result": rule_result["result"],
        "score": rule_result["score"],
        "keywords": rule_result["keywords"],
        "is_ai": "Server ยุ่ง" not in ai_result   # 👈 เพิ่ม
    }
)


@app.post("/api/analyze")
async def analyze_api(text: str = Form(...), db: Session = Depends(get_db)):

    ai_result = analyze_with_ai(text)
    rule_result = analyze_news(text)

    news = News(
        text=text,
        result=ai_result,
        score=rule_result["score"]
    )

    db.add(news)
    db.commit()

    return {
        "result": ai_result,
        "score": rule_result["score"],
        "keywords": rule_result["keywords"]
    }



# ================== LOGIN ==================
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        context={}
    )

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":
        request.session["user"] = username
        request.session["role"] = "admin"   # 👈 สำคัญมาก

        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        context={"error": "Login failed"}
    )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/api/time")
def get_time():
    return {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}




