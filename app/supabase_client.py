import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Load .env if present (development convenience)
load_dotenv()


def get_supabase() -> Optional[Client]:
    """Create and return a Supabase client if env vars are present, else None.

    Required env vars:
    - SUPABASE_URL
    - SUPABASE_ANON_KEY
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        return None

    return create_client(url, key)
