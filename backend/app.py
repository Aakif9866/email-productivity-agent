# backend/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3, json, os
from typing import List
from llm_client import call_llm

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
app = FastAPI()

# --- simple DB helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prompts(name TEXT PRIMARY KEY, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS emails(id TEXT PRIMARY KEY, json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results(email_id TEXT PRIMARY KEY, json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY, json TEXT)''')
    conn.commit()
    conn.close()

init_db()

class PromptItem(BaseModel):
    name: str
    content: str

class Email(BaseModel):
    id: str
    from_addr: str
    to: str
    subject: str
    body: str
    timestamp: str

@app.post("/prompts")
def save_prompt(item: PromptItem):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO prompts(name, content) VALUES (?, ?)", (item.name, item.content))
    conn.commit()
    conn.close()
    return {"status":"ok"}

@app.get("/prompts")
def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, content FROM prompts")
    rows = c.fetchall()
    conn.close()
    return [{"name":r[0],"content":r[1]} for r in rows]

@app.post("/load_mock_inbox")
def load_mock_inbox(payload: dict):
    # expects {"path":"../frontend/assets/mock_inbox.json"}
    path = payload.get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=400, detail="mock inbox path missing or not found")
    with open(path, "r") as f:
        emails = json.load(f)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for e in emails:
        c.execute("REPLACE INTO emails(id, json) VALUES (?, ?)", (e["id"], json.dumps(e)))
    conn.commit()
    conn.close()
    return {"loaded": len(emails)}

@app.get("/emails")
def get_emails():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, json FROM emails")
    rows = c.fetchall()
    conn.close()
    return [json.loads(r[1]) for r in rows]

@app.post("/process_email/{email_id}")
def process_email(email_id: str, prompt_names: List[str]):
    """
    For each prompt (categorization, action_item, etc) call LLM and store results.
    prompt_names is a list like ["categorization_prompt","action_item_prompt"].
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT json FROM emails WHERE id=?", (email_id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="email not found")
    email = json.loads(row[0])
    # fetch prompts
    results = {}
    for pname in prompt_names:
        c.execute("SELECT content FROM prompts WHERE name=?", (pname,))
        prow = c.fetchone()
        if not prow:
            results[pname] = {"error":"prompt not found"}
            continue
        prompt_template = prow[0]
        # construct prompt
        prompt = f"{prompt_template}\n\nEMAIL:\nSubject: {email.get('subject')}\nFrom: {email.get('from')}\nBody:\n{email.get('body')}"
        llm_out = call_llm(prompt)
        results[pname] = llm_out
    # store results
    c.execute("REPLACE INTO results(email_id, json) VALUES (?, ?)", (email_id, json.dumps(results)))
    conn.commit()
    conn.close()
    return {"status":"ok","results":results}

@app.get("/results/{email_id}")
def get_results(email_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT json FROM results WHERE email_id=?", (email_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {}
    return json.loads(row[0])

@app.post("/save_draft")
def save_draft(payload: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    did = payload.get("id")
    c.execute("REPLACE INTO drafts(id, json) VALUES (?, ?)", (did, json.dumps(payload)))
    conn.commit()
    conn.close()
    return {"status":"ok"}
