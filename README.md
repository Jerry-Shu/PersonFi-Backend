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

- Open http://127.0.0.1:8000/hello
- API docs: http://127.0.0.1:8000/docs

The endpoint returns 200 even if Supabase is not configured, and includes a hint. Once `.env` is set, it reports `supabaseConfigured: true`.

## API

- GET `/hello`
	- When Supabase is not configured:
		```json
		{"message":"Hello from FastAPI. Supabase is not configured yet.","supabaseConfigured":false,"hint":"Set SUPABASE_URL and SUPABASE_ANON_KEY in your environment or .env file."}
		```
	- When Supabase is configured:
		```json
		{"message":"Hello from FastAPI with Supabase configured.","supabaseConfigured":true}
		```

## Project Structure

```
app/
	__init__.py
	main.py             # FastAPI app and /hello endpoint
	supabase_client.py  # Supabase Client from environment
tests/
	test_hello.py       # Minimal test for /hello
.env.example          # Environment variables template
requirements.txt      # Dependencies
.gitignore
```

## Testing

```powershell
pytest -q
```

## Troubleshooting

- Error like `Import "supabase" could not be resolved`: make sure you ran `pip install -r requirements.txt` in the active venv.
- Port in use: change the port `uvicorn app.main:app --reload --port 8080`
- `.env` not loaded: ensure the file is named `.env` and located in the project root.

## Notes

- Add more endpoints in `app/main.py`. The helper `get_supabase()` returns a ready Supabase client once `.env` is configured.
- The template does not assume any table schema; it only checks whether Supabase is configured so you can extend safely.
