# PersonFi-Backend

Minimal FastAPI + Supabase backend template with a single endpoint.

## Quick Start (Windows PowerShell)

1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) Configure environment variables

- Copy `.env.example` to `.env`
- In your Supabase project settings, copy the Project URL and anon key, then set:

```
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
```

4) Run the server (defaults to port 8000)

```powershell
uvicorn app.main:app --reload --port 8000
```

5) Try it

- Open http://127.0.0.1:8000/ui
- API docs: http://127.0.0.1:8000/docs