import os
import re
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(
    page_title="Receipt Tracker AI",
    page_icon="🧾",
    layout="centered",
)

# ── Markdown → safe HTML (handles bold, italic, code, newlines, bullets) ──────
def _md(text: str) -> str:
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', t)
    t = re.sub(r'`(.+?)`',       r'<code>\1</code>', t)
    t = t.replace("\n", "<br>")
    return t

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

:root {
  --bg:            #0B0F14;
  --bg-sidebar:    #0E1319;
  --bg-card:       #141C26;
  --bg-elevated:   #1A2535;
  --bubble-user:   #163426;
  --bubble-bot:    #161E2A;
  --text:          #E4EAF0;
  --text-sub:      #7A8FA6;
  --text-muted:    #3D5166;
  --accent:        #25D366;
  --accent-dark:   #1AAF52;
  --accent-glow:   rgba(37,211,102,0.15);
  --accent-glow2:  rgba(37,211,102,0.06);
  --border:        rgba(255,255,255,0.07);
  --border-accent: rgba(37,211,102,0.28);
  --radius:        14px;
  --radius-sm:     8px;
  --font-d:        'Bricolage Grotesque', sans-serif;
  --font-b:        'DM Sans', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

/* ── App shell ── */
.stApp {
  background: var(--bg) !important;
  font-family: var(--font-b) !important;
  color: var(--text) !important;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0;
  background-image:
    linear-gradient(rgba(37,211,102,0.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,211,102,0.018) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none; z-index: 0;
}
.main .block-container {
  padding-top: 0.75rem !important;
  max-width: 720px !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 1.4rem 1.1rem !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: var(--text) !important; font-family: var(--font-b) !important; }
section[data-testid="stSidebar"] h2 {
  font-family: var(--font-d) !important; font-size: 0.72rem !important;
  font-weight: 700 !important; letter-spacing: 0.12em !important;
  text-transform: uppercase !important; color: var(--text-sub) !important;
  margin: 1.4rem 0 0.6rem !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--bg-card) !important;
  border: 1.5px dashed var(--border-accent) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stFileUploader"] *,
[data-testid="stFileUploaderDropzoneInstructions"] * { color: var(--text-sub) !important; }
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ── Buttons ── */
.stButton > button {
  font-family: var(--font-d) !important; font-weight: 600 !important;
  font-size: 0.84rem !important; border-radius: 999px !important;
  border: none !important; transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"] {
  background: var(--accent) !important; color: #071A0E !important;
  box-shadow: 0 0 22px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent-dark) !important;
  box-shadow: 0 0 32px rgba(37,211,102,0.3) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--bg-elevated) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--border-accent) !important; color: var(--accent) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 0.9rem 0 !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: var(--text-sub) !important; font-family: var(--font-b) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
  background: rgba(255,75,75,0.08) !important;
  border: 1px solid rgba(255,75,75,0.22) !important;
  border-radius: var(--radius-sm) !important; color: #FF8080 !important;
}

/* ── Chat input (bottom bar) ── */
[data-testid="stChatInput"],
[data-testid="stChatInputContainer"] textarea,
.stChatInputContainer {
  background: var(--bg-card) !important;
  color: var(--text) !important;
  font-family: var(--font-b) !important;
}
[data-testid="stChatInput"] {
  border: 1.5px solid var(--border) !important;
  border-radius: 999px !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--border-accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }
.stChatInputContainer { background: transparent !important; padding-bottom: 1rem !important; }

/* ── Custom chat bubbles ── */
.chat-wrap { display: flex; flex-direction: column; gap: 10px; padding: 4px 0 12px; }
.msg-row   { display: flex; align-items: flex-end; gap: 8px; }
.msg-user  { justify-content: flex-end; }
.msg-bot   { justify-content: flex-start; }

.bubble {
  max-width: 76%; padding: 11px 15px;
  font-family: var(--font-b); font-size: 0.9rem; line-height: 1.65;
  color: var(--text); word-break: break-word;
}
.bubble-user {
  background: var(--bubble-user);
  border: 1px solid rgba(37,211,102,0.22);
  border-radius: 18px 4px 18px 18px;
  color: #DFF2E8;
  box-shadow: 0 2px 14px rgba(37,211,102,0.09);
}
.bubble-bot {
  background: var(--bubble-bot);
  border: 1px solid var(--border);
  border-radius: 4px 18px 18px 18px;
  color: var(--text);
  box-shadow: 0 2px 14px rgba(0,0,0,0.22);
}
.bubble strong { color: #ffffff; font-weight: 600; }
.bubble em     { color: #9DB4C8; }
.bubble code   {
  background: rgba(37,211,102,0.13); color: var(--accent);
  border-radius: 4px; padding: 1px 5px; font-size: 0.81rem;
}
.avatar {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 0.85rem;
}
.avatar-user { background: var(--accent); color: #071A0E; order: 2; }
.avatar-bot  { background: var(--bg-elevated); border: 1px solid var(--border-accent); order: 0; }

/* ── Header ── */
.rt-header {
  display: flex; align-items: center; gap: 13px;
  padding: 14px 18px; margin-bottom: 18px;
  background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
  position: relative; overflow: hidden;
}
.rt-header::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; background: var(--accent); border-radius: 3px 0 0 3px;
}
.rt-header::after {
  content: ''; position: absolute; top: -50px; right: -50px;
  width: 130px; height: 130px;
  background: radial-gradient(circle, var(--accent-glow), transparent 70%);
  pointer-events: none;
}
.rt-icon {
  width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
  background: var(--accent-glow2); border: 1px solid var(--border-accent);
  display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
}
.rt-title {
  font-family: var(--font-d); font-size: 1.1rem; font-weight: 700;
  color: #fff; margin: 0; line-height: 1.2;
}
.rt-sub {
  font-family: var(--font-b); font-size: 0.72rem; color: var(--text-sub);
  margin: 3px 0 0; letter-spacing: 0.01em;
}
.rt-dot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); margin-right: 5px;
  animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.45;transform:scale(.75)} }
.rt-badge {
  margin-left: auto; flex-shrink: 0;
  background: var(--accent-glow2); border: 1px solid var(--border-accent);
  color: var(--accent); font-family: var(--font-d); font-size: 0.62rem;
  font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 999px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rt-header">
  <div class="rt-icon">🧾</div>
  <div>
    <p class="rt-title">Receipt Tracker AI</p>
    <p class="rt-sub"><span class="rt-dot"></span>Claude Vision &nbsp;·&nbsp; LangGraph &nbsp;·&nbsp; PostgreSQL</p>
  </div>
  <span class="rt-badge">Mock Mode</span>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm your AI expense assistant.\n\n"
                "📸 **Upload a receipt** in the sidebar — I'll extract every detail instantly.\n"
                "💬 Or **ask me anything** — *'show me this week's food spending'*, "
                "*'what's my biggest expense category?'*, etc."
            ),
        }
    ]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📎 Upload Receipt")
    uploaded = st.file_uploader(
        "Drop a receipt image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded:
        st.image(uploaded, caption="Preview", use_container_width=True)

        if st.button("⚡ Process with AI", use_container_width=True, type="primary"):
            with st.spinner("Extracting receipt data…"):
                try:
                    resp = requests.post(
                        f"{API_URL}/receipts/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.messages.append(
                        {"role": "user", "content": f"📸 *Uploaded:* `{uploaded.name}`"}
                    )
                    st.session_state.messages.append(
                        {"role": "assistant", "content": data["message"]}
                    )
                    st.rerun()
                except requests.exceptions.RequestException as exc:
                    st.error(f"API error: {exc}")

    st.divider()
    st.markdown("## 📊 Quick Reports")

    if st.button("This month's summary", use_container_width=True):
        with st.spinner("Fetching…"):
            try:
                resp = requests.get(f"{API_URL}/reports/summary?days=30", timeout=10)
                resp.raise_for_status()
                summary = resp.json()
                lines = [f"**Grand total:** ${summary['grand_total']:.2f}\n"]
                for cat, vals in summary["by_category"].items():
                    lines.append(f"• {cat}: ${vals['total']:.2f} ({vals['count']} receipts)")
                st.session_state.messages.append(
                    {"role": "assistant", "content": "\n".join(lines)}
                )
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"API error: {exc}")

# ── Chat history — rendered as guaranteed HTML divs ───────────────────────────
rows = ""
for msg in st.session_state.messages:
    content = _md(msg["content"])
    if msg["role"] == "user":
        rows += (
            f'<div class="msg-row msg-user">'
            f'  <div class="bubble bubble-user">{content}</div>'
            f'  <div class="avatar avatar-user">👤</div>'
            f'</div>'
        )
    else:
        rows += (
            f'<div class="msg-row msg-bot">'
            f'  <div class="avatar avatar-bot">🤖</div>'
            f'  <div class="bubble bubble-bot">{content}</div>'
            f'</div>'
        )

st.markdown(f'<div class="chat-wrap">{rows}</div>', unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Ask about your spending…"):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking…"):
        try:
            resp = requests.post(
                f"{API_URL}/receipts/chat",
                json={"message": user_input},
                timeout=30,
            )
            resp.raise_for_status()
            reply = resp.json()["response"]
        except requests.exceptions.RequestException as exc:
            reply = f"❌ Couldn't reach the API: {exc}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
