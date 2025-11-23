# frontend/streamlit_app.py
import streamlit as st
import requests, json, os

import streamlit as st

BACKEND = st.secrets["backend_url"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


st.set_page_config(page_title="Prompt-Driven Email Agent", layout="wide")

st.title("Prompt-Driven Email Productivity Agent")

# Sidebar: Prompt Brain
st.sidebar.header("Prompt Brain")
if "prompts" not in st.session_state:
    # fetch prompts from backend
    try:
        resp = requests.get(f"{BACKEND}/prompts")
        st.session_state.prompts = {p["name"]: p["content"] for p in resp.json()}
    except:
        st.session_state.prompts = {}

# Show editable prompts
with st.sidebar.form("prompt_form"):
    categorization = st.text_area("Categorization Prompt", value=st.session_state.prompts.get("categorization_prompt",""))
    action_item = st.text_area("Action Item Prompt", value=st.session_state.prompts.get("action_item_prompt",""))
    auto_reply = st.text_area("Auto-Reply Prompt", value=st.session_state.prompts.get("auto_reply_prompt",""))
    submitted = st.form_submit_button("Save Prompts")
    if submitted:
        for name, content in [("categorization_prompt", categorization),("action_item_prompt", action_item),("auto_reply_prompt", auto_reply)]:
            requests.post(f"{BACKEND}/prompts", json={"name":name,"content":content})
        st.sidebar.success("Prompts saved")

# Top: load mock inbox
st.markdown("### Inbox")
col1, col2 = st.columns([1,3])
with col1:
    if st.button("Load Mock Inbox"):
        path = os.path.join(os.path.dirname(__file__), "assets", "mock_inbox.json")
        r = requests.post(f"{BACKEND}/load_mock_inbox", json={"path": path})
        st.success(f"Loaded: {r.json().get('loaded')} emails")

    emails = []
    try:
        resp = requests.get(f"{BACKEND}/emails")
        emails = resp.json()
    except Exception as e:
        st.write("Could not fetch emails from backend.")

    # Email list
    selected_id = st.selectbox("Select an email", options=[e["id"] for e in emails] if emails else [])
    if selected_id:
        selected_email = next(e for e in emails if e["id"]==selected_id)
        st.write("From:", selected_email["from"])
        st.write("Subject:", selected_email["subject"])
        st.write("Timestamp:", selected_email["timestamp"])
        if st.button("Run processing (categorize + extract)"):
            # call backend to process
            r = requests.post(f"{BACKEND}/process_email/{selected_id}", json=["categorization_prompt","action_item_prompt"])
            st.write("Processing results saved.")

with col2:
    if selected_id:
        st.subheader("Email content")
        st.write(selected_email["body"])
        # fetch results
        r = requests.get(f"{BACKEND}/results/{selected_id}")
        res = r.json()
        st.subheader("LLM Results")
        st.json(res)
        st.subheader("Email Agent")
        query = st.text_input("Ask the agent (e.g., 'Summarize this email', 'What tasks do I need to do?')")
        if st.button("Ask Agent"):
            # choose prompt based on query heuristics
            if "task" in query.lower() or "what do i need" in query.lower():
                p = st.session_state.prompts.get("action_item_prompt")
            elif "summar" in query.lower():
                p = st.session_state.prompts.get("summarize_prompt","Summarize this email.")
            else:
                p = st.session_state.prompts.get("auto_reply_prompt")
            prompt = f"{p}\n\nEMAIL:\nSubject:{selected_email['subject']}\n{selected_email['body']}\n\nUSER_QUERY: {query}"
            # call backend LLM endpoint directly (we didn't expose a special endpoint, so reuse process_email code path)
            # For demo: call /process_email with a custom prompt name saved temporarily as 'ad-hoc'
            requests.post(f"{BACKEND}/prompts", json={"name":"ad_hoc_prompt","content":prompt})
            r2 = requests.post(f"{BACKEND}/process_email/{selected_id}", json=["ad_hoc_prompt"])
            results = r2.json().get("results",{})
            st.json(results.get("ad_hoc_prompt"))
            # If results look like a reply, provide Save Draft button
            if st.button("Save as draft"):
                # create a simple draft object
                draft = {"id": f"draft_{selected_id}", "email_id": selected_id, "draft": results.get("ad_hoc_prompt")}
                requests.post(f"{BACKEND}/save_draft", json=draft)
                st.success("Draft saved (not sent).")
