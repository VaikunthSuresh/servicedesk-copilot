"""Capture every screenshot the report needs, plus the raw API responses behind them.

Prerequisites (one-time, in your venv):
    pip install playwright && playwright install chromium

Start the app first (two terminals, from the repo root):
    cd backend && uvicorn app.main:app --port 8000
    streamlit run frontend/app.py

Then:
    python scripts/capture_screenshots.py            # everything (Sections I, III, IV)
    python scripts/capture_screenshots.py --only 4   # just one section

Output:
    docs/screenshots/*.png     screenshots, numbered in report order
    docs/screenshots/api/*.json  the API responses shown in them (evidence + latency numbers)
"""
import argparse
import json
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
API_OUT = OUT / "api"
WORKPLACE = ROOT / "data" / "workplace"

SAMPLE_TICKETS = {
    "vpn_outage": "VPN keeps disconnecting every 10 minutes since this morning's Windows update. I have a client demo "
                  "at 3pm today and can't access SAP or Jira. Please help urgently!",
    "phishing": "I got an email from 'IT Support' asking me to re-enter my password on a link. I clicked it and typed "
                "my password before I realised it looked suspicious.",
    "slow_laptop": "My laptop has been really slow for the last week, especially when Teams and Excel are open together.",
}
CHAT_QUESTIONS = {
    "vpn": "vpn on my macbook says connected but nothing loads after upgrading macOS",
    "policy_usb": "can I copy project files to my own USB stick",
    "out_of_scope": "what's on the canteen menu today",
}
WORKPLACE_TICKETS = {
    "genai_key": "Hi, I joined the GenAI team last week and still don't have an API key for the internal LLM platform. "
                 "Our proof-of-concept demo to the business is on Friday, can this be sped up?",
    "sandbox_budget": "Since this morning all our dev pipelines fail with 'resource creation denied' in the cloud sandbox. "
                      "The whole team is blocked and we cannot deploy anything to test.",
    "public_ai": "Is it okay if I paste a supplier contract PDF into a public AI chatbot to get a quick summary? "
                 "It would save me a lot of time this week.",
}
WORKPLACE_QUESTIONS = {
    "quota_429": "our LLM calls started failing with error 429 today, what does that mean and when does it reset",
    "repo_access": "how do I get access to another team's code repository",
}

p = argparse.ArgumentParser()
p.add_argument("--ui", default="http://localhost:8501")
p.add_argument("--api", default="http://localhost:8000")
p.add_argument("--only", choices=["1", "3", "4"], help="capture one section only")
a = p.parse_args()
OUT.mkdir(parents=True, exist_ok=True)
API_OUT.mkdir(parents=True, exist_ok=True)


def save_json(name, data):
    (API_OUT / f"{name}.json").write_text(json.dumps(data, indent=2))


def api(path, **kw):
    r = httpx.post(f"{a.api}{path}", timeout=240, **kw) if kw else httpx.get(f"{a.api}{path}", timeout=60)
    r.raise_for_status()
    return r.json()


def shot(page, name):
    """Screenshot the Streamlit content area (cropped to the content, not the whole tall viewport)."""
    page.wait_for_timeout(800)
    target = page.locator('[data-testid="stMainBlockContainer"]')
    (target if target.count() else page).screenshot(path=str(OUT / f"{name}.png"))
    print("  saved", f"{name}.png")


def open_ui(page, tab=None):
    page.goto(a.ui)
    page.wait_for_selector("text=IT Service Desk Copilot", timeout=60_000)
    page.wait_for_selector("text=API online", timeout=60_000)
    if tab:
        page.get_by_role("tab", name=tab).click()
        page.wait_for_timeout(500)


def triage_ui(page, name, text):
    open_ui(page)
    box = page.get_by_label("Ticket text")
    box.fill(text)
    box.press("Tab")  # commit the value so Streamlit enables the button
    btn = page.get_by_role("button", name="Triage ticket")
    btn.wait_for(state="visible")
    page.wait_for_function("() => [...document.querySelectorAll('button')].some(b => b.innerText.includes('Triage ticket') && !b.disabled)", timeout=30_000)
    btn.click()
    page.wait_for_selector("text=Draft reply to employee", timeout=240_000)
    shot(page, name)


def chat_ui(page, name, question):
    open_ui(page, "Knowledge chatbot (RAG)")
    page.get_by_test_id("stChatInputTextArea").fill(question)
    page.get_by_test_id("stChatInputTextArea").press("Enter")
    page.wait_for_function("() => document.querySelectorAll('[data-testid=\"stChatMessage\"]').length >= 2", timeout=240_000)
    # expand the sources list is plain markdown; nothing to click
    shot(page, name)


def section1(page):
    print("Section I")
    save_json("health", api("/health"))
    page.goto(f"{a.api}/docs")
    try:  # Swagger UI loads its JS from a CDN; needs internet access
        page.wait_for_selector(".opblock", timeout=30_000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "01_swagger_docs.png"), full_page=True)
        print("  saved 01_swagger_docs.png")
    except Exception:
        print("  WARN: Swagger UI did not load (no internet?) - open http://localhost:8000/docs and screenshot it manually")
    page.goto(f"{a.api}/health")
    page.screenshot(path=str(OUT / "02_health.png"))
    print("  saved 02_health.png")
    for i, (key, text) in enumerate(SAMPLE_TICKETS.items(), 3):
        t = time.perf_counter()
        save_json(f"triage_{key}", api("/api/v1/triage", json={"text": text}))
        print(f"  API /triage {key}: {time.perf_counter() - t:.1f}s")
        triage_ui(page, f"{i:02d}_triage_{key}", text)


def section3(page):
    print("Section III")
    for i, (key, q) in enumerate(CHAT_QUESTIONS.items(), 10):
        save_json(f"chat_{key}", api("/api/v1/chat", json={"question": q}))
        chat_ui(page, f"{i:02d}_chat_{key}", q)


def section4(page):
    print("Section IV")
    docs = sorted(WORKPLACE.glob("*.md"))
    docs = [d for d in docs if d.name.lower() != "readme.md"]
    open_ui(page, "Knowledge base")
    page.locator('input[type="file"]').set_input_files([str(d) for d in docs])
    page.get_by_role("button", name="Ingest").click()
    page.wait_for_selector("text=chunks added", timeout=240_000)
    shot(page, "20_kb_upload_workplace_docs")
    for i, (key, text) in enumerate(WORKPLACE_TICKETS.items(), 21):
        save_json(f"workplace_triage_{key}", api("/api/v1/triage", json={"text": text}))
        triage_ui(page, f"{i:02d}_workplace_triage_{key}", text)
    for i, (key, q) in enumerate(WORKPLACE_QUESTIONS.items(), 25):
        save_json(f"workplace_chat_{key}", api("/api/v1/chat", json={"question": q}))
        chat_ui(page, f"{i:02d}_workplace_chat_{key}", q)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 2400}, device_scale_factor=2)
    if a.only in (None, "1"):
        section1(page)
    if a.only in (None, "3"):
        section3(page)
    if a.only in (None, "4"):
        section4(page)
    browser.close()
print(f"\nDone. Screenshots in {OUT}")
