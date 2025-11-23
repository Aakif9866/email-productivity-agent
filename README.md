# Prompt-Driven Email Productivity Agent

## Overview

A minimal prompt-driven Email Productivity Agent that ingests an inbox (mock or real), runs user-defined prompts via an LLM to categorize emails, extract action items, draft replies, and provides an email-agent chat interface. Drafts are saved — the system never sends emails.

## Architecture

- Frontend: Streamlit app (`frontend/streamlit_app.py`)
- Backend: FastAPI (`backend/app.py`) — stores prompts, emails, results, and drafts in SQLite
- LLM: `backend/llm_client.py` — wrapper for OpenAI or other LLMs
- Mock inbox: `frontend/assets/mock_inbox.json`
- Default prompts: `prompts/default_prompts.json`

## Setup (local)

1. Clone:
   git clone <repo-url>
   cd email-agent

markdown
Copy code

2. Backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --reload --port 8000

go
Copy code
Set `OPENAI_API_KEY` env var if you want real LLM calls.

Example `requirements.txt`:
fastapi
uvicorn
openai
pydantic

cpp
Copy code

3. Frontend (in new terminal)
   cd frontend
   pip install streamlit requests
   streamlit run streamlit_app.py

pgsql
Copy code
If backend URL is not `http://localhost:8000`, set `st.secrets["backend_url"]` or modify `BACKEND` in the file.

## How to load the Mock Inbox

- Open Streamlit UI → left panel → click "Load Mock Inbox". This calls backend `/load_mock_inbox` to populate DB.

## How to configure prompts

- Use the **Prompt Brain** on the left. Edit categorization, action item, and auto-reply prompts. Click **Save Prompts**. Prompts are stored in backend DB.

## Usage examples

1. Load inbox.
2. Select an email from the dropdown.
3. Click "Run processing" to run categorization & action extraction.
4. Use "Ask the agent" field for summarization or draft replies.
5. Save any generated reply as a draft (not sent).

## Mock inbox & default prompts

Mock inbox at `frontend/assets/mock_inbox.json`. Default prompts in `prompts/default_prompts.json`.

## Demo video (5-10 min) checklist

- Start backend and frontend
- Load the mock inbox
- Show Prompt Brain and edit a prompt live
- Select an email, run processing (show category + extracted tasks)
- Ask agent to "Summarize this email" and "Draft reply"
- Save a draft and show it stored in the DB
- Mention safety: drafts are stored, never sent automatically

## Notes / Next steps

- Add OAuth or IMAP connector for real inbox ingestion
- Improve prompt storage with versioning and history
- Add RAG: embed email content into vector DB (FAISS) for context-aware replies
- Add user roles and permissions, logging and monitoring
