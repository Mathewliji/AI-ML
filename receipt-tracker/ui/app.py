import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Receipt Tracker AI",
    page_icon="🧾",
    layout="centered",
)

# ── WhatsApp-inspired styling ─────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #ECE5DD; }

  /* Header bar */
  .wa-header {
    background: #075E54;
    color: white;
    padding: 12px 18px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }
  .wa-header h2 { margin: 0; font-size: 1.1rem; }
  .wa-header small { opacity: 0.75; font-size: 0.8rem; }

  /* User chat bubble */
  [data-testid="stChatMessage"]:has(img[alt="user"]) > div:last-child {
    background: #DCF8C6;
    border-radius: 12px 0 12px 12px;
    margin-left: 15%;
    padding: 10px 14px;
  }

  /* Assistant chat bubble */
  [data-testid="stChatMessage"]:has(img[alt="assistant"]) > div:last-child {
    background: #FFFFFF;
    border-radius: 0 12px 12px 12px;
    margin-right: 15%;
    padding: 10px 14px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  }

  /* Input bar */
  .stChatInputContainer { background: #F0F0F0; border-radius: 24px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wa-header">
  <span style="font-size:2rem">🧾</span>
  <div>
    <h2>Receipt Tracker AI</h2>
    <small>Claude Vision · LangGraph · Always on</small>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm your AI expense assistant.\n\n"
                "📸 **Upload a receipt** in the sidebar and I'll extract every detail.\n"
                "💬 Or just **ask me anything** — *'show me this week's food spending'*, "
                "*'what's my biggest expense category?'*, etc."
            ),
        }
    ]

# ── Sidebar — receipt upload ──────────────────────────────────────────────────
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
            with st.spinner("Claude is reading your receipt…"):
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
                lines = [f"**Grand total:** {summary['grand_total']:.2f}\n"]
                for cat, vals in summary["by_category"].items():
                    lines.append(f"• {cat}: {vals['total']:.2f} ({vals['count']} receipts)")
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
