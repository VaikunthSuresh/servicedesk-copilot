"""Streamlit UI for the IT Service Desk Copilot. Owner: Member 4.
Run: streamlit run frontend/app.py   (API_URL defaults to http://localhost:8000)
"""
import os

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000").rstrip("/") + "/api/v1"
PRIORITY_COLOUR = {"P1": "🔴", "P2": "🟠", "P3": "🟢"}
SAMPLES = {
    # --- IT service desk (Sections I and III) ---
    "VPN outage before demo": "VPN keeps disconnecting every 10 minutes since this morning's Windows update. "
                              "I have a client demo at 3pm today and can't access SAP or Jira. Please help urgently!",
    "Suspicious email": "I got an email from 'IT Support' asking me to re-enter my password on a link. I clicked it "
                        "and typed my password before I realised it looked suspicious.",
    "Slow laptop": "My laptop has been really slow for the last week, especially when Teams and Excel are open together.",
    "Email outage for the whole team": "Is there planned maintenance on the email servers tonight? Since 9pm nobody in "
                                       "our team can send or receive mail in Outlook and we have month-end reports due.",
    "Charged twice for a licence": "We were charged twice for our software licence renewal this month. The same invoice "
                                   "appears two times on the company card statement. Please refund the duplicate payment.",
    "Return a damaged headset": "The headset delivered last week arrived with a broken microphone. How do I return it "
                                "and get a replacement?",
    "Pricing for 50 more licences": "We plan to add 50 more user licences next quarter. Can someone share pricing and "
                                    "any volume discount before our budget meeting on Friday?",
    "Long ticket (shows the summariser)": (
        "Hi team, sorry for the long message. I changed my phone over the weekend because the old one stopped charging, "
        "and I set up WhatsApp and my personal apps without any trouble. On Monday morning I tried to log in to my "
        "laptop and Outlook, and the Microsoft Authenticator app on the new phone never shows any approval prompt, so "
        "I am stuck at the sign-in screen. I tried restarting both the phone and the laptop twice and also reinstalled "
        "the Authenticator app, but nothing changed. A colleague said I might need IT to reset something on my account. "
        "I have a project review with my manager at 2pm today and all my slides are in OneDrive, so I really need to get "
        "back in before then. Could someone please help me as soon as possible? Thanks a lot."),
    "Out of scope (chatbot should decline)": "What is on the canteen menu today, and is the office gym open on Saturday?",
    # --- Workplace demo (Section IV): upload data/workplace/*.md in the Knowledge base tab first ---
    "Workplace: GenAI API key": "Hi, I joined the GenAI team last week and still don't have an API key for the internal "
                                "LLM platform. Our proof-of-concept demo to the business is on Friday, can this be sped up?",
    "Workplace: cloud sandbox blocked": "Since this morning all our dev pipelines fail with 'resource creation denied' in "
                                        "the cloud sandbox. The whole team is blocked and we cannot deploy anything to test.",
    "Workplace: public AI chatbot": "Is it okay if I paste a supplier contract PDF into a public AI chatbot to get a quick "
                                    "summary? It would save me a lot of time this week.",
}

st.set_page_config(page_title="IT Service Desk Copilot", page_icon="🎫", layout="wide")
st.title("🎫 IT Service Desk Copilot")
st.caption("Customer Service · Enterprise IT Service Desk — classify, prioritise, summarise, resolve.")

try:
    h = requests.get(API.replace("/api/v1", "/health"), timeout=5).json()
    st.sidebar.success(f"API online · classifier: {h['classifier_mode']} · LLM: {h['llm_model'] if h['llm_configured'] else 'not configured'}")
except Exception:
    st.sidebar.error(f"API not reachable at {API}")

tab_triage, tab_chat, tab_kb = st.tabs(["Ticket triage", "Knowledge chatbot (RAG)", "Knowledge base"])

with tab_triage:
    choice = st.selectbox("Load a sample ticket", ["—"] + list(SAMPLES))
    text = st.text_area("Ticket text", value=SAMPLES.get(choice, ""), height=140)
    if st.button("Triage ticket", type="primary", disabled=len(text) < 3):
        with st.spinner("Running classification → sentiment → summary → RAG → reply..."):
            r = requests.post(f"{API}/triage", json={"text": text}, timeout=180)
        if r.ok:
            d = r.json()
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.metric("Routed to", d["classification"]["label"], f"{d['classification']['score']:.0%} confidence", delta_color="off")
            c2.metric("Priority", f"{PRIORITY_COLOUR.get(d['sentiment']['urgency'], '')} {d['sentiment']['urgency']}",
                      f"sentiment: {d['sentiment']['sentiment']}", delta_color="off")
            c3.metric("Total latency", f"{d['latency_ms']['total']:.0f} ms")
            st.caption(f"Classifier mode: {d['classification']['mode']} · urgency signals: "
                       f"{', '.join(d['sentiment']['urgency_signals']) or 'none'}")
            st.subheader("Summary for agent")
            st.info(d["summary"]["summary"])
            st.subheader("Suggested resolution (from knowledge base)")
            st.markdown(d["suggested_resolution"]["answer"])
            for i, s in enumerate(d["suggested_resolution"]["sources"], 1):
                with st.expander(f"[{i}] {s['source']} · relevance {s['score']:.2f}"):
                    st.write(s["text"])
            st.subheader("Draft reply to employee")
            st.text_area("Reply", d["draft_reply"], height=140, label_visibility="collapsed")
            with st.expander("Raw API response / per-step latency"):
                st.json(d)
        else:
            st.error(f"{r.status_code}: {r.text}")

with tab_chat:
    st.session_state.setdefault("history", [])
    for role, msg in st.session_state.history:
        st.chat_message(role).markdown(msg)
    if q := st.chat_input("Ask about VPN, passwords, MFA, printers, SLAs..."):
        st.chat_message("user").markdown(q)
        r = requests.post(f"{API}/chat", json={"question": q}, timeout=120).json()
        srcs = "\n".join(f"- [{i}] `{s['source']}` (score {s['score']:.2f})" for i, s in enumerate(r["sources"], 1))
        ans = r["answer"] + (f"\n\n**Sources**\n{srcs}" if srcs else "")
        st.chat_message("assistant").markdown(ans)
        st.session_state.history += [("user", q), ("assistant", ans)]

with tab_kb:
    st.write("Upload your organisation's SOPs, runbooks or KB articles (PDF, DOCX, MD, TXT). "
             "Use anonymised or synthetic copies only.")
    files = st.file_uploader("Documents", type=["pdf", "docx", "md", "txt"], accept_multiple_files=True)
    if files and st.button("Ingest"):
        r = requests.post(f"{API}/ingest", files=[("files", (f.name, f.getvalue())) for f in files], timeout=300)
        if r.ok:
            d = r.json()
            st.success(f"Ingested {len(d['files'])} file(s): {', '.join(d['files'])} — "
                       f"{d['chunks_added']} chunks added, {d['total_chunks']} chunks in the knowledge base.")
        else:
            st.error(r.text)
