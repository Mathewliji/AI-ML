import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(
    page_title="Receipt Tracker AI",
    page_icon="🧾",
    layout="centered",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

/* ── Tokens ── */
:root {
  --bg:           #0B0F14;
  --bg-sidebar:   #0E1319;
  --bg-card:      #141C26;
  --bg-elevated:  #1A2535;
  --bubble-user:  #163426;
  --bubble-bot:   #161E2A;
  --text:         #E4EAF0;
  --text-sub:     #7A8FA6;
  --text-muted:   #3D5166;
  --accent:       #25D366;
  --accent-dark:  #1AAF52;
  --accent-glow:  rgba(37,211,102,0.15);
  --accent-glow2: rgba(37,211,102,0.06);
  --border:       rgba(255,255,255,0.06);
  --border-accent:rgba(37,211,102,0.25);
  --radius:       14px;
  --radius-sm:    8px;
  --font-display: 'Bricolage Grotesque', sans-serif;
  --font-body:    'DM Sans', sans-serif;
}

/* ── Reset & global ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
  background: var(--bg) !important;
  font-family: var(--font-body) !important;
  color: var(--text) !important;
}

/* Subtle grid texture on background */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(37,211,102,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,211,102,0.015) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div {
  padding: 1.5rem 1.2rem !important;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
  font-family: var(--font-display) !important;
  font-size: 0.75rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--text-sub) !important;
  margin: 1.5rem 0 0.75rem !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
  color: var(--text) !important;
}

/* ── Sidebar file uploader ── */
[data-testid="stFileUploader"] {
  background: var(--bg-card) !important;
  border: 1.5px dashed var(--border-accent) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploaderDropzoneInstructions"] span {
  color: var(--text-sub) !important;
  font-family: var(--font-body) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] svg {
  fill: var(--accent) !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-glow2) !important;
}

/* ── Sidebar image preview ── */
[data-testid="stImage"] img {
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
}

/* ── Buttons ── */
.stButton > button {
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.02em !important;
  border-radius: 999px !important;
  border: none !important;
  transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid*="primary"] {
  background: var(--accent) !important;
  color: #0B1A10 !important;
  box-shadow: 0 0 20px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent-dark) !important;
  box-shadow: 0 0 28px rgba(37,211,102,0.3) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--bg-elevated) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button:not([kind="primary"]):hover {
  background: var(--bg-card) !important;
  border-color: var(--border-accent) !important;
  color: var(--accent) !important;
}

/* ── Divider ── */
hr {
  border-color: var(--border) !important;
  margin: 1rem 0 !important;
}

/* ── Chat container ── */
.main .block-container {
  padding-top: 1rem !important;
  max-width: 720px !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 4px 0 !important;
  gap: 10px !important;
}

/* Avatar circles */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
  width: 32px !important;
  height: 32px !important;
  border-radius: 50% !important;
  flex-shrink: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
  background: var(--accent) !important;
}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-accent) !important;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessageContent {
  background: var(--bubble-user) !important;
  border: 1px solid rgba(37,211,102,0.18) !important;
  border-radius: 18px 4px 18px 18px !important;
  padding: 12px 16px !important;
  margin-left: 10% !important;
  box-shadow: 0 2px 12px rgba(37,211,102,0.08) !important;
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stChatMessageContent {
  background: var(--bubble-bot) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px 18px 18px 18px !important;
  padding: 12px 16px !important;
  margin-right: 10% !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
}

/* All bubble text */
[data-testid="stChatMessage"] .stMarkdown p,
[data-testid="stChatMessage"] .stMarkdown li,
[data-testid="stChatMessage"] .stMarkdown span,
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span {
  color: var(--text) !important;
  font-family: var(--font-body) !important;
  font-size: 0.9rem !important;
  line-height: 1.6 !important;
}
[data-testid="stChatMessage"] .stMarkdown strong {
  color: #ffffff !important;
  font-weight: 600 !important;
}
[data-testid="stChatMessage"] .stMarkdown em {
  color: var(--text-sub) !important;
  font-style: italic !important;
}
[data-testid="stChatMessage"] .stMarkdown code {
  background: rgba(37,211,102,0.12) !important;
  color: var(--accent) !important;
  border-radius: 4px !important;
  padding: 1px 5px !important;
  font-size: 0.82rem !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
  background: var(--bg-card) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 999px !important;
  color: var(--text) !important;
  font-family: var(--font-body) !important;
  transition: border-color 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--border-accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
[data-testid="stChatInput"] textarea {
  color: var(--text) !important;
  background: transparent !important;
  font-family: var(--font-body) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: var(--text-muted) !important;
}
.stChatInputContainer {
  background: transparent !important;
  padding-bottom: 1rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] p {
  color: var(--text-sub) !important;
  font-family: var(--font-body) !important;
}
[data-testid="stSpinner"] svg circle {
  stroke: var(--accent) !important;
}

/* ── Error/success alerts ── */
[data-testid="stAlert"] {
  background: rgba(255,75,75,0.1) !important;
  border: 1px solid rgba(255,75,75,0.25) !important;
  border-radius: var(--radius-sm) !important;
  color: #FF8080 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--bg-elevated);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Header ── */
.rt-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.rt-header::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--accent);
  border-radius: 3px 0 0 3px;
}
.rt-header::after {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 120px; height: 120px;
  background: radial-gradient(circle, var(--accent-glow), transparent 70%);
  pointer-events: none;
}
.rt-icon {
  width: 44px; height: 44px;
  background: var(--accent-glow);
  border: 1px solid var(--border-accent);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}
.rt-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  line-height: 1.2;
}
.rt-subtitle {
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--text-sub);
  margin: 2px 0 0;
  letter-spacing: 0.01em;
}
.rt-dot {
  width: 7px; height: 7px;
  background: var(--accent);
  border-radius: 50%;
  display: inline-block;
  margin-right: 5px;
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.8); }
}
.rt-badge {
  margin-left: auto;
  background: var(--accent-glow);
  border: 1px solid var(--border-accent);
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 3px 9px;
  border-radius: 999px;
  flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rt-header">
  <div class="rt-icon">🧾</div>
  <div>
    <p class="rt-title">Receipt Tracker AI</p>
    <p class="rt-subtitle">
      <span class="rt-dot"></span>Claude Vision &nbsp;·&nbsp; LangGraph &nbsp;·&nbsp; PostgreSQL
    </p>
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
        "Choose a receipt image",
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

                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📸 *Uploaded:* `{uploaded.name}`",
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["message"],
                    })
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
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "\n".join(lines),
                })
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"API error: {exc}")

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Ask about your spending…"):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
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

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
