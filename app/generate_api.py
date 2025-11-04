from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from .generator import generate_clothing_only_image

router = APIRouter()

@router.get("/generate-clothing/ready")
def generate_ready():
    return {"ok": True}

@router.post("/generate-clothing")
async def generate_clothing(file: UploadFile = File(...)) -> Response:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Image file is empty")

    png = await generate_clothing_only_image(raw_bytes=raw)
    return Response(content=png, media_type="image/png")
