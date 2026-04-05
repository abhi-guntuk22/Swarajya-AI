"""
app.py — Swarajya-AI Streamlit Frontend
Entry point: streamlit run app.py --server.address 0.0.0.0 --server.port 8501
"""

import time
import streamlit as st

from config import (
    APP_TITLE, APP_SUBTITLE, APP_TAGLINE, VERSION,
    DEFAULT_MODEL, SERVER_PORT, MODE_PROMPTS,
)
from security import (
    check_auth, login, logout,
    validate_prompt, check_rate_limit, record_request_time,
)
from brain import (
    query_model, check_ollama_health, format_error_for_ui,
    OllamaConnectionError, ModelNotFoundError, VRAMOverflowError,
)
from utils import (
    get_hardware_metrics, get_local_ip,
    percent_to_color, format_gb, get_system_info,
)


# ─────────────────────────────────────────────
# 🎨 Page Config & CSS
# ─────────────────────────────────────────────

st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg-primary:    #0a0e1a;
    --bg-secondary:  #111827;
    --bg-card:       #161d2e;
    --bg-input:      #1e2a3a;
    --accent-saffron:#ff9933;
    --accent-green:  #138808;
    --accent-blue:   #0066cc;
    --text-primary:  #e8ecf0;
    --text-muted:    #8892a4;
    --border:        #1e2d42;
    --success:       #00d68f;
    --warning:       #ffaa00;
    --danger:        #ff3d71;
    --radius:        8px;
}

html, body, .stApp { background-color: var(--bg-primary) !important; }
.stApp { font-family: 'Inter', sans-serif; color: var(--text-primary); }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }

[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown { color: var(--text-primary); }

.swarajya-header {
    background: linear-gradient(135deg, #0a1628 0%, #0d1f3c 50%, #0a1628 100%);
    border: 1px solid var(--border);
    border-bottom: 2px solid var(--accent-saffron);
    border-radius: var(--radius);
    padding: 20px 28px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.swarajya-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-saffron), white, var(--accent-green));
}
.swarajya-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-saffron);
    margin: 0;
    letter-spacing: 0.05em;
}
.swarajya-header p {
    color: var(--text-muted);
    margin: 4px 0 0;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.status-pill {
    display: inline-block;
    background: rgba(0, 214, 143, 0.15);
    border: 1px solid var(--success);
    color: var(--success);
    border-radius: 100px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.05em;
    margin-top: 8px;
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    margin: 8px 0;
}
.metric-label {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
    font-family: 'Space Mono', monospace;
}
.metric-value {
    font-size: 1.1rem;
    font-weight: 600;
    font-family: 'Space Mono', monospace;
}

.progress-container { margin: 6px 0; }
.progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-bottom: 3px;
    font-family: 'Space Mono', monospace;
}
.progress-bar {
    height: 6px;
    background: var(--bg-input);
    border-radius: 3px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}

.privacy-badge {
    background: rgba(19, 136, 8, 0.1);
    border: 1px solid var(--accent-green);
    border-radius: var(--radius);
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.8rem;
    color: #4ade80;
}

.network-badge {
    background: rgba(0, 102, 204, 0.1);
    border: 1px solid var(--accent-blue);
    border-radius: var(--radius);
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.8rem;
    color: #60a5fa;
    word-break: break-all;
}

.chat-message {
    padding: 14px 18px;
    border-radius: var(--radius);
    margin: 8px 0;
    line-height: 1.6;
    font-size: 0.92rem;
}
.chat-user {
    background: var(--bg-input);
    border-left: 3px solid var(--accent-saffron);
    color: var(--text-primary);
}
.chat-bot {
    background: var(--bg-card);
    border-left: 3px solid var(--accent-green);
    color: var(--text-primary);
}
.chat-error {
    background: rgba(255, 61, 113, 0.08);
    border-left: 3px solid var(--danger);
    color: #fca5a5;
}
.chat-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 6px;
}

.stTextArea textarea {
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus {
    border-color: var(--accent-saffron) !important;
    box-shadow: 0 0 0 2px rgba(255, 153, 51, 0.15) !important;
}

.stButton > button {
    background: var(--accent-saffron) !important;
    color: #000 !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    font-family: 'Space Mono', monospace !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #ffb347 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 153, 51, 0.3) !important;
}

.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    padding: 12px 0 6px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
}

.login-card {
    max-width: 420px;
    margin: 80px auto;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent-saffron);
    border-radius: 12px;
    padding: 40px;
}

.ollama-online  { color: var(--success); font-size: 0.8rem; font-family: 'Space Mono', monospace; }
.ollama-offline { color: var(--danger);  font-size: 0.8rem; font-family: 'Space Mono', monospace; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🔐 Login Page
# ─────────────────────────────────────────────

def render_login_page():
    st.markdown("""
    <div class='login-card'>
        <div style='text-align:center; margin-bottom:28px;'>
            <div style='font-size:2.5rem; margin-bottom:8px;'>🇮🇳</div>
            <div style='font-family: Space Mono, monospace; font-size:1.4rem;
                        color:#ff9933; font-weight:700;'>SWARAJYA-AI</div>
            <div style='color:#8892a4; font-size:0.8rem; margin-top:4px;
                        letter-spacing:0.1em; text-transform:uppercase;'>
                Sovereign Intelligence Hub
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 🔒 Gatekeeper Authentication")
        st.markdown(
            "<p style='color:#8892a4; font-size:0.83rem; margin-bottom:16px;'>"
            "Enter the access password to proceed.</p>",
            unsafe_allow_html=True
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter access password...",
            key="login_input",
        )
        if st.button("AUTHENTICATE →", use_container_width=True):
            success, message = login(password)
            if success:
                st.success(message)
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(message)

        st.markdown(
            f"<p style='color:#4b5563; font-size:0.72rem; text-align:center; margin-top:20px;'>"
            f"Swarajya-AI v{VERSION} · AMD Slingshot 2026</p>",
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# 📊 Sidebar
# ─────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 16px 0 12px;'>
            <div style='font-family: Space Mono, monospace; font-size:1.1rem;
                        color:#ff9933; font-weight:700;'>⚡ SWARAJYA-AI</div>
            <div style='color:#8892a4; font-size:0.68rem; letter-spacing:0.1em;
                        text-transform:uppercase; margin-top:2px;'>
                AMD Slingshot 2026
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>⚙️ Hardware Monitor</div>", unsafe_allow_html=True)

        hw = get_hardware_metrics()

        if hw.gpu_available:
            gpu_color = percent_to_color(hw.vram_percent)
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>🎮 GPU</div>
                <div class='metric-value' style='color:{gpu_color}; font-size:0.85rem;'>
                    {hw.gpu_name}
                </div>
                <div class='progress-container' style='margin-top:8px;'>
                    <div class='progress-label'>
                        <span>VRAM</span>
                        <span>{format_gb(hw.vram_used_gb)} / {format_gb(hw.vram_total_gb)}</span>
                    </div>
                    <div class='progress-bar'>
                        <div class='progress-fill'
                             style='width:{hw.vram_percent}%; background:{gpu_color};'></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-label'>🎮 GPU</div>
                <div style='color:#ffaa00; font-size:0.82rem;'>CPU Mode (No CUDA GPU detected)</div>
                <div style='color:#8892a4; font-size:0.72rem; margin-top:4px;'>
                    Install PyTorch with CUDA for GPU acceleration
                </div>
            </div>
            """, unsafe_allow_html=True)

        cpu_color = percent_to_color(hw.cpu_percent)
        st.markdown(f"""
        <div class='metric-card'>
            <div class='progress-container'>
                <div class='progress-label'>
                    <span>CPU ({hw.cpu_cores} cores)</span>
                    <span>{hw.cpu_percent:.1f}%</span>
                </div>
                <div class='progress-bar'>
                    <div class='progress-fill'
                         style='width:{hw.cpu_percent}%; background:{cpu_color};'></div>
                </div>
            </div>
            <div class='progress-container'>
                <div class='progress-label'>
                    <span>RAM</span>
                    <span>{format_gb(hw.ram_used_gb)} / {format_gb(hw.ram_total_gb)}</span>
                </div>
                <div class='progress-bar'>
                    <div class='progress-fill'
                         style='width:{hw.ram_percent}%; background:{percent_to_color(hw.ram_percent)};'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='color:#8892a4; font-size:0.72rem; padding:2px 4px;'>
            💾 Disk Free: {format_gb(hw.disk_free_gb)} / {format_gb(hw.disk_total_gb)}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🤖 AI Engine</div>", unsafe_allow_html=True)

        try:
            health = check_ollama_health()
            model_status = "✅ Ready" if health["model_available"] else "⚠️ Pull llama3"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='ollama-online'>● Ollama: ONLINE</div>
                <div style='color:#8892a4; font-size:0.72rem; margin-top:4px;'>
                    Model: {DEFAULT_MODEL} — {model_status}
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
            <div class='metric-card'>
                <div class='ollama-offline'>● Ollama: OFFLINE</div>
                <div style='color:#8892a4; font-size:0.72rem; margin-top:4px;'>
                    Run: <code>ollama serve</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🔒 Data Sovereignty</div>", unsafe_allow_html=True)

        for badge in [
            ("🔴", "100% Offline — No Internet Required"),
            ("🟢", "Zero Cloud API Calls"),
            ("🇮🇳", "Data Stays in India"),
            ("🔐", "No Telemetry · No Logging"),
        ]:
            st.markdown(f"""
            <div class='privacy-badge'>
                <span style='margin-right:6px;'>{badge[0]}</span>{badge[1]}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🌐 LAN Access</div>", unsafe_allow_html=True)

        local_ip = get_local_ip()
        lan_url = f"http://{local_ip}:{SERVER_PORT}"

        st.markdown(f"""
        <div class='network-badge'>
            <div style='font-size:0.68rem; color:#8892a4; margin-bottom:4px;'>
                Share this URL on your LAN:
            </div>
            <div style='font-family: Space Mono, monospace; font-weight:700;'>
                {lan_url}
            </div>
            <div style='font-size:0.68rem; color:#8892a4; margin-top:4px;'>
                Any device on this network can connect
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🔧 Session</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()

        st.markdown(f"""
        <div style='text-align:center; padding:16px 0 8px;
                    color:#4b5563; font-size:0.68rem;
                    font-family: Space Mono, monospace;'>
            Swarajya-AI v{VERSION} · AMD Slingshot 2026<br>
            Built for Bharat 🇮🇳
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 💬 Chat Interface
# ─────────────────────────────────────────────

def render_chat_interface():
    st.markdown(f"""
    <div class='swarajya-header'>
        <h1>⚡ {APP_TITLE}</h1>
        <p>{APP_SUBTITLE} — {APP_TAGLINE}</p>
        <span class='status-pill'>● SYSTEM ONLINE</span>
    </div>
    """, unsafe_allow_html=True)

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 2])

    with ctrl_col1:
        mode = st.selectbox(
            "🎯 Mode",
            options=list(MODE_PROMPTS.keys()),
            help="Select the AI's operational mode",
            key="selected_mode",
        )

    with ctrl_col2:
        hinglish = st.toggle(
            "🇮🇳 Hinglish Mode",
            value=False,
            help="Get responses in a natural Hindi-English mix",
            key="hinglish_toggle",
        )

    with ctrl_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        msg_count = len(st.session_state.get("messages", []))
        st.markdown(
            f"<div style='color:#8892a4; font-size:0.8rem; padding-top:8px;'>"
            f"💬 {msg_count // 2} exchange{'s' if msg_count != 2 else ''} this session</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    messages = st.session_state["messages"]

    if not messages:
        st.markdown("""
        <div style='text-align:center; padding:48px 20px; color:#4b5563;'>
            <div style='font-size:2.5rem; margin-bottom:12px;'>🎓</div>
            <div style='font-family: Space Mono, monospace; font-size:0.9rem; color:#8892a4;'>
                SwarajyaBot is ready. Ask your first question.
            </div>
            <div style='font-size:0.78rem; color:#4b5563; margin-top:8px;'>
                Try: "Explain Operating System deadlock using a Mumbai local train analogy"
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        chat_container = st.container()
        with chat_container:
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                is_error = msg.get("is_error", False)

                if role == "user":
                    st.markdown(f"""
                    <div class='chat-message chat-user'>
                        <div class='chat-label'>👤 You</div>
                        {content}
                    </div>
                    """, unsafe_allow_html=True)
                elif role == "assistant":
                    css_class = "chat-error" if is_error else "chat-bot"
                    label = "⚠️ System" if is_error else "🤖 SwarajyaBot"
                    st.markdown(f"""
                    <div class='chat-message {css_class}'>
                        <div class='chat-label'>{label}</div>
                    """, unsafe_allow_html=True)
                    st.markdown(content)
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    input_col, btn_col = st.columns([5, 1])

    with input_col:
        user_input = st.text_area(
            "Your question",
            placeholder=(
                "Ask anything IT Engineering related...\n"
                "e.g. 'Debug this Python code' / 'Explain TCP/IP' / 'SPPU CN syllabus'"
            ),
            height=100,
            label_visibility="collapsed",
            key="user_input",
        )

    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        send_pressed = st.button("SEND →", use_container_width=True, key="send_btn")

    if send_pressed and user_input and user_input.strip():
        _process_message(user_input.strip(), mode, hinglish)


def _process_message(user_input: str, mode: str, hinglish: bool):
    """Handle validation, rate limiting, inference, and state updates."""

    allowed, wait_secs = check_rate_limit()
    if not allowed:
        st.warning(f"⏱️ Please wait {wait_secs}s before sending another message.")
        return

    is_safe, firewall_msg = validate_prompt(user_input)
    if not is_safe:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["messages"].append({
            "role": "assistant",
            "content": firewall_msg,
            "is_error": True,
        })
        record_request_time()
        st.rerun()
        return

    st.session_state["messages"].append({"role": "user", "content": user_input})
    record_request_time()

    with st.spinner("🧠 SwarajyaBot is thinking..."):
        try:
            response = query_model(
                user_message=user_input,
                conversation_history=st.session_state["messages"][:-1],
                mode=mode,
                hinglish=hinglish,
            )
            st.session_state["messages"].append({
                "role": "assistant",
                "content": response,
                "is_error": False,
            })

        except Exception as e:
            error_md = format_error_for_ui(e)
            st.session_state["messages"].append({
                "role": "assistant",
                "content": error_md,
                "is_error": True,
            })

    st.rerun()


# ─────────────────────────────────────────────
# 🚀 Main Orchestrator
# ─────────────────────────────────────────────

def main():
    if not check_auth():
        render_login_page()
    else:
        render_sidebar()
        render_chat_interface()


if __name__ == "__main__":
    main()
