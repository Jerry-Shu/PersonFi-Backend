import io
import os
import tempfile
from typing import Optional

from fastapi import HTTPException
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
import httpx

# Lazy client
_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY in environment")
        _client = OpenAI(api_key=api_key)
    return _client

# Core generation
async def generate_clothing_only_image(*, raw_bytes: bytes) -> bytes:
    """Given a person photo, generate a clothing-only product-style image.

    Returns PNG bytes.
    """
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty")

    # Validate/readability
    try:
        Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Unsupported or invalid image file") from exc

    client = get_client()
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")

    # Use image edits with a strong instruction to extract only clothing and accessories
    instruction = (
        "Extract only the wearable clothing and accessories from the person photo. "
        "Remove the person and any body parts completely. Arrange the garments and accessories "
        "neatly as a styled product laydown on a plain white background. Keep colors and textures "
        "accurate and realistic. No logos unless clearly visible in the source, no text, and no extra objects."
    )

    # Write to a temp file with delete=False to avoid Windows file locking, reopen separately
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp.flush()
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            try:
                # Newer SDKs use images.edit (singular) and accept a single file-like for image
                if hasattr(client.images, "edit"):
                    result = client.images.edit(
                        model=model,
                        image=f,
                        prompt=instruction,
                        size=size,
                    )
                else:
                    # Fallback to .edits for older SDKs
                    result = client.images.edits(
                        model=model,
                        image=[f],
                        prompt=instruction,
                        size=size,
                    )
            except Exception as exc:  # propagate as HTTP error
                raise HTTPException(status_code=502, detail=f"OpenAI image edit failed: {exc}") from exc
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    if not result.data:
        raise HTTPException(status_code=500, detail="Image generation returned empty response")

    # Prefer base64 payload if provided; otherwise fetch from URL
    data0 = result.data[0]
    png_bytes: Optional[bytes] = None
    b64_val = getattr(data0, "b64_json", None)
    url_val = getattr(data0, "url", None)

    if b64_val:
        import base64
        png_bytes = base64.b64decode(b64_val)
    elif url_val:
        try:
            resp = httpx.get(url_val, timeout=30)
            resp.raise_for_status()
            png_bytes = resp.content
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch generated image url: {exc}") from exc
    else:
        raise HTTPException(status_code=500, detail="Image generation contained no data payload")

    # Ensure valid PNG (re-encode)
    try:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return png_bytes
