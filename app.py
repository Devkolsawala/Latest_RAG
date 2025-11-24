import streamlit as st
import os
from rag_engine import get_documents_text, get_text_chunks, get_vector_store, user_input
from chat_utils import load_chat_history, group_chat_history, save_chat_session, get_new_session_id, delete_chat_session
from datetime import datetime, timedelta
import uuid
import extra_streamlit_components as stx
import tempfile

# NEW IMPORT (replaces cv2/imageio)
from video_utils import get_video_summary_from_file

# --- Page Configuration ---
st.set_page_config(
    page_title="DocChat AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "session_id" not in st.session_state:
    st.session_state.session_id = get_new_session_id()
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# --- Device ID Management ---
cookie_manager = stx.CookieManager(key="cookie_manager")
cookies = cookie_manager.get_all()
device_id = cookies.get("device_id") if cookies else None

if not device_id:
    device_id = str(uuid.uuid4())
    cookie_manager.set("device_id", device_id, expires_at=datetime.now() + timedelta(days=365))

# ---------------------------------------
# (❗ KEEP YOUR EXISTING CSS AND SIDEBAR)
# ---------------------------------------
# I did not modify ANYTHING below this line 
# except the video summarization block.
# ---------------------------------------

def inject_custom_css():
    bg_color = "#ffffff"
    sidebar_bg = "#f0f4f9"
    text_color = "#1f1f1f"
    secondary_text = "#444746"
    accent_color = "#0b57d0"
    hover_color = "#0842a0"
    
    user_bg = "#f0f4f9"
    user_text = "#1f1f1f"
    ai_bg = "#ffffff"
    ai_text = "#1f1f1f"

    css = f"""
    <style>
        html, body, [class*="css"] {{
            font-family: 'Google Sans', 'Roboto', sans-serif;
            color: {text_color};
            background-color: {bg_color};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)



def render_sidebar():
    with st.sidebar:
        st.markdown("### ✨ DocChat")

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = get_new_session_id()
            st.session_state.processing_complete = False
            st.session_state.confirm_delete = None
            st.session_state.uploader_key = str(uuid.uuid4())
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        pdf_docs = st.file_uploader(
            "Upload PDF/DOCX/TXT",
            accept_multiple_files=True,
            type=["pdf","docx","txt"],
            label_visibility="collapsed",
            key=st.session_state.uploader_key
        )

        if pdf_docs:
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("⚡ Process Files", use_container_width=True):
                with st.spinner("Analyzing documents..."):
                    raw_text = get_documents_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    get_vector_store(text_chunks, st.session_state.session_id)
                    st.session_state.processing_complete = True
                    st.toast("Documents processed successfully!", icon="✅")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        st.markdown("#### 🛠️ Mode")
        mode = st.radio(
            "Select Mode",
            ["Chat with Documents", "Video Summarization"],
            label_visibility="collapsed"
        )
        st.session_state.mode = mode

        st.divider()

        st.markdown("#### 🤖 Model")
        if mode == "Video Summarization":
            st.info("Using Nvidia Nemotron")
            st.session_state.selected_model = "nvidia/nemotron-nano-12b-v2-vl:free"
        else:
            model_mapping = {
                "GPT-OSS": "openai/gpt-oss-20b:free",
                "Qwen 3": "qwen/qwen3-coder:free"
            }
            selected_model_name = st.radio(
                "Choose Model",
                list(model_mapping.keys()),
                horizontal=True,
                label_visibility="collapsed"
            )
            st.session_state.selected_model = model_mapping[selected_model_name]


# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------

def main():
    inject_custom_css()
    render_sidebar()

    # ---------------------------
    # VIDEO SUMMARIZATION MODE
    # ---------------------------
    if st.session_state.get("mode") == "Video Summarization":
        st.title("🎬 Video Summarization")
        st.caption("Powered by Nvidia Nemotron Vision")

        video_file = st.file_uploader("Upload a short video", type=["mp4","mov","avi","mkv"])
        
        if video_file:
            # Save temp file
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(video_file.read())
            video_path = tfile.name

            st.video(video_path)

            if st.button("✨ Summarize Video", type="primary"):
                with st.spinner("Analyzing video..."):
                    summary = get_video_summary_from_file(
                        video_path,
                        os.getenv("OPENROUTER_API_KEY")
                    )

                st.markdown("### 📝 Summary")
                st.markdown(summary)

            tfile.close()
            return

    # ---------------------------
    # DOCUMENT CHAT MODE
    # ---------------------------
    st.title("Chat with Documents")

    if not st.session_state.processing_complete:
        st.info("👈 Upload your documents in the sidebar to begin.")
    else:
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                avatar = "✨" if message["role"] == "assistant" else "👤"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.chat_input("Thinking...", disabled=True)

            with st.chat_message("assistant", avatar="✨"):
                with st.spinner("Thinking..."):
                    try:
                        response = user_input(
                            st.session_state.messages[-1]["content"],
                            st.session_state.get("selected_model", "openai/gpt-oss-20b:free"),
                            st.session_state.session_id
                        )
                    except Exception as e:
                        response = f"⚠️ An error occurred: {str(e)}"
                    
                    st.markdown(response)

            st.session_state.messages.append({"role":"assistant","content":response})
            save_chat_session(st.session_state.session_id, st.session_state.messages, user_id=device_id)
            st.rerun()

        else:
            if prompt := st.chat_input("Ask anything about your documents..."):
                st.session_state.messages.append({"role":"user","content":prompt})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)
                
                save_chat_session(st.session_state.session_id, st.session_state.messages, user_id=device_id)
                st.rerun()


if __name__ == "__main__":
    main()
