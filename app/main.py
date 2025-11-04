from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .analyzer import analyze_items
from .generate_api import router as generate_router

# -------- dotenv: always load .env regardless of where the app starts --------
env_path = find_dotenv(filename=".env", usecwd=True)
if not env_path:
    env_path = str((Path(__file__).resolve().parent / ".env"))
load_dotenv(env_path, override=True)

app = FastAPI(title="PersonFi Backend API (analyze-only, minimal)", version="0.4.0")

# -------- CORS (convenient for local frontend testing) --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to specific origins for production
    allow_credentials=False,  # avoid conflict with "*" that browsers may block
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI demo page (optional): served at /ui/
app.mount(
    "/ui",
    StaticFiles(directory=str((Path(__file__).resolve().parent / "static")), html=True),
    name="ui",
)


# -------- Health check --------
@app.get("/hello")
def hello():
    return {
        "message": "Hello from FastAPI. PersonFi analyze-only API (minimal) ready.",
        "supabaseConfigured": False,
    }

# -------- Main endpoint: analyze clothing, return only 3 fields --------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Upload a photo containing a person. Detect wearable items.
    Returns JSON: { "items": [ {item_category, item_color, item_brand}, ... ] }
    """
    raw_bytes = await file.read()
    mime = file.content_type or "image/png"
    payload = await analyze_items(raw_bytes=raw_bytes, mime=mime)
    return JSONResponse(payload)

# -------- Generation endpoints (image-to-image: clothing-only PNG) --------
app.include_router(generate_router)



