from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .analyzer import analyze_items
from .generate_api import router as generate_router

# -------- dotenv：无论从哪里启动都能加载到 .env --------
env_path = find_dotenv(filename=".env", usecwd=True)
if not env_path:
    env_path = str((Path(__file__).resolve().parent / ".env"))
load_dotenv(env_path, override=True)

app = FastAPI(title="PersonFi Backend API (analyze-only, minimal)", version="0.4.0")

# -------- CORS（本地前端测试方便） --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境请收紧或改为具体域名
    allow_credentials=False,  # 避免与 "*" 冲突导致浏览器拦截
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI demo page (optional): served at /ui/
app.mount(
    "/ui",
    StaticFiles(directory=str((Path(__file__).resolve().parent / "static")), html=True),
    name="ui",
)


# -------- 健康检查 --------
@app.get("/hello")
def hello():
    return {
        "message": "Hello from FastAPI. PersonFi analyze-only API (minimal) ready.",
        "supabaseConfigured": False,
    }

# -------- 主接口：只做“识别”，只回三字段 --------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    上传一张含有人的照片，识别衣物信息。
    返回 JSON：{ "items": [ {item_category, item_color, item_brand}, ... ] }
    """
    raw_bytes = await file.read()
    mime = file.content_type or "image/png"
    payload = await analyze_items(raw_bytes=raw_bytes, mime=mime)
    return JSONResponse(payload)


# -------- 生成接口（图生图：只输出衣物 PNG） --------
app.include_router(generate_router)



