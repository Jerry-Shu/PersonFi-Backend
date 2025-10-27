from fastapi import FastAPI, HTTPException

from .supabase_client import get_supabase

app = FastAPI(title="PersonFi Backend API", version="0.1.0")


@app.get("/hello")
def hello():
    """A single sample endpoint.

    If Supabase env vars are configured, it confirms the client is ready.
    Otherwise, it still responds with a friendly message.
    """
    sb = get_supabase()
    if sb is None:
        return {
            "message": "Hello from FastAPI. Supabase is not configured yet.",
            "supabaseConfigured": False,
            "hint": "Set SUPABASE_URL and SUPABASE_ANON_KEY in your environment or .env file.",
        }

    try:
        # We don't assume any tables exist; just report that the client is configured.
        return {
            "message": "Hello from FastAPI with Supabase configured.",
            "supabaseConfigured": True,
        }
    except Exception as e:
        # Surface any unexpected client errors
        raise HTTPException(status_code=500, detail=str(e))
