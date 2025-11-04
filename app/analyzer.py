import base64
import io
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

# -------- OpenAI Client (lazy init) --------
_openai_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY in environment")
        try:
            _openai_client = OpenAI(api_key=api_key)
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Failed to init OpenAI client") from exc
    return _openai_client

# -------- Prompt (only 3 fields) --------
def _vision_prompt() -> str:
    return (
        """
You are a precise fashion vision assistant.

TASK:
Analyze the photo of a person and identify ALL distinct wearable clothing items visible
(e.g., t-shirt, shirt, jacket, blazer, pants, jeans, dress, skirt, tie, coat, shoes, hat).

For each detected clothing item, output exactly these three fields:
- "item_category": concise lower-case noun (e.g., "t-shirt", "blazer", "jeans", "tie").
- "item_color": short phrase of the visible color and pattern.
  • If any pattern exists (stripes, plaid, polka dots, prints, logos, text, lace, etc.),
    include base color + pattern (e.g., "white with blue stripes", "black with white checks").
  • If there is a visible logo/text/print, include it in the color phrase (e.g., "red with white logo").
  • Keep it lowercase and concise.
- "item_brand": brand name only if clearly visible; otherwise "".

STYLE:
- Do NOT invent brands or hallucinate colors.
- Keep all text lowercase.
- Return JSON ONLY. No explanations, no markdown.

OUTPUT FORMAT (return strictly this):
{
  "items": [
    { "item_category": "string", "item_color": "string", "item_brand": "string" }
  ]
}
"""
    ).strip()

# -------- Clean output to required shape --------

def _coerce_items(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    items = payload.get("items") or []
    clean: List[Dict[str, str]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        cat = str(it.get("item_category", "")).strip().lower()
        col = str(it.get("item_color", "")).strip().lower()
        brd = str(it.get("item_brand", "")).strip()
        clean.append({
            "item_category": cat,
            "item_color": col,
            "item_brand": brd if brd else "",
        })
    return clean

# -------- Public: analyze items from raw image bytes --------
async def analyze_items(*, raw_bytes: bytes, mime: str) -> Dict[str, Any]:
    """Validate image, call OpenAI vision, and return {"items": [...]}."""
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty")

    # Validate the image is decodable
    try:
        Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Unsupported or invalid image file") from exc

    client = get_openai_client()
    # Default to GPT-5 as requested; respect OPENAI_VISION_MODEL when provided
    model_name = os.getenv("OPENAI_VISION_MODEL") or "gpt-5.0"
    # Prefer Responses API for GPT-5; otherwise allow env override
    env_flag = os.getenv("USE_RESPONSES")
    use_responses = model_name.startswith("gpt-5") or (env_flag and env_flag.lower() == "true")

    prompt = _vision_prompt()
    encoded_image = base64.b64encode(raw_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{encoded_image}"

    if use_responses:
        # Responses API (recommended for GPT-5). Some SDK versions don't support response_format.
        try:
            resp = await run_in_threadpool(
                client.responses.create,
                model=model_name,
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }],
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI vision request failed: {exc}") from exc

        try:
            text = getattr(resp, "output_text", None)
            if not text:
                # Fallback for older structures
                text = resp.output[0].content[0].text
            data = json.loads(text)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Malformed response from vision model: {exc}") from exc

    else:
        # Chat Completions API
        try:
            resp = await run_in_threadpool(
                client.chat.completions.create,
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }],
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"OpenAI vision request failed: {exc}") from exc

        try:
            msg = resp.choices[0].message
            message = getattr(msg, "content", None)
            if not message:
                raise ValueError(f"empty content. raw={resp}")
            data = json.loads(message)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Malformed response from vision model: {exc}") from exc

    return {"items": _coerce_items(data)}
