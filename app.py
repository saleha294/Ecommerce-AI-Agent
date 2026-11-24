import streamlit as st
from agent import agent
from errors import LLMBusyError, LLMConfigError, AgentError

# Must be the first Streamlit call. The built-in sidebar is unused (it can be collapsed),
# so we draw our own fixed sidebar in HTML instead.
st.set_page_config(
    page_title="E-Commerce AI Data Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ───────────────────────── STYLES (one block, edit here) ─────────────────────────
# Palette: white #FFFFFF | pastel red #F0767F | tint #FFF1F1 | navy #1D2B4F | near-black #0B1020
# Fixed pieces: sidebar (left), navbar (top), chat input (bottom). Only messages scroll.
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root { --navy:#1D2B4F; --red:#F0767F; --tint:#FFF1F1; --line:#F3D5D7; --ink:#0B1020; --side:280px; --col:860px; }

/* Font: applied to text areas only, never with a wildcard (that would break icon fonts) */
.stApp, .stApp [data-testid="stMarkdownContainer"] *, .stApp textarea, .stApp button p {
    font-family: 'Inter', sans-serif;
}
.stApp { background:#FFFFFF; }

/* Hide Streamlit's own chrome and its built-in sidebar */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], footer, #MainMenu { display:none !important; }

/* Main column: centred in the space to the right of the sidebar */
[data-testid="stMainBlockContainer"] {
    width: min(var(--col), calc(100% - var(--side))) !important;
    max-width: var(--col) !important;
    margin-left: max(var(--side), calc(var(--side) + (100% - var(--side) - var(--col)) / 2)) !important;
    margin-right: 0 !important;
    padding: 5rem 1rem 8.5rem 1rem !important;   /* top clears the navbar, bottom clears the input */
    align-self: flex-start !important;               /* the parent centres children, which shifted us right */
    box-sizing: border-box !important;
}

/* Message box: a form (text input + Send), fixed at the bottom and aligned with the main column.
   Built from a normal text input because st.chat_input cannot be pre-filled from code. */
[data-testid="stBottom"] { display:none !important; }
.st-key-composer {
    position:fixed; bottom:0; left:var(--side); right:0; width:calc(100% - var(--side)) !important; z-index:1000; background:#FFFFFF;
    box-sizing:border-box; padding:0.75rem max(1rem, calc((100% - var(--side) - var(--col)) / 2)) 1.25rem;
}
.st-key-composer [data-testid="stForm"] { border:none !important; padding:0 !important; background:transparent !important; }
/* The text input itself is the one visible box */
.st-key-composer [data-testid="stTextInputRootElement"] {
    border:1px solid var(--line) !important; border-radius:14px !important; background:#FFFFFF !important;
    padding:0.15rem 0.6rem !important; box-shadow:none !important;
}
.st-key-composer [data-testid="stTextInputRootElement"]:focus-within {
    border-color:var(--red) !important; box-shadow:0 0 0 3px rgba(240,118,127,0.18) !important;
}
.st-key-composer [data-baseweb="input"], .st-key-composer [data-baseweb="base-input"] {
    border:none !important; background:transparent !important; box-shadow:none !important;
}
.st-key-composer input {
    border:none !important; box-shadow:none !important; background:transparent !important;
    padding:0.6rem 0.25rem !important; font-size:0.97rem;
}
[data-testid="InputInstructions"] { display:none !important; }
/* Enter sends the question. A form must contain a submit button, so it is hidden, not removed. */
.st-key-composer [data-testid="stFormSubmitButton"] {
    position:absolute !important; width:1px; height:1px; overflow:hidden; opacity:0; pointer-events:none;
}

/* Sidebar (fixed HTML panel) */
.side {
    position:fixed; top:0; left:0; bottom:0; width:var(--side); z-index:1001;
    background:var(--navy); color:#C9D3F0; box-sizing:border-box;
    padding:1.7rem 1.5rem; display:flex; flex-direction:column; overflow-y:auto;
}
.side-brand { display:flex; align-items:center; gap:0.75rem; font-size:1.15rem; font-weight:700; color:#FFFFFF; }
.side-about { margin-top:1.2rem; font-size:0.93rem; line-height:1.7; color:#C9D3F0; }
.side-bottom { margin-top:auto; }
.side-label { font-size:0.68rem; letter-spacing:0.13em; font-weight:600; color:#8E9CC4; margin-bottom:0.65rem; }
.side-chip {
    display:inline-block; margin:0 0.35rem 0.4rem 0; padding:0.25rem 0.7rem; border-radius:999px;
    background:rgba(255,255,255,0.09); font-size:0.78rem; color:#E6ECFF;
}
.side-credit { margin-top:1.2rem; padding-top:1.1rem; border-top:1px solid rgba(255,255,255,0.14); line-height:1.5; }
.side-credit .small { font-size:0.74rem; color:#8E9CC4; }
.side-credit .name { font-size:1rem; font-weight:700; color:#FFFFFF; margin:0.15rem 0; }
.side-credit .role { font-size:0.78rem; color:#C9D3F0; }

/* Navbar (fixed, full width of the area right of the sidebar) */
.st-key-topbar {
    position:fixed; top:0; left:var(--side); right:0; width:calc(100% - var(--side)) !important; height:64px; z-index:1000;
    background:#FFFFFF; border-bottom:1px solid var(--line); box-sizing:border-box;
    padding:0 2rem; display:flex; flex-direction:row; align-items:center; justify-content:space-between; gap:1.25rem;
}
.st-key-topbar > * { flex:0 0 auto; width:auto !important; }
.st-key-topbar [data-testid="stMarkdown"], .st-key-topbar [data-testid="stMarkdownContainer"] { margin:0 !important; }
.st-key-topbar button {
    background:var(--navy) !important; border:none !important; border-radius:10px !important;
    padding:0.45rem 1.15rem !important; min-height:0 !important;
}
.st-key-topbar button p { color:#FFFFFF !important; font-weight:600; font-size:0.9rem; }
.st-key-topbar button:hover { background:#2d4072 !important; }
.nav-title { display:flex; align-items:center; gap:0.7rem; font-weight:600; font-size:1.05rem; color:var(--navy); }
.nav-dot {
    width:14px; height:14px; border-radius:50%;
    background:radial-gradient(circle at 30% 30%, #3d57a0, #1D2B4F 60%, #0B1020);
}

/* Welcome section */
.welcome { text-align:center; padding-top:0; }
.welcome-blob {
    width:64px; height:64px; border-radius:50%; margin:0 auto 0.9rem auto;
    background:radial-gradient(circle at 30% 28%, #3d57a0, #1D2B4F 55%, #0B1020);
    box-shadow:inset 0 2px 8px rgba(255,255,255,0.14), 0 10px 28px rgba(11,16,32,0.35);
}
.welcome-title { font-size:1.9rem; font-weight:700; color:var(--navy); line-height:1.2; }
.welcome-sub { margin-top:0.4rem; margin-bottom:1.3rem; color:#6B7A99; }

/* Cards: an HTML card with an invisible button laid over it */
[class*="st-key-card_"] {
    position:relative; background:#FFFFFF; border:1px solid var(--line); border-radius:16px;
    padding:1.35rem 1.5rem; min-height:146px; box-sizing:border-box;
    transition:border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}
[class*="st-key-card_"]:hover {
    border-color:var(--red); transform:translateY(-2px); box-shadow:0 8px 20px rgba(29,43,79,0.10);
}
.card-icon {
    width:38px; height:38px; border-radius:10px; background:var(--tint);
    display:flex; align-items:center; justify-content:center; margin-bottom:0.9rem;
}
.card-title { font-weight:600; color:var(--navy); font-size:0.95rem; }
.card-desc { color:#6B7A99; font-size:0.83rem; margin-top:0.3rem; line-height:1.45; }
[class*="st-key-btn_"] { position:absolute; inset:0; z-index:2; margin:0; }
[class*="st-key-btn_"], [class*="st-key-btn_"] * { width:100%; height:100%; min-height:100%; }
[class*="st-key-btn_"] button { opacity:0; cursor:pointer; }

/* Chat bubbles: keyed containers, so we do not depend on Streamlit's avatar internals */
[class*="st-key-msg_"] {
    position:relative; border-radius:18px; padding:16px 22px; margin-bottom:1.1rem;
    box-sizing:border-box; width:fit-content; line-height:1.6;
}
[class*="st-key-msg_"]::before {
    content:""; position:absolute; top:0; width:34px; height:34px; border-radius:50%;
    background-color:var(--navy); background-repeat:no-repeat; background-position:center; background-size:18px;
}
/* You: right side. Agent: left side. Both shrink to fit their text. */
[class*="st-key-msg_user_"] { background:var(--navy); margin-left:auto; margin-right:46px; max-width:75%; }
[class*="st-key-msg_user_"]::before { right:-46px; }
[class*="st-key-msg_assistant_"] { margin-left:46px; margin-right:auto; max-width:calc(100% - 46px); }
[class*="st-key-msg_assistant_"]::before { left:-46px; }
[class*="st-key-msg_user_"] * { color:#FFFFFF !important; }
[class*="st-key-msg_user_"]::before {
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E");
}
[class*="st-key-msg_assistant_"] { background:var(--red); }
[class*="st-key-msg_assistant_"] * { color:var(--navy) !important; }
[class*="st-key-msg_assistant_"]::before {
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z'/%3E%3C/svg%3E");
}
[class*="st-key-msg_assistant_"] table, [class*="st-key-msg_assistant_"] th, [class*="st-key-msg_assistant_"] td {
    border-color:rgba(29,43,79,0.3) !important;
}
[class*="st-key-msg_assistant_"] code { background:rgba(29,43,79,0.12) !important; }
[class*="st-key-msg_assistant_"] a { text-decoration:underline; }

/* Small screens: no sidebar, full-width layout */
@media (max-width: 768px) {
    .side { display:none; }
    .st-key-topbar { left:0; width:100% !important; padding:0 1rem; }
    .st-key-composer { left:0; width:100% !important; padding-left:1rem; padding-right:1rem; }
    [data-testid="stMainBlockContainer"], [data-testid="stBottomBlockContainer"] {
        width:100% !important; margin-left:0 !important;
    }
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ───────────────────────── SIDEBAR (static, fixed, cannot collapse) ─────────────────────────
# HTML is built from one-line pieces: no indentation and no blank lines, or Markdown
# would turn it into a code block.
SIDEBAR_HTML = (
    '<div class="side">'
    '<div><div class="side-brand">Store Assistant</div>'
    '<div class="side-about">An AI agent that answers questions about the store in plain English. '
    'Browse products by category, look up customers, see what is inside an order, '
    'check order totals, or find the best sellers.</div></div>'
    '<div class="side-bottom">'
    '<div class="side-label">BUILT WITH</div>'
    '<div><span class="side-chip">Python</span><span class="side-chip">Gemini</span>'
    '<span class="side-chip">PostgreSQL</span><span class="side-chip">Supabase</span></div>'
    '<div class="side-credit"><div class="small">Built by</div>'
    '<div class="name">Saleha Zeeshan</div>'
    '<div class="role">Aspirant Agentic AI &amp; Automation Engineer</div></div>'
    '</div></div>'
)
st.markdown(SIDEBAR_HTML, unsafe_allow_html=True)

# ───────────────────────── STATE ─────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ───────────────────────── NAVBAR ─────────────────────────
with st.container(key="topbar"):
    st.markdown(
        '<div class="nav-title"><span class="nav-dot"></span>Chat with AI Agent</div>',
        unsafe_allow_html=True,
    )
    if st.button("New chat", key="new_chat"):
        st.session_state.messages = []
        st.rerun()

# ───────────────────────── FLOW ─────────────────────────
# Card click: put the question in the message box. The user reads it, edits it if
# they like, and presses Enter (or Send). Nothing is sent by accident.
def fill_prompt(q):
    st.session_state.draft = q


# The message box is created first so we know whether a question was sent. It is fixed
# to the bottom with CSS, so its place in the script does not matter visually.
with st.container(key="composer"):
    with st.form("ask_form", clear_on_submit=True, border=False):
        typed = st.text_input(
            "Message",
            key="draft",
            placeholder="Ask about products, customers or orders",
            label_visibility="collapsed",
        )
        # A form must have a submit button. It is hidden with CSS; pressing Enter submits.
        submitted = st.form_submit_button("Send")

# Save the question BEFORE drawing the page so the welcome screen is gone on this run.
question = typed.strip() if submitted and typed.strip() else None
if question:
    st.session_state.messages.append({"role": "user", "content": question})


def svg(paths):
    return (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1D2B4F" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + paths + "</svg>"
    )


CARDS = [
    ("Browse products", "Browse the catalogue and prices", "Show me beauty products",
     '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>'),
    ("Find a customer", "Look up a customer by name", "Find customer Michael",
     '<circle cx="10" cy="7" r="4"/><path d="M10.3 15H7a4 4 0 0 0-4 4v2"/><circle cx="17" cy="17" r="3"/><path d="m21 21-1.9-1.9"/>'),
    ("Customer orders", "See all orders for a customer", "What orders did Emily place?",
     '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M8 8h8"/><path d="M8 12h8"/><path d="M8 16h5"/>'),
    ("Order details", "View what is inside an order", "What's in order 1?",
     '<path d="m7.5 4.3 9 5.2"/><path d="M21 8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>'),
    ("Order total", "Get the total cost of an order", "What's the total of order 104?",
     '<rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>'),
    ("Best sellers", "Find the top-selling products", "Top 3 best-selling products?",
     '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>'),
]

# d) welcome screen. It lives in its own slot: when a question is sent this slot is
#    emptied at once. Otherwise Streamlit keeps the old cards on screen, faded, until
#    the agent has finished answering.
welcome = st.empty()
if not st.session_state.messages:
    with welcome.container():
        st.markdown(
            '<div class="welcome"><div class="welcome-blob"></div>'
            '<div class="welcome-title">Welcome to your E-Commerce AI Agent</div>'
            '<div class="welcome-sub">Ask about products, customers or orders.</div></div>',
            unsafe_allow_html=True,
        )
        for row in (CARDS[:3], CARDS[3:]):
            columns = st.columns(3)
            for column, (title, desc, q, paths) in zip(columns, row):
                n = CARDS.index((title, desc, q, paths)) + 1
                with column:
                    with st.container(key=f"card_{n}"):
                        st.markdown(
                            f'<div class="card-icon">{svg(paths)}</div>'
                            f'<div class="card-title">{title}</div>'
                            f'<div class="card-desc">{desc}</div>',
                            unsafe_allow_html=True,
                        )
                        st.button("open", key=f"btn_{n}", on_click=fill_prompt, args=(q,))


# e) saved messages
def show_message(role, content, index, caption=None):
    with st.container(key=f"msg_{role}_{index}"):
        st.markdown(content)
        if caption:
            st.caption(caption)


for i, message in enumerate(st.session_state.messages):
    show_message(message["role"], message["content"], i)

# f) call the agent (same error handling as main.py, shown in the page)
if question:
    caption = None
    with st.spinner("Thinking..."):
        try:
            answer = agent(question)
        except LLMBusyError as e:
            answer = "The AI service is busy. Please try again in a moment."
            caption = str(e)  # technical detail for the developer
        except LLMConfigError as e:
            answer = f"There is a configuration problem with the AI service: {e}"
        except AgentError as e:
            answer = f"Something went wrong while processing your question: {e}"
    show_message("assistant", answer, len(st.session_state.messages), caption)
    st.session_state.messages.append({"role": "assistant", "content": answer})