import os
import re
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(page_title="Receipt Tracker AI", page_icon="🧾", layout="centered")

# ── Theme state ───────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK = st.session_state.dark_mode

# ── Theme tokens ──────────────────────────────────────────────────────────────
if DARK:
    T = dict(
        bg="#0B0F14", sidebar="#0E1319", card="#141C26", elevated="#1A2535",
        text="#E4EAF0", text_sub="#7A8FA6", text_muted="#3D5166",
        border="rgba(255,255,255,0.07)", border_acc="rgba(37,211,102,0.28)",
        bub_u_bg="#163426", bub_u_txt="#DFF2E8",
        bub_b_bg="#161E2A", bub_b_txt="#E4EAF0",
        av_bot_bg="#1A2535", strong="#ffffff", em="#9DB4C8",
        hdr_bg="#141C26", hdr_border="rgba(255,255,255,0.07)",
        title_c="#ffffff", sub_c="#7A8FA6",
    )
else:
    T = dict(
        bg="#F5F7FA", sidebar="#EAECF0", card="#FFFFFF", elevated="#E2E8F0",
        text="#1A202C", text_sub="#4A5568", text_muted="#A0AEC0",
        border="rgba(0,0,0,0.08)", border_acc="rgba(37,211,102,0.5)",
        bub_u_bg="#DCF8C6", bub_u_txt="#0D3B20",
        bub_b_bg="#FFFFFF",  bub_b_txt="#1A202C",
        av_bot_bg="#E2E8F0", strong="#0D3B20", em="#4A5568",
        hdr_bg="#FFFFFF", hdr_border="rgba(0,0,0,0.08)",
        title_c="#1A202C", sub_c="#4A5568",
    )

# ── Markdown → safe HTML with theme-aware inline colours ─────────────────────
def _md(text: str) -> str:
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r'\*\*(.+?)\*\*',
               rf'<strong style="color:{T["strong"]};font-weight:600">\1</strong>', t)
    t = re.sub(r'\*(.+?)\*',
               rf'<em style="color:{T["em"]};font-style:italic">\1</em>', t)
    t = re.sub(r'`(.+?)`',
               r'<code style="background:rgba(37,211,102,0.15);color:#25D366;'
               r'border-radius:4px;padding:1px 6px;font-size:0.82rem">\1</code>', t)
    t = t.replace("\n", "<br>")
    return t

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

:root {{
  --bg:           {T["bg"]};
  --sidebar:      {T["sidebar"]};
  --card:         {T["card"]};
  --elevated:     {T["elevated"]};
  --text:         {T["text"]};
  --text-sub:     {T["text_sub"]};
  --text-muted:   {T["text_muted"]};
  --accent:       #25D366;
  --accent-dark:  #1AAF52;
  --accent-glow:  rgba(37,211,102,0.15);
  --border:       {T["border"]};
  --border-acc:   {T["border_acc"]};
  --radius:       14px;
  --font-d:       'Bricolage Grotesque', sans-serif;
  --font-b:       'DM Sans', sans-serif;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

.stApp {{
  background: var(--bg) !important;
  font-family: var(--font-b) !important;
  color: var(--text) !important;
}}
.main .block-container {{
  padding-top: 0.75rem !important;
  max-width: 720px !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] > div {{
  padding: 1rem 1rem !important;
}}

/* Sidebar text */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {{
  color: var(--text) !important;
  font-family: var(--font-b) !important;
}}

/* Sidebar section headings — proper size, no truncation */
section[data-testid="stSidebar"] h2 {{
  font-family: var(--font-d) !important;
  font-size: 0.9rem !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  margin: 1rem 0 0.5rem !important;
  white-space: normal !important;
  overflow: visible !important;
  line-height: 1.3 !important;
}}

/* ── File uploader box ── */
[data-testid="stFileUploader"] {{
  background: var(--card) !important;
  border: 1.5px dashed var(--border-acc) !important;
  border-radius: var(--radius) !important;
}}
[data-testid="stFileUploader"]:hover {{
  border-color: var(--accent) !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] p {{
  color: var(--text-sub) !important;
}}

/* Browse files button — stays natural inside the dashed box */
[data-testid="stFileUploader"] button {{
  border-radius: 8px !important;
  border: 1px solid var(--border-acc) !important;
  background: transparent !important;
  color: var(--accent) !important;
  font-size: 0.8rem !important;
  width: auto !important;
  margin-top: 0 !important;
  box-shadow: none !important;
}}

/* ── Sidebar action buttons (pill) ── */
section[data-testid="stSidebar"] .stButton > button {{
  font-family: var(--font-d) !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  border-radius: 999px !important;
  width: 100% !important;
  transition: all 0.18s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: var(--accent) !important;
  color: #071A0E !important;
  border: none !important;
  box-shadow: 0 0 20px var(--accent-glow) !important;
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
  background: var(--accent-dark) !important;
  box-shadow: 0 0 28px rgba(37,211,102,0.3) !important;
  transform: translateY(-1px) !important;
}}
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {{
  background: var(--elevated) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {{
  border-color: var(--border-acc) !important;
  color: var(--accent) !important;
}}

/* Override the Browse files button BACK after the sidebar pill rule */
[data-testid="stFileUploader"] button {{
  border-radius: 8px !important;
  width: auto !important;
  background: transparent !important;
  color: var(--accent) !important;
  border: 1px solid var(--border-acc) !important;
  box-shadow: none !important;
  transform: none !important;
}}

/* ── Theme toggle button in sidebar — small, top-right ── */
.theme-toggle-wrap {{
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}}

/* ── Divider ── */
hr {{ border-color: var(--border) !important; margin: 0.75rem 0 !important; }}

/* ── Spinner ── */
[data-testid="stSpinner"] p {{
  color: var(--text-sub) !important;
  font-family: var(--font-b) !important;
}}

/* ── Alerts ── */
[data-testid="stAlert"] {{
  border-radius: 8px !important;
  color: var(--text) !important;
}}

/* ── Chat input ── */
[data-testid="stChatInput"] {{
  border: 1.5px solid var(--border) !important;
  border-radius: 999px !important;
  background: var(--card) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stChatInput"]:focus-within {{
  border-color: var(--border-acc) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}}
[data-testid="stChatInput"] textarea {{
  color: var(--text) !important;
  background: transparent !important;
  font-family: var(--font-b) !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
  color: var(--text-muted) !important;
}}
.stChatInputContainer {{
  background: transparent !important;
  padding-bottom: 1rem !important;
}}

/* ── Header card ── */
.rt-header {{
  display: flex; align-items: center; gap: 13px;
  padding: 14px 18px; margin-bottom: 18px;
  background: {T["hdr_bg"]}; border: 1px solid {T["hdr_border"]};
  border-radius: var(--radius); position: relative; overflow: hidden;
}}
.rt-header::before {{
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; background: var(--accent); border-radius: 3px 0 0 3px;
}}
.rt-header::after {{
  content: ''; position: absolute; top: -50px; right: -50px;
  width: 130px; height: 130px;
  background: radial-gradient(circle, rgba(37,211,102,0.12), transparent 70%);
  pointer-events: none;
}}
.rt-icon {{
  width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
  background: rgba(37,211,102,0.08); border: 1px solid {T["border_acc"]};
  display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
}}
.rt-title {{
  font-family: var(--font-d); font-size: 1.1rem; font-weight: 700;
  color: {T["title_c"]}; margin: 0; line-height: 1.2;
}}
.rt-sub {{
  font-family: var(--font-b); font-size: 0.72rem; color: {T["sub_c"]};
  margin: 3px 0 0;
}}
.rt-dot {{
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); margin-right: 5px;
  animation: blink 2s ease-in-out infinite;
}}
@keyframes blink {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.45;transform:scale(.75)}} }}
.rt-badge {{
  margin-left: auto; flex-shrink: 0;
  background: rgba(37,211,102,0.08); border: 1px solid {T["border_acc"]};
  color: var(--accent); font-family: var(--font-d); font-size: 0.62rem;
  font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 999px;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--elevated); border-radius: 4px; }}
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

    # Light / Dark toggle — top of sidebar
    col_lbl, col_btn = st.columns([2, 1])
    with col_lbl:
        st.markdown(
            f"<p style='margin:0;padding-top:6px;font-size:0.8rem;"
            f"color:{T['text_sub']};font-family:DM Sans,sans-serif;'>"
            f"{'🌙 Dark mode' if DARK else '☀️ Light mode'}</p>",
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("☀️" if DARK else "🌙", key="theme_toggle"):
            st.session_state.dark_mode = not DARK
            st.rerun()

    st.divider()

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

# ── Chat history — fully inline-styled, immune to theme cascade ───────────────
_ROW   = "display:flex;align-items:flex-end;gap:8px;margin-bottom:10px;"
_BBASE = ("max-width:76%;padding:12px 16px;border-radius:{r};"
          "font-family:'DM Sans',sans-serif;font-size:0.9rem;"
          "line-height:1.65;word-break:break-word;color:{c};background:{bg};")
_BUSER = _BBASE.format(
    r="18px 4px 18px 18px", c=T["bub_u_txt"], bg=T["bub_u_bg"]
) + "border:1px solid rgba(37,211,102,0.25);box-shadow:0 2px 12px rgba(37,211,102,0.08);"

_BBOT  = _BBASE.format(
    r="4px 18px 18px 18px", c=T["bub_b_txt"], bg=T["bub_b_bg"]
) + f"border:1px solid {T['border']};box-shadow:0 2px 12px rgba(0,0,0,0.1);"

_AV    = "width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.85rem;flex-shrink:0;"
_AVUSR = _AV + "background:#25D366;color:#071A0E;order:2;"
_AVBOT = _AV + f"background:{T['av_bot_bg']};border:1px solid {T['border_acc']};order:0;"

rows = ""
for msg in st.session_state.messages:
    content = _md(msg["content"])
    if msg["role"] == "user":
        rows += (f'<div style="{_ROW}justify-content:flex-end;">'
                 f'<div style="{_BUSER}">{content}</div>'
                 f'<div style="{_AVUSR}">👤</div></div>')
    else:
        rows += (f'<div style="{_ROW}justify-content:flex-start;">'
                 f'<div style="{_AVBOT}">🤖</div>'
                 f'<div style="{_BBOT}">{content}</div></div>')

st.markdown(
    f'<div style="display:flex;flex-direction:column;padding:4px 0 12px;">{rows}</div>',
    unsafe_allow_html=True,
)

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
